import logging
from unittest.mock import MagicMock, patch

import pytest
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.app.command_executor import CommandExecutor


@pytest.fixture
def config():
    """Setup the CommandExecutor with a mock configuration for testing."""
    config = Config()
    config.model_actions = {
        'lights_on': {'url': 'http://homeassistant.domain.home:8123/api/lights_on'},
        'okay_stop': {'keypress': ['ctrl', 'shift', ';']},
        'single_key': {'keypress': 'a'},
        'test_key': {'keypress': 'ctrl+alt+t'},
        'invalid_type_cmd': {'invalid': 'action'},
    }
    return config


@pytest.fixture
def model_manager(config):
    return ModelManager(config)


@pytest.fixture
def state_manager():
    return StateManager()


@pytest.fixture
def command_executor(config, model_manager, state_manager):
    return CommandExecutor(config, model_manager, state_manager)


class TestCommandExecution:
    @patch('chatty_commander.app.command_executor.requests')
    def test_url_command_execution(self, mock_requests, command_executor):
        """Test executing a URL command."""
        mock_requests.get.return_value = MagicMock(status_code=200)
        command_executor.execute_command('lights_on')
        mock_requests.get.assert_called_once_with(
            'http://homeassistant.domain.home:8123/api/lights_on'
        )
        logging.debug("URL command 'lights_on' executed with status 200")

    @patch('chatty_commander.app.command_executor.pyautogui', create=True)
    def test_keypress_command_execution(self, mock_pyautogui, command_executor):
        """Test executing a keypress command."""
        command_executor.execute_command('okay_stop')
        mock_pyautogui.hotkey.assert_called_once_with('ctrl', 'shift', ';')
        logging.debug("Keypress command 'okay_stop' executed")

    def test_invalid_command(self, command_executor):
        """Test handling of undefined commands."""
        with pytest.raises(ValueError):
            command_executor.execute_command('undefined_command')
        logging.debug("Invalid command raised ValueError as expected")

    @patch('chatty_commander.app.command_executor.requests')
    def test_url_command_failure(self, mock_requests, command_executor):
        """Test URL command with failure."""
        mock_requests.get.side_effect = Exception("Network error")
        command_executor._execute_url(
            'lights_on', 'http://homeassistant.domain.home:8123/api/lights_on'
        )
        logging.debug("URL command failure handled")

    @patch('chatty_commander.app.command_executor.pyautogui', create=True)
    def test_keypress_single_key(self, mock_pyautogui, command_executor):
        """Test single key press."""
        command_executor.execute_command('single_key')
        mock_pyautogui.press.assert_called_once_with('a')
        logging.debug("Single keypress executed")

    def test_missing_pyautogui(self, command_executor):
        """Test behavior when pyautogui is not available."""
        with patch('chatty_commander.app.command_executor.pyautogui', None), patch('logging.critical') as mock_log:
            command_executor.execute_command('test_key')
            mock_log.assert_called_once_with("Error in test_key: pyautogui not available")
        logging.debug("Handled missing pyautogui")

    def test_pre_post_hooks(self, command_executor):
        """Test pre and post execute hooks."""
        with (
            patch.object(command_executor, 'pre_execute_hook') as mock_pre,
            patch.object(command_executor, 'post_execute_hook') as mock_post,
            patch('chatty_commander.app.command_executor.requests') as mock_requests,
        ):
            mock_requests.get.return_value = MagicMock(status_code=200)
            command_executor.execute_command('lights_on')
            mock_pre.assert_called_once_with('lights_on')
            mock_post.assert_called_once_with('lights_on')
        logging.debug("Pre and post hooks called")

    def test_error_reporting(self, command_executor):
        """Test error reporting mechanism."""
        with patch('logging.critical') as mock_log:
            command_executor.report_error('test_cmd', "Test error")
            mock_log.assert_called_once_with("Error in test_cmd: Test error")
        logging.debug("Error reported")

    @patch('chatty_commander.app.command_executor.pyautogui', create=True)
    @patch('chatty_commander.app.command_executor.requests')
    def test_multiple_commands(self, mock_requests, mock_pyautogui, command_executor):
        """Test executing multiple different commands."""
        mock_requests.get.return_value = MagicMock(status_code=200)
        command_executor.execute_command('lights_on')
        command_executor.execute_command('okay_stop')
        mock_requests.get.assert_called_once()
        mock_pyautogui.hotkey.assert_called_once()
        logging.debug("Multiple commands executed")
        logging.debug("Multiple commands executed")

    def test_invalid_command_type(self, command_executor):
        """Test that a command with an invalid type raises a TypeError."""
        with pytest.raises(TypeError):
            command_executor.execute_command('invalid_type_cmd')
        logging.debug("Invalid command type raised TypeError as expected")
