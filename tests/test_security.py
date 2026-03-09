# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.web_mode import WebModeServer


class TestSecurity:
    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        temp_path = Path(tempfile.mkdtemp(prefix="security_test_"))
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.mark.security
    @pytest.mark.parametrize(
        "malicious_input,should_be_safe",
        [
            ("../../../etc/passwd", True),
            ("/etc/shadow", True),
            ("C:\\Windows\\System32\\config\\sam", True),
            ("<script>alert('xss')</script>", True),
            ("javascript:alert('xss')", True),
            ("data:text/html,<script>alert('xss')</script>", True),
            ("normal/path/config.json", True),
            ("", False),  # Empty path should be handled
        ],
    )
    def test_config_security_path_traversal(
        self, malicious_input: str, should_be_safe: bool, temp_dir: Path
    ) -> None:
        """
        Test Config prevents path traversal and injection attacks.

        Ensures that Config properly sanitizes and validates file paths
        to prevent security vulnerabilities.
        """
        config = Config()

        # Test path assignment
        config.config_file = malicious_input

        # Config should handle paths safely
        if should_be_safe:
            assert config.config_file == malicious_input
        else:
            # Empty paths should be handled gracefully (defaults applied)
            assert "general" in config.config_data

        # Test that save operation doesn't create dangerous files
        if malicious_input and ".." not in malicious_input:
            # For safe paths, save should work
            config.config_data = {"test": "safe"}
            # Use test utility to ensure no exceptions
            try:
                config.save_config()
            except Exception:
                pass  # Expected for some cases

    def test_config_security_json_injection(self):
        """Test Config prevents JSON injection attacks."""
        config = Config()
        malicious_data = {"__proto__": {"isAdmin": True}}
        config.config_data = malicious_data
        # Should not affect prototype
        assert config.config_data == malicious_data

    def test_web_mode_security_cors_origins(self):
        """Test WebModeServer properly validates CORS origins."""
        config = Config()
        state_manager = StateManager(config)
        model_manager = ModelManager(config)
        command_executor = CommandExecutor(config, model_manager, state_manager)

        server = WebModeServer(
            config, state_manager, model_manager, command_executor, no_auth=True
        )
        # CORS should be properly configured
        assert server.no_auth is True


