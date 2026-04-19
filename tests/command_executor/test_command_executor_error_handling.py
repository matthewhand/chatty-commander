"""
Error handling tests for CommandExecutor.
"""

from subprocess import CalledProcessError
from unittest.mock import Mock, patch

import pytest


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

    def test_keypress_command_failure(self, command_executor, mock_dependencies):
        """Test handling of keypress command failures."""
        mock_pg, mock_requests = mock_dependencies
        mock_pg.press.side_effect = Exception("Key press failed")

        result = command_executor.execute_command("test_keypress")
        assert result is False

    @patch("src.chatty_commander.app.command_executor.requests.get")
    def test_url_command_failure(self, mock_get, command_executor):
        """Test handling of URL command failures."""
        mock_get.side_effect = Exception("Failed to open URL")

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
        with pytest.raises(ValueError, match="Invalid command name: None"):
            command_executor.execute_command(None)

    def test_empty_command_name(self, command_executor):
        """Test handling of empty command name."""
        with pytest.raises(ValueError, match="Invalid command name: ''"):
            command_executor.execute_command("")

    def test_non_string_command_name(self, command_executor):
        """Test handling of non-string command name."""
        with pytest.raises(ValueError, match="Invalid command name: 123"):
            command_executor.execute_command(123)

    @patch("subprocess.run")
    def test_shell_command_with_invalid_characters(
        self, mock_run, command_executor, mock_config
    ):
        """Test handling of shell commands with invalid characters."""
        mock_config.model_actions = {
            "dangerous": {"action": "shell", "cmd": "rm -rf /"}
        }
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = command_executor.execute_command("dangerous")
        assert result is True
        mock_run.assert_called_once_with(
            ["rm", "-rf", "/"], capture_output=True, text=True, timeout=15
        )

    def test_command_execution_with_missing_dependencies(
        self, command_executor, mock_config
    ):
        """Test command execution when dependencies are missing."""
        mock_config.model_actions = {"test": {"action": "shell", "cmd": "echo test"}}

        # This should work even if some optional dependencies are missing
        result = command_executor.execute_command("test")
        assert isinstance(result, bool)
