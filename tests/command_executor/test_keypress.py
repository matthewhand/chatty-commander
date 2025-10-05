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
Keypress command execution tests for CommandExecutor.
"""

import pytest


class TestCommandExecutorKeypress:
    """Test keypress command execution functionality."""

    def test_single_keypress(self, command_executor, mock_dependencies):
        """Test execution of single keypress."""
        mock_pyautogui, _ = mock_dependencies
        result = command_executor.execute_command("test_keypress")
        assert result is True
        mock_pyautogui.press.assert_called_once_with("space")

    def test_multiple_keypress(self, command_executor, mock_config, mock_dependencies):
        """Test execution of multiple keypresses."""
        mock_pyautogui, _ = mock_dependencies
        mock_config.model_actions = {
            "multi_keypress": {"action": "keypress", "keys": ["ctrl", "c"]}
        }

        result = command_executor.execute_command("multi_keypress")
        assert result is True
        mock_pyautogui.hotkey.assert_called_once_with("ctrl", "c")

    def test_function_keypress(self, command_executor, mock_config, mock_dependencies):
        """Test execution of function keypress."""
        mock_pyautogui, _ = mock_dependencies
        mock_config.model_actions = {
            "f_keypress": {"action": "keypress", "keys": "f12"}
        }

        result = command_executor.execute_command("f_keypress")
        assert result is True
        mock_pyautogui.press.assert_called_once_with("f12")

    def test_modifier_keypress(self, command_executor, mock_config, mock_dependencies):
        """Test execution of modifier keypress."""
        mock_pyautogui, _ = mock_dependencies
        mock_config.model_actions = {
            "mod_keypress": {"action": "keypress", "keys": ["alt", "f4"]}
        }

        result = command_executor.execute_command("mod_keypress")
        assert result is True
        mock_pyautogui.hotkey.assert_called_once_with("alt", "f4")

    def test_special_keypress(self, command_executor, mock_config, mock_dependencies):
        """Test execution of special keypress."""
        mock_pyautogui, _ = mock_dependencies
        mock_config.model_actions = {
            "special_keypress": {"action": "keypress", "keys": "enter"}
        }

        result = command_executor.execute_command("special_keypress")
        assert result is True
        mock_pyautogui.press.assert_called_once_with("enter")

    def test_keypress_failure(self, command_executor, mock_dependencies):
        """Test handling of keypress failure."""
        mock_pyautogui, _ = mock_dependencies
        mock_pyautogui.press.side_effect = Exception("Key press failed")

        result = command_executor.execute_command("test_keypress")
        assert result is False

    def test_keypress_with_invalid_key(
        self, command_executor, mock_config, mock_dependencies
    ):
        """Test keypress with invalid key."""
        mock_pyautogui, _ = mock_dependencies
        mock_config.model_actions = {
            "invalid_keypress": {"action": "keypress", "keys": "invalid_key_12345"}
        }
        mock_pyautogui.press.side_effect = Exception("Invalid key")

        result = command_executor.execute_command("invalid_keypress")
        assert result is False

    def test_keypress_with_empty_keys(
        self, command_executor, mock_config, mock_dependencies
    ):
        """Test keypress with empty keys."""
        mock_pyautogui, _ = mock_dependencies
        mock_config.model_actions = {
            "empty_keypress": {"action": "keypress", "keys": []}
        }

        result = command_executor.execute_command("empty_keypress")
        assert result is True
        mock_pyautogui.hotkey.assert_called_once_with()

    def test_keypress_with_none_keys(
        self, command_executor, mock_config, mock_dependencies
    ):
        """Test keypress with None keys."""
        mock_pyautogui, _ = mock_dependencies
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
    def test_common_keypress_keys(
        self, command_executor, mock_config, mock_dependencies, key
    ):
        """Test common keypress keys."""
        mock_pyautogui, _ = mock_dependencies
        mock_config.model_actions = {
            "common_keypress": {"action": "keypress", "keys": key}
        }

        result = command_executor.execute_command("common_keypress")
        assert result is True
        mock_pyautogui.press.assert_called_once_with(key)

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
    def test_common_key_combinations(
        self, command_executor, mock_config, mock_dependencies, key_combo
    ):
        """Test common key combinations."""
        mock_pyautogui, _ = mock_dependencies
        mock_config.model_actions = {
            "combo_keypress": {"action": "keypress", "keys": key_combo}
        }

        result = command_executor.execute_command("combo_keypress")
        assert result is True
        mock_pyautogui.hotkey.assert_called_once_with(*key_combo)
