import unittest
import sys
import os
from unittest.mock import patch, MagicMock
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from command_extractor import CommandExecutor
from config import Config

class TestCommandExecutor(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.config.auth_token = 'test_token'
        self.config.screenshot_save_path = 'test/path/to/screenshot.png'
        self.executor = CommandExecutor(self.config)

    @patch('command_extractor.requests.get')
    def test_execute_url(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        self.config.url_commands = {'test_command': 'http://test.url'}
        self.executor.execute_url('test_command')
        mock_get.assert_called_once_with('http://test.url', headers={'Authorization': 'Bearer test_token'})

    @patch('command_extractor.pyautogui.hotkey')
    @patch('command_extractor.pyautogui.press')
    def test_execute_keypress_list(self, mock_press, mock_hotkey):
        self.config.keypress_commands = {'test_command': ['ctrl', 'shift', 'a']}
        self.executor.execute_keypress('test_command')
        mock_hotkey.assert_called_once_with('ctrl', 'shift', 'a')
        mock_press.assert_not_called()

    @patch('command_extractor.pyautogui.hotkey')
    @patch('command_extractor.pyautogui.press')
    def test_execute_keypress_single(self, mock_press, mock_hotkey):
        self.config.keypress_commands = {'test_command': 'enter'}
        self.executor.execute_keypress('test_command')
        mock_press.assert_called_once_with('enter')
        mock_hotkey.assert_not_called()

    @patch('command_extractor.pyautogui.screenshot')
    @patch('command_extractor.subprocess.run')
    @patch('command_extractor.pyautogui.hotkey')
    @patch('command_extractor.pyautogui.press')
    def test_execute_system_command(self, mock_press, mock_hotkey, mock_run, mock_screenshot):
        mock_save = MagicMock()
        mock_screenshot.return_value = MagicMock(save=mock_save)
        self.config.system_commands = ['take_screenshot', 'start_run', 'cycle_window', 'send_newline', 'wax_poetic']
        self.executor.execute_system_command('take_screenshot')
        mock_screenshot.assert_called_once()
        mock_save.assert_called_once_with(self.config.screenshot_save_path)

        self.executor.execute_system_command('start_run')
        mock_run.assert_called_once_with(['start', 'run'], shell=True)

        self.executor.execute_system_command('cycle_window')
        mock_hotkey.assert_called_once_with('alt', 'tab')

        self.executor.execute_system_command('send_newline')
        mock_press.assert_called_once_with('enter')

        self.executor.execute_system_command('wax_poetic')
        # Just logs, no assertion needed beyond execution

    def test_execute_command(self):
        with patch.object(self.executor, 'execute_url') as mock_url, \
             patch.object(self.executor, 'execute_keypress') as mock_key, \
             patch.object(self.executor, 'execute_system_command') as mock_sys:
            self.config.url_commands = {'url_cmd': 'url'}
            self.executor.execute_command('url_cmd', 'model')
            mock_url.assert_called_once_with('url_cmd')

            self.config.keypress_commands = {'key_cmd': 'key'}
            self.executor.execute_command('key_cmd', 'model')
            mock_key.assert_called_once_with('key_cmd')

            self.config.system_commands = ['sys_cmd']
            self.executor.execute_command('sys_cmd', 'model')
            mock_sys.assert_called_once_with('sys_cmd')

if __name__ == '__main__':
    unittest.main()