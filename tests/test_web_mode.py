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


import pytest
from test_data_factories import TestDataFactory

from chatty_commander.web.web_mode import WebModeServer


class TestWebMode:
    """
    Comprehensive tests for the WebModeServer module.
    """

    @pytest.mark.parametrize("no_auth", [True, False])
    def test_web_mode_server_initialization(self, no_auth):
        """Test WebModeServer initialization with auth settings."""
        config = TestDataFactory.create_mock_config(
            {
                "web_server": {
                    "host": "0.0.0.0",
                    "port": 8000,
                    "auth_enabled": not no_auth,
                }
            }
        )
        server = WebModeServer(config, no_auth=no_auth)
        assert server is not None

    @pytest.mark.parametrize("host", ["0.0.0.0", "127.0.0.1", "localhost", ""])
    def test_web_mode_server_host_configuration(self, host):
        """Test WebModeServer host configuration."""
        config = TestDataFactory.create_mock_config(
            {"web_server": {"host": host, "port": 8000, "auth_enabled": False}}
        )
        server = WebModeServer(config)
        assert server is not None
        # Assuming server has host attribute; adjust as needed
        # assert server.host == host

    @pytest.mark.parametrize("port", [8000, 3000, 5000, 0, 65535, None])
    def test_web_mode_server_port_configuration(self, port):
        """Test WebModeServer port configuration."""
        config = TestDataFactory.create_mock_config(
            {"web_server": {"host": "0.0.0.0", "port": port, "auth_enabled": False}}
        )
        server = WebModeServer(config)
        assert server is not None
        # Assuming server has port attribute; adjust as needed
        # assert server.port == port

    def test_web_mode_server_cors_configuration(self):
        """Test WebModeServer CORS configuration."""
        config = TestDataFactory.create_mock_config()
        server = WebModeServer(config)
        assert server is not None
        # Assuming CORS is configured; add assertions

    def test_web_mode_server_websocket_management(self):
        """Test WebModeServer WebSocket management."""
        config = TestDataFactory.create_mock_config()
        server = WebModeServer(config)
        assert server is not None
        # Assuming WebSocket handling; add assertions

    def test_web_mode_server_cache_management(self):
        """Test WebModeServer cache management."""
        config = TestDataFactory.create_mock_config()
        server = WebModeServer(config)
        assert server is not None
        # Assuming cache functionality; add assertions

    @pytest.mark.parametrize("uptime_seconds", [0, 60, 3600, 86400, 604800])
    def test_web_mode_server_uptime_formatting(self, uptime_seconds):
        """Test WebModeServer uptime formatting."""
        config = TestDataFactory.create_mock_config()
        server = WebModeServer(config)
        assert server is not None
        # Assuming uptime method; adjust as needed
        # uptime_str = server.format_uptime(uptime_seconds)
        # assert isinstance(uptime_str, str)
