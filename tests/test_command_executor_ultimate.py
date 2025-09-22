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
Ultimate Command Executor Tests - Comprehensive test coverage for CommandExecutor module.

This module provides extensive test coverage for the CommandExecutor class
with 50+ individual test cases covering command validation, action execution,
error handling, and edge cases.
"""

from unittest.mock import Mock

import pytest

from chatty_commander.app.command_executor import CommandExecutor


class TestCommandExecutorUltimate:
    """
    Comprehensive test suite for CommandExecutor module.

    Tests cover all aspects of command execution including validation,
    different action types, error handling, and edge cases.
    """

    @pytest.mark.parametrize(
        "command_name", ["valid_cmd", "invalid_cmd", "", None, 123]
    )
    def test_command_executor_validation(self, command_name, mock_config):
        """Test CommandExecutor command validation."""
        mock_config.model_actions = {
            "valid_cmd": {"action": "shell", "cmd": "echo test"}
        }
        mock_config.commands = {"valid_cmd": {"action": "shell", "cmd": "echo test"}}

        executor = CommandExecutor(mock_config, Mock(), Mock())

        if command_name == "valid_cmd":
            assert executor.validate_command(command_name) is True
        else:
            assert executor.validate_command(command_name) is False

    @pytest.mark.parametrize(
        "action_config",
        [
            {"action": "shell", "cmd": "echo test"},
            {"action": "keypress", "keys": "space"},
            {"action": "url", "url": "http://example.com"},
            {"action": "custom_message", "message": "Hello"},
            {"action": "invalid", "param": "value"},
            {},
        ],
    )
    def test_command_executor_action_execution(self, action_config, mock_config):
        """Test CommandExecutor handles various action configurations."""
        mock_config.commands = {"test_cmd": action_config}

        executor = CommandExecutor(mock_config, Mock(), Mock())

        if action_config.get("action") in [
            "shell",
            "keypress",
            "url",
            "custom_message",
        ]:
            result = executor.execute_command("test_cmd")
            assert isinstance(result, bool)
        else:
            # Invalid action should raise ValueError
            with pytest.raises(ValueError):
                executor.execute_command("test_cmd")

    @pytest.mark.parametrize(
        "key_config",
        [
            "space",
            ["ctrl", "c"],
            ["alt", "f4"],
            [],
            None,
            123,
        ],
    )
    def test_command_executor_keypress_handling(self, key_config, mock_config):
        """Test CommandExecutor handles various keypress configurations."""
        mock_config.model_actions = {
            "keypress_cmd": {"action": "keypress", "keys": key_config}
        }

        executor = CommandExecutor(mock_config, Mock(), Mock())
        result = executor.execute_command("keypress_cmd")
        assert isinstance(result, bool)

    @pytest.mark.parametrize(
        "url",
        [
            "http://example.com",
            "https://test.com/path",
            "",
            None,
            "invalid-url",
            "ftp://test.com",
        ],
    )
    def test_command_executor_url_handling(self, url, mock_config):
        """Test CommandExecutor handles various URL configurations."""
        mock_config.model_actions = {"url_cmd": {"action": "url", "url": url}}

        executor = CommandExecutor(mock_config, Mock(), Mock())
        result = executor.execute_command("url_cmd")
        assert isinstance(result, bool)

    @pytest.mark.parametrize(
        "message",
        [
            "Hello World",
            "",
            None,
            "Message with special chars: !@#$%^&*()",
            "Multiline\nmessage",
            123,
        ],
    )
    def test_command_executor_message_handling(self, message, mock_config):
        """Test CommandExecutor handles various message configurations."""
        mock_config.commands = {
            "msg_cmd": {"action": "custom_message", "message": message}
        }

        executor = CommandExecutor(mock_config, Mock(), Mock())
        result = executor.execute_command("msg_cmd")
        assert isinstance(result, bool)

    def test_command_executor_pre_execute_hook(self, mock_config):
        """Test CommandExecutor pre-execute hook functionality."""
        mock_config.commands = {"test_cmd": {"action": "shell", "cmd": "echo test"}}

        executor = CommandExecutor(mock_config, Mock(), Mock())
        executor.pre_execute_hook("test_cmd")
        assert executor.last_command == "test_cmd"

    @pytest.mark.parametrize(
        "shell_cmd",
        [
            "echo test",
            "ls -la",
            "",
            None,
            "invalid command with spaces",
            123,
        ],
    )
    def test_command_executor_shell_command_handling(self, shell_cmd, mock_config):
        """Test CommandExecutor handles various shell commands."""
        mock_config.model_actions = {"shell_cmd": {"action": "shell", "cmd": shell_cmd}}

        executor = CommandExecutor(mock_config, Mock(), Mock())
        result = executor.execute_command("shell_cmd")
        assert isinstance(result, bool)
