import subprocess
from unittest.mock import MagicMock, patch
import pytest
from chatty_commander.app.command_executor import CommandExecutor

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.model_actions = {
        "malicious_cmd": {"action": "shell", "cmd": "cat /etc/passwd"},
        "safe_cmd": {"action": "shell", "cmd": "echo hello"},
        "absolute_safe_cmd": {"action": "shell", "cmd": "/bin/echo hello"}
    }
    config.allowed_shell_commands = ["echo"]
    return config

@pytest.fixture
def executor(mock_config):
    return CommandExecutor(mock_config, MagicMock(), MagicMock())

def test_repro_arbitrary_shell_execution_blocked(executor):
    with patch("chatty_commander.app.command_executor.subprocess.run") as mock_run:
        # malicious_cmd: cat /etc/passwd -> 'cat' is not in ['echo']
        success = executor.execute_command("malicious_cmd")

        assert success is False
        mock_run.assert_not_called()

def test_safe_shell_execution_allowed(executor):
    with patch("chatty_commander.app.command_executor.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="hello")

        # safe_cmd: echo hello -> 'echo' is in ['echo']
        success = executor.execute_command("safe_cmd")

        assert success is True
        mock_run.assert_called_once()

def test_absolute_path_safe_shell_execution_allowed(executor):
    with patch("chatty_commander.app.command_executor.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="hello")

        # absolute_safe_cmd: /bin/echo hello -> basename is 'echo', which is in ['echo']
        success = executor.execute_command("absolute_safe_cmd")

        assert success is True
        mock_run.assert_called_once()
