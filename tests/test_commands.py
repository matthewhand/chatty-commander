import unittest
from unittest.mock import patch, MagicMock
from command_executor import CommandExecutor

class TestCommandExecution(unittest.TestCase):
    def setUp(self):
        """Setup the CommandExecutor with a mock configuration for testing."""
        self.command_executor = CommandExecutor()

    @patch('command_executor.pyautogui')
    def test_url_command_execution(self, mock_pyautogui):
        """Test executing a URL command that involves GUI actions."""
        # Setup the mock
        mock_pyautogui.click.return_value = None
        mock_pyautogui.moveTo.return_value = None

        # Call the function that should trigger pyautogui actions
        self.command_executor.execute_command('open_url')

        # Assert that the pyautogui methods were called
        mock_pyautogui.click.assert_called_once()
        mock_pyautogui.moveTo.assert_called_once_with(100, 200)

    @patch('command_executor.pyautogui')
    def test_keypress_command_execution(self, mock_pyautogui):
        """Test executing a keypress command that involves GUI actions."""
        # Setup the mock
        mock_pyautogui.press.return_value = None

        # Call the function that should trigger pyautogui actions
        self.command_executor.execute_command('press_key')

        # Assert that the pyautogui method was called
        mock_pyautogui.press.assert_called_once_with('enter')

    @patch('command_executor.pyautogui')
    def test_system_command_execution(self, mock_pyautogui):
        """Test executing a system command that involves GUI actions."""
        # Setup the mock
        mock_pyautogui.hotkey.return_value = None

        # Call the function that should trigger pyautogui actions
        self.command_executor.execute_command('open_run')

        # Assert that the pyautogui method was called
        mock_pyautogui.hotkey.assert_called_once_with('ctrl', 'r')

    def test_invalid_command(self):
        """Test handling of undefined commands."""
        with self.assertRaises(ValueError):
            self.command_executor.execute_command('undefined_command')

if __name__ == '__main__':
    unittest.main()
