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

"""Tests for shell command execution in CommandExecutor."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from chatty_commander.app.command_executor import CommandExecutor


class TestCommandExecutorShellSecurity:
    """Security-focused tests for _execute_shell."""

    @pytest.fixture
    def executor(self):
        config = MagicMock()
        model_manager = MagicMock()
        state_manager = MagicMock()
        return CommandExecutor(config, model_manager, state_manager)

    def test_execute_shell_allowed_command(self, executor):
        """Test that whitelisted shell command is executed."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="hello", stderr="")

            result = executor._execute_shell("test_cmd", "echo hello")

            assert result is True
            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            assert args[0] == ["echo", "hello"]

    def test_execute_shell_disallowed_command(self, executor):
        """Test that non-whitelisted shell command is rejected."""
        with patch("subprocess.run") as mock_run:
            with patch.object(executor, "report_error") as mock_report:
                result = executor._execute_shell("test_cmd", "ls -la")

                assert result is False
                mock_run.assert_not_called()
                mock_report.assert_called_once_with("test_cmd", "unsafe shell command rejected")

    def test_execute_shell_dangerous_characters(self, executor):
        """Test that commands with dangerous characters are rejected."""
        with patch("subprocess.run") as mock_run:
            with patch.object(executor, "report_error") as mock_report:
                result = executor._execute_shell("test_cmd", "echo hello; rm -rf /")

                assert result is False
                mock_run.assert_not_called()
                mock_report.assert_called_once_with("test_cmd", "unsafe shell command rejected")

    def test_execute_shell_empty_command(self, executor):
        """Test handling of empty shell command."""
        with patch.object(executor, "report_error") as mock_report:
            result = executor._execute_shell("test_cmd", "")

            assert result is False
            mock_report.assert_called_once_with("test_cmd", "missing shell command")

    def test_execute_shell_timeout(self, executor):
        """Test handling of shell command timeout."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["echo"], 15)):
            with patch.object(executor, "report_error") as mock_report:
                result = executor._execute_shell("test_cmd", "echo long_run")

                assert result is False
                mock_report.assert_called_once_with("test_cmd", "shell command timed out")

    def test_execute_shell_non_zero_exit(self, executor):
        """Test handling of non-zero exit status."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error message")
            with patch.object(executor, "report_error") as mock_report:
                result = executor._execute_shell("test_cmd", "echo fail")

                assert result is False
                assert "shell exit 1" in mock_report.call_args[0][1]
