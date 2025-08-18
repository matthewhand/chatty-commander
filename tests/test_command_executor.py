from unittest.mock import patch

import pytest

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager


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

    def test_validate_command_success(self, setup):
        """Test validate_command with valid command"""
        setup.config.model_actions['valid_cmd'] = {'keypress': 'space'}
        assert setup.validate_command('valid_cmd') is True

    def test_validate_command_missing(self, setup):
        """Test validate_command with missing command"""
        with pytest.raises(ValueError, match="Invalid command"):
            setup.validate_command('missing_cmd')

    def test_report_error(self, setup):
        """Test report_error method"""
        with patch('logging.critical') as mock_log:
            setup.report_error('test_cmd', 'Test error')
            mock_log.assert_called()

        # Test with error reporting utility
        with patch('chatty_commander.utils.logger.report_error') as mock_report:
            setup.report_error('test_cmd', 'Test error')
            mock_report.assert_called()