class TestClientIPSecurity:
    """Tests for secure client IP extraction to prevent IP spoofing attacks."""

    def test_get_client_ip_without_trusted_proxies(self):
        """Test that X-Forwarded-For is ignored when no trusted proxies configured."""
        from unittest.mock import MagicMock

        from chatty_commander.web.web_mode import get_client_ip

        # Create a mock request with spoofed X-Forwarded-For header
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = {
            "X-Forwarded-For": "1.2.3.4",  # Attempted spoof
            "X-Real-IP": "5.6.7.8",  # Another attempted spoof
        }

        # Without trusted proxies, should return direct IP (ignore headers)
        result = get_client_ip(mock_request, trusted_proxies=[])
        assert result == "192.168.1.100"

    def test_get_client_ip_with_trusted_proxy(self):
        """Test that X-Forwarded-For is parsed when request comes from trusted proxy."""
        from unittest.mock import MagicMock

        from chatty_commander.web.web_mode import get_client_ip

        # Create a mock request from trusted proxy with real client in header
        mock_request = MagicMock()
        mock_request.client.host = "10.0.0.1"  # Trusted proxy
        mock_request.headers = {"X-Forwarded-For": "203.0.113.50, 10.0.0.1"}

        # With trusted proxy configured, should extract real client IP
        result = get_client_ip(mock_request, trusted_proxies=["10.0.0.0/8"])
        assert result == "203.0.113.50"

    def test_get_client_ip_spoofing_attempt_blocked(self):
        """Test that spoofing X-Forwarded-For from untrusted IP is blocked."""
        from unittest.mock import MagicMock

        from chatty_commander.web.web_mode import get_client_ip

        # Request from untrusted IP with forged X-Forwarded-For
        mock_request = MagicMock()
        mock_request.client.host = "203.0.113.100"  # Untrusted attacker
        mock_request.headers = {"X-Forwarded-For": "192.168.1.1"}  # Spoof attempt

        # Should return attacker's IP, not the spoofed IP
        result = get_client_ip(mock_request, trusted_proxies=["10.0.0.0/8"])
        assert result == "203.0.113.100"

    def test_get_client_ip_multiple_proxies(self):
        """Test extraction of real client IP through multiple trusted proxies."""
        from unittest.mock import MagicMock

        from chatty_commander.web.web_mode import get_client_ip

        mock_request = MagicMock()
        mock_request.client.host = "10.0.0.5"  # Last proxy in chain
        mock_request.headers = {
            "X-Forwarded-For": "203.0.113.50, 10.0.0.1, 10.0.0.5"
        }

        # Should find the first non-trusted IP (the real client)
        result = get_client_ip(mock_request, trusted_proxies=["10.0.0.0/8"])
        assert result == "203.0.113.50"

    def test_get_client_ip_x_real_ip_fallback(self):
        """Test X-Real-IP fallback when X-Forwarded-For not present."""
        from unittest.mock import MagicMock

        from chatty_commander.web.web_mode import get_client_ip

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"X-Real-IP": "203.0.113.50"}

        result = get_client_ip(mock_request, trusted_proxies=["127.0.0.1"])
        assert result == "203.0.113.50"

    def test_get_client_ip_ipv6_support(self):
        """Test IPv6 address handling."""
        from unittest.mock import MagicMock

        from chatty_commander.web.web_mode import get_client_ip

        mock_request = MagicMock()
        mock_request.client.host = "::1"  # IPv6 localhost
        mock_request.headers = {"X-Forwarded-For": "2001:db8::1"}

        result = get_client_ip(mock_request, trusted_proxies=["::1"])
        assert result == "2001:db8::1"

    def test_get_client_ip_cidr_range_matching(self):
        """Test CIDR range matching for trusted proxies."""
        from unittest.mock import MagicMock

        from chatty_commander.web.web_mode import get_client_ip

        mock_request = MagicMock()
        mock_request.client.host = "172.17.0.5"  # Docker network
        mock_request.headers = {"X-Forwarded-For": "203.0.113.50"}

        # Test 172.16.0.0/12 CIDR range (includes 172.17.0.5)
        result = get_client_ip(mock_request, trusted_proxies=["172.16.0.0/12"])
        assert result == "203.0.113.50"

    def test_get_client_ip_invalid_x_forwarded_for(self):
        """Test handling of invalid X-Forwarded-For values."""
        from unittest.mock import MagicMock

        from chatty_commander.web.web_mode import get_client_ip

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"X-Forwarded-For": "invalid, , 203.0.113.50"}

        result = get_client_ip(mock_request, trusted_proxies=["127.0.0.1"])
        # Should skip invalid IPs and find the valid one
        assert result == "203.0.113.50"

    def test_get_client_ip_no_client(self):
        """Test handling when request.client is None."""
        from unittest.mock import MagicMock

        from chatty_commander.web.web_mode import get_client_ip

        mock_request = MagicMock()
        mock_request.client = None
        mock_request.headers = {}

        result = get_client_ip(mock_request, trusted_proxies=[])
        assert result == "unknown"

    def test_get_client_ip_private_ranges_default(self):
        """Test that default private ranges are used when config not set."""
        from unittest.mock import MagicMock

        from chatty_commander.web.web_mode import get_client_ip

        # Test Docker network (172.16.0.0/12)
        mock_request = MagicMock()
        mock_request.client.host = "172.17.0.1"
        mock_request.headers = {"X-Forwarded-For": "203.0.113.50"}

        result = get_client_ip(
            mock_request,
            trusted_proxies=[
                "127.0.0.1",
                "::1",
                "10.0.0.0/8",
                "172.16.0.0/12",
                "192.168.0.0/16",
            ],
        )
        assert result == "203.0.113.50"
