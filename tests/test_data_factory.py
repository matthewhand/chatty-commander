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
Test Data Factory - Consistent test data generation for ChattyCommander tests
"""

from typing import Any
from unittest.mock import Mock

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager


class TestDataFactory:
    """Factory for creating consistent test data across all tests."""

    @staticmethod
    def create_valid_config_data() -> dict[str, Any]:
        """Create valid configuration data for testing."""
        return {
            "default_state": "idle",
            "general_models_path": "models-idle",
            "system_models_path": "models-computer",
            "chat_models_path": "models-chatty",
            "state_models": {
                "idle": ["model1", "model2"],
                "computer": ["model3"],
                "chatty": ["model4"],
            },
            "model_actions": {
                "test_cmd": {"action": "shell", "cmd": "echo test"},
                "keypress_cmd": {"action": "keypress", "keys": "space"},
                "url_cmd": {"action": "url", "url": "http://example.com"},
                "msg_cmd": {"action": "custom_message", "message": "Hello"},
            },
            "wakeword_state_map": {
                "hey": "computer",
                "stop": "idle",
                "hello": "chatty",
            },
            "state_transitions": {
                "idle": {"start": "computer", "chat": "chatty"},
                "computer": {"stop": "idle"},
                "chatty": {"end": "idle"},
            },
            "commands": {
                "hello": {"action": "custom_message", "message": "Hi!"},
                "screenshot": {"action": "keypress", "keys": "f12"},
            },
            "advisors": {
                "enabled": False,
                "llm_api_mode": "completion",
                "model": "gpt-4",
            },
            "voice_only": False,
            "web_server": {"host": "0.0.0.0", "port": 8000, "auth_enabled": False},
        }

    @staticmethod
    def createmock_config(config_data: dict[str, Any] | None = None) -> Mock:
        """Create a properly configured mock Config object."""
        config = Mock(spec=Config)
        data = config_data or TestDataFactory.create_valid_config_data()
        config.config_data = data
        config.config = data
        config.default_state = data.get("default_state", "idle")
        config.save_config = Mock()
        config.reload_config = Mock(return_value=True)
        return config

    @staticmethod
    def create_mock_state_manager(config: Mock | None = None) -> Mock:
        """Create a properly configured mock StateManager."""
        sm = Mock(spec=StateManager)
        sm.current_state = "idle"
        sm.config = config or TestDataFactory.createmock_config()
        sm.change_state = Mock(return_value=True)
        sm.process_command = Mock(return_value=True)
        sm.get_active_models = Mock(return_value=["model1", "model2"])
        sm.add_state_change_callback = Mock()
        return sm

    @staticmethod
    def create_mock_model_manager() -> Mock:
        """Create a properly configured mock ModelManager."""
        mm = Mock(spec=ModelManager)
        mm.get_models = Mock(return_value=["model1", "model2", "model3"])
        mm.reload_models = Mock(return_value=True)
        return mm

    @staticmethod
    def create_mockcommand_executor(config: Mock | None = None) -> Mock:
        """Create a properly configured mock CommandExecutor."""
        ce = Mock(spec=CommandExecutor)
        ce.validate_command = Mock(return_value=True)
        ce.execute_command = Mock(return_value=True)
        ce.config = config or TestDataFactory.createmock_config()
        ce.last_command = None
        ce.pre_execute_hook = Mock()
        return ce
