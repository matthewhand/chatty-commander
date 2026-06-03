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
        "invalid_cmd": {"action": "unknown"},
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
        executor.config.model_actions["simple_key"] = {
            "action": "keypress",
            "keys": "a",
        }
        assert executor.execute_command("simple_key") is True
        mock_pyautogui.press.assert_called_once_with("a")

    @patch("chatty_commander.utils.url_validator.is_safe_url", return_value=True)
    @patch("chatty_commander.app.command_executor.httpx")
    def test_execute_url_success(self, mock_httpx, mock_is_safe, executor):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Configure the mock to return this response
        mock_client.get.return_value = mock_response
        mock_httpx.Client.return_value.__enter__.return_value = mock_client

        assert executor.execute_command("test_url") is True
        mock_client.get.assert_called_once_with(
            "http://example.com", timeout=10, follow_redirects=False
        )

    @patch("chatty_commander.utils.url_validator.is_safe_url", return_value=True)
    @patch("chatty_commander.app.command_executor.httpx")
    def test_execute_url_failure(self, mock_httpx, mock_is_safe, executor):
        mock_client = MagicMock()
        # Setup mock to raise an exception
        mock_client.get.side_effect = Exception("Network error")
        mock_httpx.Client.return_value.__enter__.return_value = mock_client

        assert executor.execute_command("test_url") is True
        mock_client.get.assert_called_once_with(
            "http://example.com", timeout=10, follow_redirects=False
        )

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


# ---------------------------------------------------------------------------
# Shell execution edge-case tests (caplog-based logging assertions)
# ---------------------------------------------------------------------------


class TestShellExecution:
    @pytest.fixture(autouse=True)
    def _setup_executor(self):
        """Create an executor with plain dummy objects (no MagicMock config)."""
        config = MagicMock()
        config.model_actions = {}
        self.executor = CommandExecutor(config, MagicMock(), MagicMock())

    @patch("subprocess.run")
    def test_shell_success(self, mock_run, caplog):
        self.executor.config.model_actions = {
            "test_shell": {"shell": "echo hello"},
        }
        mock_run.return_value = MagicMock(returncode=0, stdout="hello\n", stderr="")

        self.executor.execute_command("test_shell")

        mock_run.assert_called_once()
        assert any(
            ("shell ok" in rec.message)
            or ("Completed execution of command: test_shell" in rec.message)
            for rec in caplog.records
        )

    @patch("subprocess.run")
    def test_shell_nonzero_exit(self, mock_run, caplog):
        self.executor.config.model_actions = {
            "bad_shell": {"shell": "exit 5"},
        }
        mock_run.return_value = MagicMock(returncode=5, stdout="", stderr="boom")

        self.executor.execute_command("bad_shell")

        assert any("shell exit 5" in rec.message for rec in caplog.records)
        assert any(
            rec.levelname == "CRITICAL" and "Error in bad_shell" in rec.message
            for rec in caplog.records
        )

    @patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd=["sleep", "10"], timeout=15),
    )
    def test_shell_timeout(self, mock_run, caplog):
        self.executor.config.model_actions = {
            "timeout_shell": {"shell": "sleep 10"},
        }

        self.executor.execute_command("timeout_shell")

        assert any("timed out" in rec.message for rec in caplog.records)
        assert any(
            rec.levelname == "CRITICAL" and "timeout_shell" in rec.message
            for rec in caplog.records
        )

    @patch("subprocess.run", side_effect=RuntimeError("boom"))
    def test_shell_generic_exception(self, mock_run, caplog):
        self.executor.config.model_actions = {
            "explode_shell": {"shell": "whatever"},
        }

        self.executor.execute_command("explode_shell")

        assert any("shell execution failed" in rec.message for rec in caplog.records)
        assert any(
            rec.levelname == "CRITICAL" and "explode_shell" in rec.message
            for rec in caplog.records
        )


# ---------------------------------------------------------------------------
# Keybinding execution edge-case tests (caplog + monkeypatch assertions)
# ---------------------------------------------------------------------------


class TestKeybindingExecution:
    @pytest.fixture(autouse=True)
    def _setup_executor(self):
        """Create an executor with plain dummy objects (no MagicMock config)."""
        config = MagicMock()
        config.model_actions = {}
        self.executor = CommandExecutor(config, MagicMock(), MagicMock())

    def test_keypress_pyautogui_missing(self, caplog, monkeypatch):
        monkeypatch.setattr(
            "chatty_commander.app.command_executor.pyautogui", None, raising=False
        )
        self.executor.config.model_actions = {"kp": {"keypress": "a"}}

        self.executor.execute_command("kp")

        assert any(
            "pyautogui is not installed" in rec.message for rec in caplog.records
        )
        assert any(
            rec.levelname == "CRITICAL" and "Error in kp" in rec.message
            for rec in caplog.records
        )

    def test_keypress_single_key(self, caplog, monkeypatch):
        mock_pg = MagicMock()
        monkeypatch.setattr(
            "chatty_commander.app.command_executor.pyautogui", mock_pg, raising=False
        )
        self.executor.config.model_actions = {"kp": {"keypress": "a"}}

        with caplog.at_level("INFO"):
            self.executor.execute_command("kp")

        mock_pg.press.assert_called_once_with("a")
        assert any(
            ("Executed keybinding for kp" in rec.message)
            or ("Completed execution of command: kp" in rec.message)
            for rec in caplog.records
        )

    def test_keypress_combo_plus_syntax(self, caplog, monkeypatch):
        mock_pg = MagicMock()
        monkeypatch.setattr(
            "chatty_commander.app.command_executor.pyautogui", mock_pg, raising=False
        )
        self.executor.config.model_actions = {"kp": {"keypress": "ctrl+alt+t"}}

        with caplog.at_level("INFO"):
            self.executor.execute_command("kp")

        mock_pg.hotkey.assert_called_once()
        args, kwargs = mock_pg.hotkey.call_args
        assert args == ("ctrl", "alt", "t")
        assert any(
            ("Executed keybinding for kp" in rec.message)
            or ("Completed execution of command: kp" in rec.message)
            for rec in caplog.records
        )

    def test_keypress_list_hotkey(self, caplog, monkeypatch):
        mock_pg = MagicMock()
        monkeypatch.setattr(
            "chatty_commander.app.command_executor.pyautogui", mock_pg, raising=False
        )
        self.executor.config.model_actions = {
            "kp": {"keypress": ["ctrl", "shift", ";"]},
        }

        with caplog.at_level("INFO"):
            self.executor.execute_command("kp")

        mock_pg.hotkey.assert_called_once_with("ctrl", "shift", ";")
        assert any(
            ("Executed keybinding for kp" in rec.message)
            or ("Completed execution of command: kp" in rec.message)
            for rec in caplog.records
        )

    def test_keypress_runtime_error_logged(self, caplog, monkeypatch):
        mock_pg = MagicMock()
        mock_pg.press.side_effect = RuntimeError("kb fail")
        monkeypatch.setattr(
            "chatty_commander.app.command_executor.pyautogui", mock_pg, raising=False
        )
        self.executor.config.model_actions = {"kp": {"keypress": "x"}}

        self.executor.execute_command("kp")

        assert any(
            "Failed to execute keybinding" in rec.message for rec in caplog.records
        )
        assert any(
            rec.levelname == "CRITICAL" and "Error in kp" in rec.message
            for rec in caplog.records
        )
