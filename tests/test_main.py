import unittest
from unittest.mock import patch, MagicMock
import main  # Assuming main.py can be imported as main

from model_manager import ModelManager
from state_manager import StateManager
from command_executor import CommandExecutor
from config import Config

class TestMain(unittest.TestCase):
    @patch('main.StateManager')
    @patch('main.ModelManager')
    @patch('main.CommandExecutor')
    @patch('main.Config')
    @patch('main.setup_logger')
    def test_main_loop(self, mock_setup_logger, mock_Config, mock_CommandExecutor, mock_ModelManager, mock_StateManager):
        mock_config = MagicMock()
        mock_config.general_models_path = 'path'
        mock_config.system_models_path = 'path'
        mock_config.chat_models_path = 'path'
        mock_config.model_actions = {'command': 'action'}
        mock_Config.return_value = mock_config

        mock_model_manager = MagicMock()
        mock_model_manager.reload_models.return_value = None
        mock_model_manager.listen_for_commands.side_effect = ['command', KeyboardInterrupt]
        mock_ModelManager.return_value = mock_model_manager

        mock_state_manager = MagicMock()
        mock_state_manager.current_state = 'idle'
        mock_state_manager.update_state.return_value = 'new_state'
        mock_StateManager.return_value = mock_state_manager

        mock_executor = MagicMock()
        mock_CommandExecutor.return_value = mock_executor

        with self.assertRaises(SystemExit):
            main.main()

        mock_setup_logger.assert_called_once_with('main', 'logs/chattycommander.log')
        mock_model_manager.reload_models.assert_called()
        mock_model_manager.listen_for_commands.assert_called()
        mock_state_manager.update_state.assert_called_with('command')
        mock_executor.execute_command.assert_called_with('command')

if __name__ == '__main__':
    unittest.main()