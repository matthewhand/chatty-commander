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
Shell command execution tests for CommandExecutor.
"""

from subprocess import TimeoutExpired
from unittest.mock import Mock, patch


class TestCommandExecutorShell:
    """Test shell command execution functionality."""

    @patch("subprocess.run")
    def test_simple_shell_command(self, mock_run, command_executor):
        """Test execution of simple shell command."""
        mock_run.return_value = Mock(returncode=0, stdout="test", stderr="")

        result = command_executor.execute_command("test_shell")
        assert result is True
        mock_run.assert_called_once_with(
            ["echo", "test"], capture_output=True, text=True, timeout=15
        )

    @patch("subprocess.run")
    def test_shell_command_with_args(self, mock_run, command_executor, mock_config):
        """Test shell command with arguments."""
        mock_config.model_actions = {
            "complex_shell": {"action": "shell", "cmd": "ls -la /tmp"}
        }
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = command_executor.execute_command("complex_shell")
        assert result is True
        mock_run.assert_called_once_with(
            ["ls", "-la", "/tmp"], capture_output=True, text=True, timeout=15
        )

    @patch("subprocess.run")
    def test_shell_command_failure_nonzero_exit(self, mock_run, command_executor):
        """Test shell command that returns non-zero exit code."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="error")

        result = command_executor.execute_command("test_shell")
        assert result is False

    @patch("subprocess.run")
    def test_shell_command_timeout(self, mock_run, command_executor):
        """Test shell command that times out."""
        mock_run.side_effect = TimeoutError("Command timed out")

        result = command_executor.execute_command("test_shell")
        assert result is False

    @patch("subprocess.run")
    def test_shell_command_permission_denied(self, mock_run, command_executor):
        """Test shell command with permission denied error."""
        mock_run.side_effect = PermissionError("Permission denied")

        result = command_executor.execute_command("test_shell")
        assert result is False

    @patch("subprocess.run")
    def test_shell_command_file_not_found(self, mock_run, command_executor):
        """Test shell command with file not found error."""
        mock_run.side_effect = FileNotFoundError("Command not found")

        result = command_executor.execute_command("test_shell")
        assert result is False

    @patch("subprocess.run")
    def test_shell_command_with_quoted_args(
        self, mock_run, command_executor, mock_config
    ):
        """Test shell command with quoted arguments."""
        mock_config.model_actions = {
            "quote_shell": {"action": "shell", "cmd": 'echo "hello world"'}
        }
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = command_executor.execute_command("quote_shell")
        assert result is True
        mock_run.assert_called_once_with(
            ["echo", "hello world"], capture_output=True, text=True, timeout=15
        )

    @patch("subprocess.run")
    def test_shell_command_timeout_exception(self, mock_run, command_executor):
        """Test shell command that raises TimeoutExpired."""
        mock_run.side_effect = TimeoutExpired("echo test", 15)

        result = command_executor.execute_command("test_shell")
        assert result is False

    @patch("subprocess.run")
    def test_shell_command_empty_command(self, mock_run, command_executor, mock_config):
        """Test shell command with empty command."""
        mock_config.model_actions = {"empty_shell": {"action": "shell", "cmd": ""}}

        result = command_executor.execute_command("empty_shell")
        assert result is False
        mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_shell_command_with_output(self, mock_run, command_executor, mock_config):
        """Test shell command that produces output."""
        mock_config.model_actions = {
            "output_shell": {"action": "shell", "cmd": "echo 'hello world'"}
        }
        mock_run.return_value = Mock(returncode=0, stdout="hello world\n", stderr="")

        result = command_executor.execute_command("output_shell")
        assert result is True
        mock_run.assert_called_once_with(
            ["echo", "hello world"], capture_output=True, text=True, timeout=15
        )
