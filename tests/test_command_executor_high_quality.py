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

"""High-quality tests for CommandExecutor focusing on realistic scenarios and edge cases."""

import os
import subprocess
from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.app.command_executor import CommandExecutor


class TestCommandExecutorKeyPress:
    """Test keypress command execution with realistic scenarios."""

    @pytest.fixture
    def mock_executor(self):
        """Create a CommandExecutor with mocked dependencies."""
        mock_config = Mock()
        mock_config.model_actions = {}
        mock_model_manager = Mock()
        mock_state_manager = Mock()
        return CommandExecutor(mock_config, mock_model_manager, mock_state_manager)

    def test_execute_keypress_space_key_success(self, mock_executor):
        """Test successful execution of space keypress command."""
        with patch(
            "src.chatty_commander.app.command_executor.pyautogui"
        ) as mock_pyautogui:
            mock_executor.config.model_actions = {
                "play_pause": {"action": "keypress", "keys": "space"}
            }

            result = mock_executor.execute_command("play_pause")

            assert result is True
            mock_pyautogui.press.assert_called_once_with("space")

    def test_execute_keypress_combination_keys_success(self, mock_executor):
        """Test successful execution of combination keypress like ctrl+c."""
        with patch(
            "src.chatty_commander.app.command_executor.pyautogui"
        ) as mock_pyautogui:
            mock_executor.config.model_actions = {
                "copy": {"action": "keypress", "keys": "ctrl+c"}
            }

            result = mock_executor.execute_command("copy")

            assert result is True
            mock_pyautogui.hotkey.assert_called_once_with("ctrl", "c")

    def test_execute_keypress_pyautogui_missing_logs_warning(self, mock_executor):
        """Test keypress command when pyautogui is not available."""
        with patch("src.chatty_commander.app.command_executor.pyautogui", None):
            with patch(
                "src.chatty_commander.app.command_executor.logging.getLogger"
            ) as mock_logger:
                mock_executor.config.model_actions = {
                    "play_pause": {"action": "keypress", "keys": "space"}
                }

                result = mock_executor.execute_command("play_pause")

                assert result is False
                mock_logger.return_value.warning.assert_called()

    def test_execute_keypress_empty_keys_returns_false(self, mock_executor):
        """Test keypress command with empty keys string."""
        mock_executor.config.model_actions = {
            "empty_command": {"action": "keypress", "keys": ""}
        }

        result = mock_executor.execute_command("empty_command")

        assert result is False

    def test_execute_keypress_pyautogui_exception_handles_gracefully(
        self, mock_executor
    ):
        """Test keypress command when pyautogui raises an exception."""
        with patch(
            "src.chatty_commander.app.command_executor.pyautogui"
        ) as mock_pyautogui:
            mock_pyautogui.press.side_effect = Exception("Display error")
            with patch(
                "src.chatty_commander.app.command_executor.logging.getLogger"
            ) as mock_logger:
                mock_executor.config.model_actions = {
                    "play_pause": {"action": "keypress", "keys": "space"}
                }

                result = mock_executor.execute_command("play_pause")

                assert result is False
                mock_logger.return_value.error.assert_called()


