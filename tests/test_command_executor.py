import subprocess
from unittest.mock import MagicMock, patch

import pytest

from chatty_commander.app.command_executor import CommandExecutor


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.model_actions = {
        "test_keypress": {"action": "keypress", "keys": "ctrl+c"},
        "test_url": {"action": "url", "url": "http://example.com"},
        "test_shell": {"action": "shell", "cmd": "echo hello"},
        "test_old_keypress": {"keypress": "a"},
        "test_voice": {"action": "voice_chat"},
        "invalid_cmd": {"action": "unknown"}
    }
    return config

@pytest.fixture
def executor(mock_config):
    return CommandExecutor(mock_config, MagicMock(), MagicMock())

class TestCommandExecutor:
    def test_validate_command_valid(self, executor):
        assert executor.validate_command("test_keypress") is True
        assert executor.validate_command("test_url") is True
        assert executor.validate_command("test_shell") is True
        assert executor.validate_command("test_old_keypress") is True

    def test_validate_command_invalid(self, executor):
        assert executor.validate_command("nonexistent") is False
        assert executor.validate_command("invalid_cmd") is False
        assert executor.validate_command("") is False
        # Test missing model_actions
        executor.config.model_actions = None
        assert executor.validate_command("test_keypress") is False

    @patch("chatty_commander.app.command_executor.pyautogui")
    def test_execute_keypress_hotkey(self, mock_pyautogui, executor):
        assert executor.execute_command("test_keypress") is True
        mock_pyautogui.hotkey.assert_called_once_with("ctrl", "c")

    @patch("chatty_commander.app.command_executor.pyautogui")
    def test_execute_keypress_simple(self, mock_pyautogui, executor):
        executor.config.model_actions["simple_key"] = {"action": "keypress", "keys": "a"}
        assert executor.execute_command("simple_key") is True
        mock_pyautogui.press.assert_called_once_with("a")

    @patch("chatty_commander.app.command_executor.requests")
    def test_execute_url_success(self, mock_requests, executor):
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Configure the mock to return this response
        mock_requests.get.return_value = mock_response

        assert executor.execute_command("test_url") is True
        mock_requests.get.assert_called_once_with("http://example.com")

    @patch("chatty_commander.app.command_executor.requests")
    def test_execute_url_failure(self, mock_requests, executor):
        # Setup mock to raise an exception
        mock_requests.get.side_effect = Exception("Network error")

        # Should return True because the exception is caught and logged,
        # but technically the method returns success=True for URL type if it attempted it?
        # Re-reading code: _execute_url sets success=True in the loop logic commands.
        # Wait, the main execute_command sets success=True if action_type == "url".
        # The exception in _execute_url is caught and reported, but the return in execute_command is hardcoded True for URL.
        # Let's verify this behavior.
        assert executor.execute_command("test_url") is True
        mock_requests.get.assert_called_once()

    @patch("chatty_commander.app.command_executor.subprocess.run")
    def test_execute_shell_success(self, mock_run, executor):
        mock_run.return_value = MagicMock(returncode=0, stdout="hello")
        assert executor.execute_command("test_shell") is True
        # Verify shlex split happened effectively (checking first arg)
        assert mock_run.call_args[0][0][0] == "echo"

    @patch("chatty_commander.app.command_executor.subprocess.run")
    def test_execute_shell_failure(self, mock_run, executor):
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        assert executor.execute_command("test_shell") is False

    @patch("chatty_commander.app.command_executor.subprocess.run")
    def test_execute_shell_timeout(self, mock_run, executor):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="cmd", timeout=15)
        assert executor.execute_command("test_shell") is False

    def test_execute_voice_chat(self, executor):
        # Setup mocks for voice chat components
        mock_llm = MagicMock()
        mock_pipeline = MagicMock()
        mock_transcriber = MagicMock()
        mock_tts = MagicMock()

        executor.config.llm_manager = mock_llm
        executor.config.voice_pipeline = mock_pipeline
        mock_pipeline.transcriber = mock_transcriber
        mock_pipeline.tts = mock_tts

        mock_transcriber.record_and_transcribe.return_value = "hello"
        mock_llm.generate_response.return_value = "hello user"
        mock_tts.is_available.return_value = True

        assert executor.execute_command("test_voice") is True

        mock_transcriber.record_and_transcribe.assert_called_once()
        mock_llm.generate_response.assert_called_once_with("hello")
        mock_tts.speak.assert_called_once_with("hello user")

    def test_execute_unknown_command(self, executor):
        assert executor.execute_command("nonexistent") is False

    def test_execute_missing_model_actions(self, executor):
        executor.config.model_actions = None
        with pytest.raises(ValueError, match="Missing model_actions"):
            executor.execute_command("some_cmd")
