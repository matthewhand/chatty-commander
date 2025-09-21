import pytest
from unittest.mock import patch


def test_execute_command_keypress(mock_executor):
    """Test keypress command execution."""
    result = mock_executor.execute_command("mock_cmd")
    assert result is True
    mock_executor._execute_keybinding.assert_called_once_with("mock_cmd", "space")


def test_execute_command_new_format_keypress(setup_executor):
    """Test execute_command with new format keypress action."""
    setup_executor.config.model_actions = {
        "test_cmd": {"action": "keypress", "keys": "ctrl+c"}
    }
    with patch.object(setup_executor, "_execute_keybinding") as mock_key:
        mock_key.return_value = True
        result = setup_executor.execute_command("test_cmd")
        assert result is True
        mock_key.assert_called_once_with("test_cmd", "ctrl+c")


def test_execute_command_old_format_keypress(setup_executor):
    """Test execute_command with old format keypress action."""
    setup_executor.config.model_actions = {"test_cmd": {"keypress": "ctrl+c"}}
    with patch.object(setup_executor, "_execute_keybinding") as mock_key:
        mock_key.return_value = True
        result = setup_executor.execute_command("test_cmd")
        assert result is True
        mock_key.assert_called_once_with("test_cmd", "ctrl+c")


def test_execute_keybinding_no_pyautogui(setup_executor):
    """Test _execute_keybinding when pyautogui is not available."""
    with patch("chatty_commander.app.command_executor.pyautogui", None):
        with patch.object(setup_executor, "report_error") as mock_report:
            setup_executor._execute_keybinding("test_cmd", "space")
            mock_report.assert_called_once_with("test_cmd", "pyautogui is not installed")


def test_execute_keybinding_list_keys(setup_executor):
    """Test _execute_keybinding with list of keys."""
    with patch("chatty_commander.app.command_executor.pyautogui") as mock_pg:
        setup_executor._execute_keybinding("test_cmd", ["ctrl", "c"])
        mock_pg.hotkey.assert_called_once_with("ctrl", "c")


def test_execute_keybinding_plus_separated_keys(setup_executor):
    """Test _execute_keybinding with plus-separated keys."""
    with patch("chatty_commander.app.command_executor.pyautogui") as mock_pg:
        setup_executor._execute_keybinding("test_cmd", "ctrl+alt+t")
        mock_pg.hotkey.assert_called_once_with("ctrl", "alt", "t")


def test_execute_keybinding_simple_key(setup_executor):
    """Test _execute_keybinding with simple key."""
    with patch("chatty_commander.app.command_executor.pyautogui") as mock_pg:
        setup_executor._execute_keybinding("test_cmd", "space")
        mock_pg.press.assert_called_once_with("space")


def test_execute_keybinding_exception(setup_executor):
    """Test _execute_keybinding exception handling."""
    with patch("chatty_commander.app.command_executor.pyautogui") as mock_pg:
        mock_pg.press.side_effect = Exception("Test error")
        with patch.object(setup_executor, "report_error") as mock_report:
            setup_executor._execute_keybinding("test_cmd", "space")
            mock_report.assert_called_once_with("test_cmd", "Test error")