class TestCommandExecutorShell:
    """Test shell command execution with realistic scenarios."""

    @pytest.fixture
    def mock_executor(self):
        """Create a CommandExecutor with mocked dependencies."""
        mock_config = Mock()
        mock_config.model_actions = {}
        mock_model_manager = Mock()
        mock_state_manager = Mock()
        return CommandExecutor(mock_config, mock_model_manager, mock_state_manager)

    def test_execute_shell_simple_command_success(self, mock_executor):
        """Test successful execution of simple shell command."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["echo", "hello"], returncode=0, stdout="hello\n", stderr=""
            )

            mock_executor.config.model_actions = {
                "test_echo": {"action": "shell", "cmd": "echo hello"}
            }

            result = mock_executor.execute_command("test_echo")

            assert result is True
            mock_run.assert_called_once_with(
                "echo hello", shell=True, capture_output=True, text=True, timeout=30
            )

    def test_execute_shell_command_with_timeout(self, mock_executor):
        """Test shell command that times out."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("sleep 5", 30)
            with patch(
                "src.chatty_commander.app.command_executor.logging.getLogger"
            ) as mock_logger:
                mock_executor.config.model_actions = {
                    "long_command": {"action": "shell", "cmd": "sleep 5"}
                }

                result = mock_executor.execute_command("long_command")

                assert result is False
                mock_logger.return_value.error.assert_called()

    def test_execute_shell_command_non_zero_exit_code(self, mock_executor):
        """Test shell command that returns non-zero exit code."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["false"], returncode=1, stdout="", stderr=""
            )
            with patch(
                "src.chatty_commander.app.command_executor.logging.getLogger"
            ) as mock_logger:
                mock_executor.config.model_actions = {
                    "failing_command": {"action": "shell", "cmd": "false"}
                }

                result = mock_executor.execute_command("failing_command")

                assert result is False
                mock_logger.return_value.error.assert_called()

    def test_execute_shell_empty_command_returns_false(self, mock_executor):
        """Test shell command with empty command string."""
        mock_executor.config.model_actions = {
            "empty_shell": {"action": "shell", "cmd": ""}
        }

        result = mock_executor.execute_command("empty_shell")

        assert result is False


class TestCommandExecutorURL:
    """Test URL command execution with realistic scenarios."""

    @pytest.fixture
    def mock_executor(self):
        """Create a CommandExecutor with mocked dependencies."""
        mock_config = Mock()
        mock_config.model_actions = {}
        mock_model_manager = Mock()
        mock_state_manager = Mock()
        return CommandExecutor(mock_config, mock_model_manager, mock_state_manager)

    def test_execute_url_https_request_success(self, mock_executor):
        """Test successful HTTPS URL request."""
        with patch(
            "src.chatty_commander.app.command_executor.requests"
        ) as mock_requests:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_requests.get.return_value = mock_response

            mock_executor.config.model_actions = {
                "open_site": {"action": "url", "url": "https://example.com"}
            }

            result = mock_executor.execute_command("open_site")

            assert result is True
            mock_requests.get.assert_called_once_with("https://example.com", timeout=10)

    def test_execute_url_http_request_success(self, mock_executor):
        """Test successful HTTP URL request."""
        with patch(
            "src.chatty_commander.app.command_executor.requests"
        ) as mock_requests:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_requests.get.return_value = mock_response

            mock_executor.config.model_actions = {
                "open_site": {"action": "url", "url": "http://example.com"}
            }

            result = mock_executor.execute_command("open_site")

            assert result is True
            mock_requests.get.assert_called_once_with("http://example.com", timeout=10)

    def test_execute_url_requests_missing_logs_warning(self, mock_executor):
        """Test URL command when requests library is not available."""
        with patch("src.chatty_commander.app.command_executor.requests", None):
            with patch(
                "src.chatty_commander.app.command_executor.logging.getLogger"
            ) as mock_logger:
                mock_executor.config.model_actions = {
                    "open_site": {"action": "url", "url": "https://example.com"}
                }

                result = mock_executor.execute_command("open_site")

                assert result is False
                mock_logger.return_value.warning.assert_called()

    def test_execute_url_request_timeout(self, mock_executor):
        """Test URL request that times out."""
        with patch(
            "src.chatty_commander.app.command_executor.requests"
        ) as mock_requests:
            mock_requests.get.side_effect = Exception("Timeout")
            with patch(
                "src.chatty_commander.app.command_executor.logging.getLogger"
            ) as mock_logger:
                mock_executor.config.model_actions = {
                    "slow_site": {"action": "url", "url": "https://slow-site.com"}
                }

                result = mock_executor.execute_command("slow_site")

                assert result is False
                mock_logger.return_value.error.assert_called()

    def test_execute_url_invalid_url_scheme(self, mock_executor):
        """Test URL command with invalid URL scheme."""
        mock_executor.config.model_actions = {
            "invalid_scheme": {"action": "url", "url": "ftp://example.com"}
        }

        result = mock_executor.execute_command("invalid_scheme")

        assert result is False


class TestCommandExecutorCustomMessage:
    """Test custom message command execution."""

    @pytest.fixture
    def mock_executor(self):
        """Create a CommandExecutor with mocked dependencies."""
        mock_config = Mock()
        mock_config.model_actions = {}
        mock_model_manager = Mock()
        mock_state_manager = Mock()
        return CommandExecutor(mock_config, mock_model_manager, mock_state_manager)

    def test_execute_custom_message_success(self, mock_executor):
        """Test successful custom message execution."""
        with patch(
            "src.chatty_commander.app.command_executor.logging.getLogger"
        ) as mock_logger:
            mock_executor.config.model_actions = {
                "notify": {"action": "custom_message", "message": "Custom notification"}
            }

            result = mock_executor.execute_command("notify")

            assert result is True
            mock_logger.return_value.info.assert_called_with("Custom notification")

    def test_execute_custom_message_empty_message(self, mock_executor):
        """Test custom message with empty message."""
        with patch(
            "src.chatty_commander.app.command_executor.logging.getLogger"
        ) as mock_logger:
            mock_executor.config.model_actions = {
                "empty_notify": {"action": "custom_message", "message": ""}
            }

            result = mock_executor.execute_command("empty_notify")

            assert result is True
            mock_logger.return_value.info.assert_called_with("")


class TestCommandExecutorErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def mock_executor(self):
        """Create a CommandExecutor with mocked dependencies."""
        mock_config = Mock()
        mock_config.model_actions = {}
        mock_model_manager = Mock()
        mock_state_manager = Mock()
        return CommandExecutor(mock_config, mock_model_manager, mock_state_manager)

    def test_execute_command_invalid_action_type(self, mock_executor):
        """Test command with invalid action type."""
        mock_executor.config.model_actions = {
            "invalid": {"action": "invalid_action", "keys": "space"}
        }

        with pytest.raises(ValueError, match="invalid action type 'invalid_action'"):
            mock_executor.execute_command("invalid")

    def test_execute_command_non_string_action_type(self, mock_executor):
        """Test command with non-string action type."""
        mock_executor.config.model_actions = {
            "invalid_type": {"action": 123, "keys": "space"}
        }

        with pytest.raises(TypeError, match="Action type must be string"):
            mock_executor.execute_command("invalid_type")

    def test_execute_command_missing_action_key_legacy_keypress(self, mock_executor):
        """Test legacy format command with keypress."""
        with patch(
            "src.chatty_commander.app.command_executor.pyautogui"
        ) as mock_pyautogui:
            mock_executor.config.model_actions = {"legacy_space": {"keypress": "space"}}

            result = mock_executor.execute_command("legacy_space")

            assert result is True
            mock_pyautogui.press.assert_called_once_with("space")

    def test_execute_command_missing_action_key_no_valid_type(self, mock_executor):
        """Test command with no valid action type."""
        mock_executor.config.model_actions = {"no_action": {"invalid": "value"}}

        with pytest.raises(ValueError, match="No valid action"):
            mock_executor.execute_command("no_action")

    def test_execute_command_empty_command_action(self, mock_executor):
        """Test with empty command action dictionary."""
        mock_executor.config.model_actions = {"empty": {}}

        with pytest.raises(ValueError, match="No valid action"):
            mock_executor.execute_command("empty")

    def test_execute_command_invalid_command_name(self, mock_executor):
        """Test with invalid command name."""
        with pytest.raises(ValueError, match="Invalid command name"):
            mock_executor.execute_command("")

        with pytest.raises(ValueError, match="Invalid command name"):
            mock_executor.execute_command(None)

    def test_execute_command_missing_model_actions(self, mock_executor):
        """Test with missing model_actions config."""
        mock_executor.config.model_actions = None

        with pytest.raises(ValueError, match="Missing model_actions config"):
            mock_executor.execute_command("test")

    def test_execute_command_non_gettable_model_actions(self, mock_executor):
        """Test with non-gettable model_actions."""
        mock_executor.config.model_actions = "not_a_dict"

        with pytest.raises(ValueError, match="Config model_actions not accessible"):
            mock_executor.execute_command("test")


class TestCommandExecutorDisplaySetup:
    """Test DISPLAY environment variable setup."""

    @pytest.fixture
    def mock_executor(self):
        """Create a CommandExecutor with mocked dependencies."""
        mock_config = Mock()
        mock_config.model_actions = {}
        mock_model_manager = Mock()
        mock_state_manager = Mock()
        return CommandExecutor(mock_config, mock_model_manager, mock_state_manager)

    def test_display_environment_set_when_missing(self, mock_executor):
        """Test that DISPLAY is set when not present."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("src.chatty_commander.app.command_executor.pyautogui"):
                mock_executor.config.model_actions = {
                    "test": {"action": "keypress", "keys": "space"}
                }

                mock_executor.execute_command("test")

                assert os.environ["DISPLAY"] == ":0"

    def test_display_environment_preserved_when_present(self, mock_executor):
        """Test that existing DISPLAY is preserved."""
        with patch.dict(os.environ, {"DISPLAY": ":1"}):
            with patch("src.chatty_commander.app.command_executor.pyautogui"):
                mock_executor.config.model_actions = {
                    "test": {"action": "keypress", "keys": "space"}
                }

                mock_executor.execute_command("test")

                assert os.environ["DISPLAY"] == ":1"
