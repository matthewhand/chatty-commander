from unittest.mock import patch

import pytest
from config import Config
from model_manager import ModelManager
from state_manager import StateManager

from src.chatty_commander.command_executor import CommandExecutor


class TestCommandExecutor:
    @pytest.fixture
    def setup(self):
        config = Config()
        model_manager = ModelManager(config)
        state_manager = StateManager()
        return CommandExecutor(config, model_manager, state_manager)

    def test_execute_command_keypress(self, setup):
        setup.config.model_actions['test_cmd'] = {'keypress': 'space'}
        with patch.object(setup, '_execute_keybinding') as mock_key:
            setup.execute_command('test_cmd')
            mock_key.assert_called_once()

    def test_execute_command_url(self, setup):
        setup.config.model_actions['test_url'] = {'url': 'http://example.com'}
        with patch.object(setup, '_execute_url') as mock_url:
            setup.execute_command('test_url')
            mock_url.assert_called_once()

    def test_execute_command_invalid(self, setup):
        setup.config.model_actions['invalid'] = {'unknown': 'value'}
        with pytest.raises(TypeError):
            setup.execute_command('invalid')

    def test_execute_command_missing(self, setup):
        with pytest.raises(ValueError):
            setup.execute_command('not_found')
