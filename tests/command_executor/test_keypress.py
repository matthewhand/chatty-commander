"""
Keypress command execution tests for CommandExecutor.
"""

import pytest
from unittest.mock import Mock, patch, call
from src.chatty_commander.app.command_executor import CommandExecutor


class TestCommandExecutorKeypress:
    """Test keypress command execution functionality."""

    @patch("pyautogui.press")
    def test_single_keypress(self, mock_press, command_executor):
        """Test execution of single keypress."""
        result = command_executor.execute_command("test_keypress")
        assert result is True
        mock_press.assert_called_once_with("space")

    @patch("pyautogui.press")
    def test_multiple_keypress(self, mock_press, command_executor, mock_config):
        """Test execution of multiple keypresses."""
        mock_config.model_actions = {
            "multi_keypress": {"action": "keypress", "keys": ["ctrl", "c"]}
        }

        result = command_executor.execute_command("multi_keypress")
        assert result is True
        mock_press.assert_called_once_with(["ctrl", "c"])

    @patch("pyautogui.press")
    def test_function_keypress(self, mock_press, command_executor, mock_config):
        """Test execution of function keypress."""
        mock_config.model_actions = {
            "f_keypress": {"action": "keypress", "keys": "f12"}
        }

        result = command_executor.execute_command("f_keypress")
        assert result is True
        mock_press.assert_called_once_with("f12")

    @patch("pyautogui.press")
    def test_modifier_keypress(self, mock_press, command_executor, mock_config):
        """Test execution of modifier keypress."""
        mock_config.model_actions = {
            "mod_keypress": {"action": "keypress", "keys": ["alt", "f4"]}
        }

        result = command_executor.execute_command("mod_keypress")
        assert result is True
        mock_press.assert_called_once_with(["alt", "f4"])

    @patch("pyautogui.press")
    def test_special_keypress(self, mock_press, command_executor, mock_config):
        """Test execution of special keypress."""
        mock_config.model_actions = {
            "special_keypress": {"action": "keypress", "keys": "enter"}
        }

        result = command_executor.execute_command("special_keypress")
        assert result is True
        mock_press.assert_called_once_with("enter")

    @patch("pyautogui.press")
    def test_keypress_failure(self, mock_press, command_executor):
        """Test handling of keypress failure."""
        mock_press.side_effect = Exception("Key press failed")

        result = command_executor.execute_command("test_keypress")
        assert result is False

    @patch("pyautogui.press")
    def test_keypress_with_invalid_key(self, mock_press, command_executor, mock_config):
        """Test keypress with invalid key."""
        mock_config.model_actions = {
            "invalid_keypress": {"action": "keypress", "keys": "invalid_key_12345"}
        }
        mock_press.side_effect = Exception("Invalid key")

        result = command_executor.execute_command("invalid_keypress")
        assert result is False

    @patch("pyautogui.press")
    def test_keypress_with_empty_keys(self, mock_press, command_executor, mock_config):
        """Test keypress with empty keys."""
        mock_config.model_actions = {
            "empty_keypress": {"action": "keypress", "keys": []}
        }

        result = command_executor.execute_command("empty_keypress")
        assert result is True
        mock_press.assert_called_once_with([])

    @patch("pyautogui.press")
    def test_keypress_with_none_keys(self, mock_press, command_executor, mock_config):
        """Test keypress with None keys."""
        mock_config.model_actions = {
            "none_keypress": {"action": "keypress", "keys": None}
        }

        result = command_executor.execute_command("none_keypress")
        assert result is False

    @pytest.mark.parametrize(
        "key",
        [
            "escape",
            "tab",
            "backspace",
            "delete",
            "home",
            "end",
            "pageup",
            "pagedown",
            "up",
            "down",
            "left",
            "right",
            "shift",
            "ctrl",
            "alt",
            "cmd",
            "win",
        ],
    )
    @patch("pyautogui.press")
    def test_common_keypress_keys(self, mock_press, command_executor, mock_config, key):
        """Test common keypress keys."""
        mock_config.model_actions = {
            "common_keypress": {"action": "keypress", "keys": key}
        }

        result = command_executor.execute_command("common_keypress")
        assert result is True
        mock_press.assert_called_once_with(key)

    @pytest.mark.parametrize(
        "key_combo",
        [
            ["ctrl", "v"],
            ["ctrl", "c"],
            ["ctrl", "z"],
            ["ctrl", "y"],
            ["alt", "tab"],
            ["ctrl", "alt", "delete"],
            ["cmd", "q"],
            ["ctrl", "s"],
            ["ctrl", "f"],
            ["ctrl", "h"],
        ],
    )
    @patch("pyautogui.press")
    def test_common_key_combinations(
        self, mock_press, command_executor, mock_config, key_combo
    ):
        """Test common key combinations."""
        mock_config.model_actions = {
            "combo_keypress": {"action": "keypress", "keys": key_combo}
        }

        result = command_executor.execute_command("combo_keypress")
        assert result is True
        mock_press.assert_called_once_with(key_combo)
