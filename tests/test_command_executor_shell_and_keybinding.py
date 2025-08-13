import subprocess
from unittest.mock import MagicMock, patch

import pytest
from chatty_commander.app import CommandExecutor


class DummyConfig:
    def __init__(self):
        # Filled per test
        self.model_actions = {}


class DummyModelManager:
    pass


class DummyStateManager:
    pass


@pytest.fixture
def executor():
    config = DummyConfig()
    mm = DummyModelManager()
    sm = DummyStateManager()
    return CommandExecutor(config, mm, sm)


class TestShellExecution:
    @patch('subprocess.run')
    def test_shell_success(self, mock_run, executor, caplog):
        executor.config.model_actions = {'test_shell': {'shell': 'echo hello'}}
        mock_run.return_value = MagicMock(returncode=0, stdout='hello\n', stderr='')

        # Should not raise; should log success
        executor.execute_command('test_shell')

        mock_run.assert_called_once()
        # Accept either 'shell ok' or 'Completed execution' as success indication
        assert any(
            ('shell ok' in rec.message)
            or ('Completed execution of command: test_shell' in rec.message)
            for rec in caplog.records
        )

    @patch('subprocess.run')
    def test_shell_nonzero_exit(self, mock_run, executor, caplog):
        executor.config.model_actions = {'bad_shell': {'shell': 'exit 5'}}
        mock_run.return_value = MagicMock(returncode=5, stdout='', stderr='boom')

        executor.execute_command('bad_shell')

        # Should log error and report_error
        assert any('shell exit 5' in rec.message for rec in caplog.records)
        assert any(
            rec.levelname == 'CRITICAL' and 'Error in bad_shell' in rec.message
            for rec in caplog.records
        )

    @patch('subprocess.run', side_effect=subprocess.TimeoutExpired(cmd=['sleep', '10'], timeout=15))
    def test_shell_timeout(self, mock_run, executor, caplog):
        executor.config.model_actions = {'timeout_shell': {'shell': 'sleep 10'}}

        executor.execute_command('timeout_shell')

        assert any('timed out' in rec.message for rec in caplog.records)
        assert any(
            rec.levelname == 'CRITICAL' and 'timeout_shell' in rec.message for rec in caplog.records
        )

    @patch('subprocess.run', side_effect=RuntimeError('boom'))
    def test_shell_generic_exception(self, mock_run, executor, caplog):
        executor.config.model_actions = {'explode_shell': {'shell': 'whatever'}}

        executor.execute_command('explode_shell')

        assert any('shell execution failed' in rec.message for rec in caplog.records)
        assert any(
            rec.levelname == 'CRITICAL' and 'explode_shell' in rec.message for rec in caplog.records
        )


class TestKeybindingExecution:
    def test_keypress_pyautogui_missing(self, executor, caplog, monkeypatch):
        # Simulate missing pyautogui
        monkeypatch.setattr('chatty_commander.app.command_executor.pyautogui', None, raising=False)
        executor.config.model_actions = {'kp': {'keypress': 'a'}}

        executor.execute_command('kp')

        # Should not raise, should log error and report_error
        assert any('pyautogui is not installed' in rec.message for rec in caplog.records)
        assert any(
            rec.levelname == 'CRITICAL' and 'Error in kp' in rec.message for rec in caplog.records
        )

    def test_keypress_single_key(self, executor, caplog, monkeypatch):
        mock_pg = MagicMock()
        monkeypatch.setattr('chatty_commander.app.command_executor.pyautogui', mock_pg, raising=False)
        executor.config.model_actions = {'kp': {'keypress': 'a'}}

        executor.execute_command('kp')

        mock_pg.press.assert_called_once_with('a')
        # Accept either explicit keybinding log or generic post-exec completion
        assert any(
            ('Executed keybinding for kp' in rec.message)
            or ('Completed execution of command: kp' in rec.message)
            for rec in caplog.records
        )

    def test_keypress_combo_plus_syntax(self, executor, caplog, monkeypatch):
        mock_pg = MagicMock()
        monkeypatch.setattr('chatty_commander.app.command_executor.pyautogui', mock_pg, raising=False)
        executor.config.model_actions = {'kp': {'keypress': 'ctrl+alt+t'}}

        executor.execute_command('kp')

        mock_pg.hotkey.assert_called_once()
        args, kwargs = mock_pg.hotkey.call_args
        assert args == ('ctrl', 'alt', 't')
        assert any(
            ('Executed keybinding for kp' in rec.message)
            or ('Completed execution of command: kp' in rec.message)
            for rec in caplog.records
        )

    def test_keypress_list_hotkey(self, executor, caplog, monkeypatch):
        mock_pg = MagicMock()
        monkeypatch.setattr('chatty_commander.app.command_executor.pyautogui', mock_pg, raising=False)
        executor.config.model_actions = {'kp': {'keypress': ['ctrl', 'shift', ';']}}

        executor.execute_command('kp')

        mock_pg.hotkey.assert_called_once_with('ctrl', 'shift', ';')
        assert any(
            ('Executed keybinding for kp' in rec.message)
            or ('Completed execution of command: kp' in rec.message)
            for rec in caplog.records
        )

    def test_keypress_runtime_error_logged(self, executor, caplog, monkeypatch):
        mock_pg = MagicMock()
        mock_pg.press.side_effect = RuntimeError('kb fail')
        monkeypatch.setattr('chatty_commander.app.command_executor.pyautogui', mock_pg, raising=False)
        executor.config.model_actions = {'kp': {'keypress': 'x'}}

        executor.execute_command('kp')

        assert any('Failed to execute keybinding' in rec.message for rec in caplog.records)
        assert any(
            rec.levelname == 'CRITICAL' and 'Error in kp' in rec.message for rec in caplog.records
        )
