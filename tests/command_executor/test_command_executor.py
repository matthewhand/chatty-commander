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
Comprehensive tests for CommandExecutor functionality.
"""

from unittest.mock import Mock, patch

import pytest


class TestCommandExecutorBasic:
    """Test basic CommandExecutor functionality."""

    def test_initialization(self, command_executor):
        """Test CommandExecutor initializes correctly."""
        assert command_executor.config is not None
        assert command_executor.model_manager is not None
        assert command_executor.state_manager is not None
        assert command_executor.last_command is None

    def test_validate_command_valid(self, command_executor):
        """Test command validation with valid commands."""
        assert command_executor.validate_command("test_shell") is True
        assert command_executor.validate_command("test_keypress") is True
        assert command_executor.validate_command("test_url") is True
        assert command_executor.validate_command("test_message") is True

    def test_validate_command_invalid(self, command_executor):
        """Test command validation with invalid commands."""
        assert command_executor.validate_command("nonexistent") is False
        assert command_executor.validate_command("") is False
        assert command_executor.validate_command(None) is False

    def test_pre_execute_hook(self, command_executor):
        """Test pre-execute hook functionality."""
        command_executor.pre_execute_hook("test_shell")
        assert command_executor.last_command == "test_shell"

    @patch("subprocess.run")
    def test_execute_shell_command(self, mock_run, command_executor):
        """Test shell command execution."""
        mock_run.return_value = Mock(returncode=0, stdout="test", stderr="")

        result = command_executor.execute_command("test_shell")
        assert result is True
        mock_run.assert_called_once_with(
            ["echo", "test"], capture_output=True, text=True, timeout=15
        )

    def test_execute_keypress_command(self, command_executor, mock_dependencies):
        """Test keypress command execution."""
        mock_pg, mock_requests = mock_dependencies
        result = command_executor.execute_command("test_keypress")
        assert result is True
        mock_pg.press.assert_called_once_with("space")

    def test_execute_url_command(self, command_executor, mock_dependencies):
        """Test URL command execution."""
        mock_pg, mock_requests = mock_dependencies
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        result = command_executor.execute_command("test_url")
        assert result is True
        mock_requests.get.assert_called_once_with("http://example.com")

    def test_execute_custom_message_command(self, command_executor):
        """Test custom message command execution."""
        result = command_executor.execute_command("test_message")
        assert result is True

    def test_execute_invalid_action(self, command_executor, mock_config):
        """Test execution of command with invalid action."""
        mock_config.model_actions = {"invalid": {"action": "unknown"}}

        with pytest.raises(ValueError, match="invalid action type"):
            command_executor.execute_command("invalid")

    def test_execute_missing_action(self, command_executor, mock_config):
        """Test execution of command with missing action."""
        mock_config.model_actions = {"no_action": {}}

        with pytest.raises(ValueError, match="invalid type"):
            command_executor.execute_command("no_action")
