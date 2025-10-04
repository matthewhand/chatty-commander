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

from unittest.mock import Mock

import pytest
from test_assertions import TestAssertions
from test_data_factories import TestDataFactory

from chatty_commander.app.command_executor import CommandExecutor


class TestCommandExecutor:
    """
    Comprehensive tests for the CommandExecutor module.
    """

    @pytest.fixture
    def mock_config(self):
        """Provide a properly configured mock Config object."""
        return TestDataFactory.create_mock_config()

    @pytest.fixture
    def mock_command_executor(self, mock_config) -> Mock:
        """Provide a properly configured mock CommandExecutor."""
        return TestDataFactory.create_mock_command_executor(mock_config)

    @pytest.mark.parametrize(
        "command_name,expected",
        [
            ("test_cmd", True),
            ("keypress_cmd", True),
            ("url_cmd", True),
            ("msg_cmd", True),
            ("invalid_cmd", False),
        ],
    )
    def test_command_executor_validation(self, command_name, expected):
        """Test CommandExecutor validation for various commands."""
        mock_model_manager = Mock()
        mock_state_manager = Mock()
        ce = CommandExecutor(
            TestDataFactory.create_mock_config(), mock_model_manager, mock_state_manager
        )
        result = ce.validate_command(command_name)
        assert result is expected

    @pytest.mark.parametrize(
        "action_config",
        [
            {"action": "shell", "cmd": "echo test"},
            {"action": "keypress", "keys": "space"},
            {"action": "url", "url": "http://example.com"},
            {"action": "custom_message", "message": "Hello"},
            {"action": "invalid", "param": "value"},
        ],
    )
    def test_command_executor_action_execution(self, action_config):
        """Test CommandExecutor action execution."""
        config = TestDataFactory.create_mock_config(
            {"model_actions": {"test": action_config}}
        )
        mock_model_manager = Mock()
        mock_state_manager = Mock()
        ce = CommandExecutor(config, mock_model_manager, mock_state_manager)
        ce.execute_command("test")
        # Add assertions based on expected side effects

    @pytest.mark.parametrize(
        "key_config",
        [
            {"action": "keypress", "keys": "space"},
            {"action": "keypress", "keys": "enter"},
            {"action": "keypress", "keys": "ctrl+shift+a"},
        ],
    )
    def test_command_executor_keypress_handling(self, key_config):
        """Test CommandExecutor keypress handling."""
        config = TestDataFactory.create_mock_config(
            {"model_actions": {"keypress": key_config}}
        )
        mock_model_manager = Mock()
        mock_state_manager = Mock()
        ce = CommandExecutor(config, mock_model_manager, mock_state_manager)
        ce.execute_command("keypress")
        # Assuming keypress is mocked; add assertions

    @pytest.mark.parametrize(
        "url",
        [
            "http://example.com",
            "https://secure.example.com",
            "file:///local/path",
        ],
    )
    def test_command_executor_url_handling(self, url):
        """Test CommandExecutor URL handling."""
        config = TestDataFactory.create_mock_config(
            {"model_actions": {"url_cmd": {"action": "url", "url": url}}}
        )
        mock_model_manager = Mock()
        mock_state_manager = Mock()
        ce = CommandExecutor(config, mock_model_manager, mock_state_manager)
        ce.execute_command("url_cmd")
        # Add assertions for URL opening

    @pytest.mark.parametrize(
        "message",
        [
            "Hello World",
            "Test message",
            "",
        ],
    )
    def test_command_executor_message_handling(self, message):
        """Test CommandExecutor message handling."""
        config = TestDataFactory.create_mock_config(
            {
                "model_actions": {
                    "msg_cmd": {"action": "custom_message", "message": message}
                }
            }
        )
        mock_model_manager = Mock()
        mock_state_manager = Mock()
        ce = CommandExecutor(config, mock_model_manager, mock_state_manager)
        ce.execute_command("msg_cmd")
        # Add assertions for message display

    def test_command_executor_pre_execute_hook(self):
        """Test CommandExecutor pre-execute hook."""
        mock_model_manager = Mock()
        mock_state_manager = Mock()
        ce = CommandExecutor(
            TestDataFactory.create_mock_config(), mock_model_manager, mock_state_manager
        )
        ce.pre_execute_hook("test_cmd")
        # Assuming hook is called; add assertions if needed

    @pytest.mark.parametrize(
        "shell_cmd",
        [
            "echo test",
            "ls -la",
            "python script.py",
        ],
    )
    def test_command_executor_shell_command_handling(self, shell_cmd):
        """Test CommandExecutor shell command handling."""
        config = TestDataFactory.create_mock_config(
            {"model_actions": {"shell_cmd": {"action": "shell", "cmd": shell_cmd}}}
        )
        mock_model_manager = Mock()
        mock_state_manager = Mock()
        ce = CommandExecutor(config, mock_model_manager, mock_state_manager)
        ce.execute_command("shell_cmd")
        # Add assertions for shell execution

    def test_command_executor_actions_valid(self):
        """Test CommandExecutor actions validation using assertion helper."""
        mock_model_manager = Mock()
        mock_state_manager = Mock()
        ce = CommandExecutor(
            TestDataFactory.create_mock_config(), mock_model_manager, mock_state_manager
        )
        TestAssertions.assert_command_executor_actions_valid(ce)
