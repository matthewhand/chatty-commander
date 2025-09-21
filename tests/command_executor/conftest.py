import pytest
from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from unittest.mock import Mock

@pytest.fixture
def setup_executor():
    """Provide a CommandExecutor with minimal configuration."""
    config = Config()
    config.model_actions = {
        "test_cmd": {"keypress": "space"},
        "test_url": {"url": "http://example.com"},
        "test_shell": {"shell": "echo test"},
    }
    model_manager = ModelManager(config)
    state_manager = StateManager()
    return CommandExecutor(config, model_manager, state_manager)

@pytest.fixture
def mock_executor():
    """Provide a CommandExecutor with mocked execution methods."""
    config = Config()
    config.model_actions = {"mock_cmd": {"keypress": "space"}}
    model_manager = ModelManager(config)
    state_manager = StateManager()

    executor = CommandExecutor(config, model_manager, state_manager)
    executor._execute_keybinding = Mock(return_value=True)
    executor._execute_url = Mock(return_value=True)
    executor._execute_shell = Mock(return_value=True)
    return executor
