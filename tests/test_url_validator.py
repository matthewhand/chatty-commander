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

"""
Comprehensive tests for URL validator module.

Tests SSRF prevention and URL safety validation.
"""

from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.utils.url_validator import is_safe_url, _is_restricted


class TestIsRestricted:
    """Tests for _is_restricted helper function."""

    def test_loopback_ipv4_is_restricted(self):
        """Test that loopback IPv4 is restricted."""
        assert _is_restricted("127.0.0.1") is True

    def test_loopback_ipv6_is_restricted(self):
        """Test that loopback IPv6 is restricted."""
        assert _is_restricted("::1") is True

    def test_private_ipv4_is_restricted(self):
        """Test that private IPv4 is restricted."""
        assert _is_restricted("192.168.1.1") is True
        assert _is_restricted("10.0.0.1") is True
        assert _is_restricted("172.16.0.1") is True

    def test_public_ip_is_not_restricted(self):
        """Test that public IP is not restricted."""
        assert _is_restricted("8.8.8.8") is False
        assert _is_restricted("1.1.1.1") is False

    def test_link_local_is_restricted(self):
        """Test that link-local is restricted."""
        assert _is_restricted("169.254.1.1") is True


class TestIsSafeUrl:
    """Tests for is_safe_url function."""

    def test_valid_http_url(self):
        """Test valid HTTP URL."""
        # Public URLs should be safe
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (2, 1, 6, "", ("93.184.216.34", 0))  # example.com IP
            ]
            assert is_safe_url("http://example.com") is True

    def test_valid_https_url(self):
        """Test valid HTTPS URL."""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (2, 1, 6, "", ("93.184.216.34", 0))
            ]
            assert is_safe_url("https://example.com") is True

    def test_loopback_url_is_blocked(self):
        """Test that loopback URL is blocked."""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (2, 1, 6, "", ("127.0.0.1", 0))
            ]
            assert is_safe_url("http://127.0.0.1") is False

    def test_private_url_is_blocked(self):
        """Test that private IP URL is blocked."""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (2, 1, 6, "", ("192.168.1.1", 0))
            ]
            assert is_safe_url("http://192.168.1.1") is False

    def test_ftp_scheme_is_blocked(self):
        """Test that FTP scheme is blocked."""
        assert is_safe_url("ftp://example.com") is False

    def test_file_scheme_is_blocked(self):
        """Test that file scheme is blocked."""
        assert is_safe_url("file:///etc/passwd") is False

    def test_javascript_scheme_is_blocked(self):
        """Test that javascript scheme is blocked."""
        assert is_safe_url("javascript:alert(1)") is False

    def test_url_without_scheme_is_blocked(self):
        """Test that URL without scheme is blocked."""
        assert is_safe_url("example.com") is False

    def test_empty_url_is_blocked(self):
        """Test that empty URL is blocked."""
        assert is_safe_url("") is False

    def test_url_without_hostname_is_blocked(self):
        """Test that URL without hostname is blocked."""
        assert is_safe_url("http://") is False

    def test_unresolvable_hostname_is_blocked(self):
        """Test that unresolvable hostname is blocked."""
        import socket
        with patch("socket.getaddrinfo", side_effect=socket.gaierror):
            assert is_safe_url("http://nonexistent-domain-12345.com") is False

    def test_mixed_addresses_all_must_be_safe(self):
        """Test that all resolved addresses must be safe."""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            # Mix of safe and unsafe - should be blocked
            mock_getaddrinfo.return_value = [
                (2, 1, 6, "", ("8.8.8.8", 0)),      # Public - safe
                (2, 1, 6, "", ("127.0.0.1", 0)),    # Loopback - unsafe
            ]
            assert is_safe_url("http://example.com") is False

    def test_all_safe_addresses_allowed(self):
        """Test that all safe addresses are allowed."""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (2, 1, 6, "", ("8.8.8.8", 0)),
                (2, 1, 6, "", ("1.1.1.1", 0)),
            ]
            assert is_safe_url("http://example.com") is True

    def test_ipv6_public_is_safe(self):
        """Test that public IPv6 is safe."""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (10, 1, 6, "", ("2001:4860:4860::8888", 0, 0, 0))
            ]
            assert is_safe_url("http://example.com") is True

    def test_ipv6_loopback_is_blocked(self):
        """Test that IPv6 loopback is blocked."""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (10, 1, 6, "", ("::1", 0, 0, 0))
            ]
            assert is_safe_url("http://example.com") is False


class TestUrlValidatorEdgeCases:
    """Edge case tests for URL validator."""

    def test_url_with_port(self):
        """Test URL with explicit port."""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (2, 1, 6, "", ("93.184.216.34", 0))
            ]
            assert is_safe_url("http://example.com:8080") is True

    def test_url_with_path(self):
        """Test URL with path."""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (2, 1, 6, "", ("93.184.216.34", 0))
            ]
            assert is_safe_url("http://example.com/path/to/resource") is True

    def test_url_with_query(self):
        """Test URL with query string."""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (2, 1, 6, "", ("93.184.216.34", 0))
            ]
            assert is_safe_url("http://example.com?key=value") is True

    def test_url_with_fragment(self):
        """Test URL with fragment."""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (2, 1, 6, "", ("93.184.216.34", 0))
            ]
            assert is_safe_url("http://example.com#section") is True

    def test_malformed_url_is_blocked(self):
        """Test that malformed URL is blocked."""
        assert is_safe_url("http://[invalid") is False

    def test_none_url_is_blocked(self):
        """Test that None URL is blocked."""
        assert is_safe_url(None) is False

    def test_exception_during_validation_is_blocked(self):
        """Test that exceptions result in blocking."""
        with patch("socket.getaddrinfo", side_effect=Exception("Unexpected error")):
            assert is_safe_url("http://example.com") is False


class TestUrlValidatorIntegration:
    """Integration tests for URL validator."""

    def test_real_public_url(self):
        """Test with real public URL resolution."""
        # This test uses real DNS resolution
        result = is_safe_url("http://example.com")
        # example.com should resolve to a public IP
        assert result is True

    def test_real_loopback_blocked(self):
        """Test that localhost is blocked."""
        result = is_safe_url("http://localhost")
        assert result is False
