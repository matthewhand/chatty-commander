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


from unittest.mock import MagicMock

import pytest
from test_data_factories import TestDataFactory

from chatty_commander.web.web_mode import WebModeServer


class TestWebMode:
    """
    Comprehensive tests for the WebModeServer module.
    """

    @pytest.fixture
    def mock_state_manager(self):
        """Create a mock StateManager."""
        mock = MagicMock()
        mock.current_state = "idle"
        mock.add_state_change_callback = MagicMock()
        return mock

    @pytest.fixture
    def mock_model_manager(self):
        """Create a mock ModelManager."""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def mock_command_executor(self):
        """Create a mock CommandExecutor."""
        mock = MagicMock()
        return mock

    @pytest.mark.parametrize("no_auth", [True, False])
    def test_web_mode_server_initialization(
        self, no_auth, mock_state_manager, mock_model_manager, mock_command_executor
    ):
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
        server = WebModeServer(
            config, mock_state_manager, mock_model_manager, mock_command_executor, no_auth=no_auth
        )
        assert server is not None

    @pytest.mark.parametrize("host", ["0.0.0.0", "127.0.0.1", "localhost", ""])
    def test_web_mode_server_host_configuration(
        self, host, mock_state_manager, mock_model_manager, mock_command_executor
    ):
        """Test WebModeServer host configuration."""
        config = TestDataFactory.create_mock_config(
            {"web_server": {"host": host, "port": 8000, "auth_enabled": False}}
        )
        server = WebModeServer(
            config, mock_state_manager, mock_model_manager, mock_command_executor
        )
        assert server is not None

    @pytest.mark.parametrize("port", [8000, 3000, 5000, 0, 65535, None])
    def test_web_mode_server_port_configuration(
        self, port, mock_state_manager, mock_model_manager, mock_command_executor
    ):
        """Test WebModeServer port configuration."""
        config = TestDataFactory.create_mock_config(
            {"web_server": {"host": "0.0.0.0", "port": port, "auth_enabled": False}}
        )
        server = WebModeServer(
            config, mock_state_manager, mock_model_manager, mock_command_executor
        )
        assert server is not None

    def test_web_mode_server_cors_configuration(
        self, mock_state_manager, mock_model_manager, mock_command_executor
    ):
        """Test WebModeServer CORS configuration."""
        config = TestDataFactory.create_mock_config()
        server = WebModeServer(
            config, mock_state_manager, mock_model_manager, mock_command_executor
        )
        assert server is not None

    def test_web_mode_server_websocket_management(
        self, mock_state_manager, mock_model_manager, mock_command_executor
    ):
        """Test WebModeServer WebSocket management."""
        config = TestDataFactory.create_mock_config()
        server = WebModeServer(
            config, mock_state_manager, mock_model_manager, mock_command_executor
        )
        assert server is not None

    def test_web_mode_server_cache_management(
        self, mock_state_manager, mock_model_manager, mock_command_executor
    ):
        """Test WebModeServer cache management."""
        config = TestDataFactory.create_mock_config()
        server = WebModeServer(
            config, mock_state_manager, mock_model_manager, mock_command_executor
        )
        assert server is not None

    @pytest.mark.parametrize("uptime_seconds", [0, 60, 3600, 86400, 604800])
    def test_web_mode_server_uptime_formatting(
        self, uptime_seconds, mock_state_manager, mock_model_manager, mock_command_executor
    ):
        """Test WebModeServer uptime formatting."""
        config = TestDataFactory.create_mock_config()
        server = WebModeServer(
            config, mock_state_manager, mock_model_manager, mock_command_executor
        )
        assert server is not None
