from unittest.mock import patch, MagicMock
import subprocess


def test_execute_command_shell(setup_executor):
    """Test shell command execution."""
    setup_executor.config.model_actions["test_shell"] = {"shell": "echo test"}
    with patch.object(setup_executor, "_execute_shell") as mock_shell:
        mock_shell.return_value = True
        result = setup_executor.execute_command("test_shell")
        assert result is True
        mock_shell.assert_called_once_with("test_shell", "echo test")


def test_execute_command_new_format_shell(setup_executor):
    """Test execute_command with new format shell action."""
    setup_executor.config.model_actions = {
        "test_cmd": {"action": "shell", "cmd": "echo test"}
    }
    with patch.object(setup_executor, "_execute_shell") as mock_shell:
        mock_shell.return_value = True
        result = setup_executor.execute_command("test_cmd")
        assert result is True
        mock_shell.assert_called_once_with("test_cmd", "echo test")


def test_execute_command_old_format_shell(setup_executor):
    """Test execute_command with old format shell action."""
    setup_executor.config.model_actions = {"test_cmd": {"shell": "echo test"}}
    with patch.object(setup_executor, "_execute_shell") as mock_shell:
        mock_shell.return_value = True
        result = setup_executor.execute_command("test_cmd")
        assert result is True
        mock_shell.assert_called_once_with("test_cmd", "echo test")


def test_execute_shell_empty_command(setup_executor):
    """Test _execute_shell with empty command."""
    result = setup_executor._execute_shell("test_cmd", "")
    assert result is False


def test_execute_shell_nonzero_exit(setup_executor):
    """Test _execute_shell with non-zero exit code."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "Command failed"
    with patch("subprocess.run", return_value=mock_result):
        with patch.object(setup_executor, "report_error") as mock_report:
            result = setup_executor._execute_shell("test_cmd", "false")
            assert result is False
            mock_report.assert_called_once()


def test_execute_shell_timeout(setup_executor):
    """Test _execute_shell with timeout."""
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("echo test", 15)):
        with patch.object(setup_executor, "report_error") as mock_report:
            result = setup_executor._execute_shell("test_cmd", "echo test")
            assert result is False
            mock_report.assert_called_once_with("test_cmd", "shell command timed out")


def test_execute_shell_exception(setup_executor):
    """Test _execute_shell exception handling."""
    with patch("subprocess.run", side_effect=Exception("Execution error")):
        with patch.object(setup_executor, "report_error") as mock_report:
            result = setup_executor._execute_shell("test_cmd", "echo test")
            assert result is False
            mock_report.assert_called_once_with("test_cmd", "Execution error")
