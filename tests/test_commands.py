import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from unittest.mock import patch, MagicMock
from command_executor import CommandExecutor
from config import Config
from model_manager import ModelManager
from state_manager import StateManager

class TestCommandExecution(unittest.TestCase):
    def setUp(self):
        """Setup the CommandExecutor with a mock configuration for testing."""
        self.config = Config()
        self.model_manager = ModelManager(self.config)
        self.state_manager = StateManager()
        self.command_executor = CommandExecutor(self.config, self.model_manager, self.state_manager)

    @patch('command_executor.requests')
    def test_url_command_execution(self, mock_requests):
        """Test executing a URL command."""
        mock_requests.get.return_value = MagicMock(status_code=200)
        self.command_executor.execute_command('lights_on')
        mock_requests.get.assert_called_once_with('http://homeassistant.domain.home:8123/api/lights_on')

    @patch('command_executor.pyautogui')
    def test_keypress_command_execution(self, mock_pyautogui):
        """Test executing a keypress command."""
        mock_pyautogui.hotkey.return_value = None
        self.command_executor.execute_command('okay_stop')
        mock_pyautogui.hotkey.assert_called_once_with('ctrl', 'shift', ';')

    def test_invalid_command(self):
        """Test handling of undefined commands."""
        with self.assertRaises(ValueError):
            self.command_executor.execute_command('undefined_command')

if __name__ == '__main__':
    unittest.main()
