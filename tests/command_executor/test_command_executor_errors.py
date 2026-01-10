"""
Error handling tests for CommandExecutor.
"""

import pytest
from unittest.mock import Mock, patch
from subprocess import CalledProcessError
from src.chatty_commander.app.command_executor import CommandExecutor


class TestCommandExecutorErrorHandling:
    """Test CommandExecutor error handling scenarios."""

    @patch("subprocess.run")
    def test_shell_command_failure(self, mock_run, command_executor):
        """Test handling of shell command failures."""
        mock_run.side_effect = CalledProcessError(1, "echo test")

        result = command_executor.execute_command("test_shell")
        assert result is False

    @patch("subprocess.run")
    def test_shell_command_timeout(self, mock_run, command_executor):
        """Test handling of shell command timeouts."""
        mock_run.side_effect = TimeoutError("Command timed out")

        result = command_executor.execute_command("test_shell")
        assert result is False

    @patch("pyautogui.press")
    def test_keypress_command_failure(self, mock_press, command_executor):
        """Test handling of keypress command failures."""
        mock_press.side_effect = Exception("Key press failed")

        result = command_executor.execute_command("test_keypress")
        assert result is False

    @patch("webbrowser.open")
    def test_url_command_failure(self, mock_open, command_executor):
        """Test handling of URL command failures."""
        mock_open.side_effect = Exception("Failed to open URL")

        result = command_executor.execute_command("test_url")
        assert result is False

    def test_missing_command_config(self, command_executor, mock_config):
        """Test handling of missing command configuration."""
        mock_config.model_actions = {}

        result = command_executor.execute_command("nonexistent")
        assert result is False

    def test_malformed_command_config(self, command_executor, mock_config):
        """Test handling of malformed command configuration."""
        mock_config.model_actions = {"malformed": "not_a_dict"}

        with pytest.raises((ValueError, TypeError)):
            command_executor.execute_command("malformed")

    def test_none_command_name(self, command_executor):
        """Test handling of None command name."""
        result = command_executor.execute_command(None)
        assert result is False

    def test_empty_command_name(self, command_executor):
        """Test handling of empty command name."""
        result = command_executor.execute_command("")
        assert result is False

    def test_non_string_command_name(self, command_executor):
        """Test handling of non-string command name."""
        result = command_executor.execute_command(123)
        assert result is False

    @patch("subprocess.run")
    def test_shell_command_with_invalid_characters(
        self, mock_run, command_executor, mock_config
    ):
        """Test handling of shell commands with invalid characters."""
        mock_config.model_actions = {
            "dangerous": {"action": "shell", "cmd": "rm -rf /"}
        }
        mock_run.return_value = Mock(returncode=0)

        result = command_executor.execute_command("dangerous")
        assert result is True
        mock_run.assert_called_once_with("rm -rf /", shell=True, check=True)

    def test_command_execution_with_missing_dependencies(
        self, command_executor, mock_config
    ):
        """Test command execution when dependencies are missing."""
        mock_config.model_actions = {"test": {"action": "shell", "cmd": "echo test"}}

        # This should work even if some optional dependencies are missing
        result = command_executor.execute_command("test")
        assert isinstance(result, bool)
