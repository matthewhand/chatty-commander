import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from unittest.mock import patch, MagicMock
import logging
from command_executor import CommandExecutor
from config import Config
from model_manager import ModelManager
from state_manager import StateManager

class TestCommandExecution(unittest.TestCase):
    def setUp(self):
        """Setup the CommandExecutor with a mock configuration for testing."""
        self.config = Config()
        self.config.model_actions = {
            'lights_on': {'url': 'http://homeassistant.domain.home:8123/api/lights_on'},
            'okay_stop': {'keypress': ['ctrl', 'shift', ';']},
            'single_key': {'keypress': 'a'},
            'test_key': {'keypress': 'ctrl+alt+t'}
        }
        self.model_manager = ModelManager(self.config)
        self.state_manager = StateManager()
        self.command_executor = CommandExecutor(self.config, self.model_manager, self.state_manager)
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)

    @patch('command_executor.requests')
    def test_url_command_execution(self, mock_requests):
        """Test executing a URL command."""
        mock_requests.get.return_value = MagicMock(status_code=200)
        self.command_executor.execute_command('lights_on')
        mock_requests.get.assert_called_once_with('http://homeassistant.domain.home:8123/api/lights_on')
        self.logger.debug("URL command 'lights_on' executed with status 200")

    @patch('command_executor.pyautogui')
    def test_keypress_command_execution(self, mock_pyautogui):
        """Test executing a keypress command."""
        self.command_executor.execute_command('okay_stop')
        mock_pyautogui.hotkey.assert_called_once_with('ctrl', 'shift', ';')
        self.logger.debug("Keypress command 'okay_stop' executed")

    def test_invalid_command(self):
        """Test handling of undefined commands."""
        with self.assertRaises(ValueError):
            self.command_executor.execute_command('undefined_command')
        self.logger.debug("Invalid command raised ValueError as expected")

    # Expanded tests
    @patch('command_executor.requests')
    def test_url_command_failure(self, mock_requests):
        """Test URL command with failure."""
        mock_requests.get.side_effect = Exception("Network error")
        self.command_executor._execute_url('lights_on', 'http://homeassistant.domain.home:8123/api/lights_on')
        self.logger.debug("URL command failure handled")

    @patch('command_executor.pyautogui')
    def test_keypress_single_key(self, mock_pyautogui):
        """Test single key press."""
        self.command_executor.execute_command('single_key')
        mock_pyautogui.press.assert_called_once_with('a')
        self.logger.debug("Single keypress executed")

    @patch('command_executor.pyautogui', None)
    def test_missing_pyautogui(self):
        """Test behavior when pyautogui is not available."""
        with patch('command_executor.pyautogui', None):
            self.command_executor.execute_command('test_key')
        self.logger.debug("Handled missing pyautogui")

    def test_pre_post_hooks(self):
        """Test pre and post execute hooks."""
        with patch.object(self.command_executor, 'pre_execute_hook') as mock_pre, \
             patch.object(self.command_executor, 'post_execute_hook') as mock_post, \
             patch('command_executor.requests') as mock_requests:
            mock_requests.get.return_value = MagicMock(status_code=200)
            self.command_executor.execute_command('lights_on')
            mock_pre.assert_called_once_with('lights_on')
            mock_post.assert_called_once_with('lights_on')
            self.logger.debug("Pre and post hooks called")

    def test_error_reporting(self):
        """Test error reporting mechanism."""
        with patch('command_executor.logging') as mock_log:
            self.command_executor.report_error('test_cmd', "Test error")
            mock_log.critical.assert_called_once_with("Error in test_cmd: Test error")
        self.logger.debug("Error reported")

    @patch('command_executor.pyautogui')
    def test_multiple_commands(self, mock_pyautogui):
        """Test executing multiple different commands."""
        with patch('command_executor.requests') as mock_requests:
            mock_requests.get.return_value = MagicMock(status_code=200)
            self.command_executor.execute_command('lights_on')
            self.command_executor.execute_command('okay_stop')
            mock_requests.get.assert_called_once()
            mock_pyautogui.hotkey.assert_called_once()
            self.logger.debug("Multiple commands executed")

if __name__ == '__main__':
    unittest.main()
