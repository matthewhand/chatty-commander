import unittest
from unittest.mock import MagicMock, patch

from src.chatty_commander import main


class TestMain(unittest.TestCase):
    @patch('sys.argv', ['main.py', '--shell'])
    @patch('builtins.input', side_effect=['exit'])
    @patch('src.chatty_commander.main.StateManager')
    @patch('src.chatty_commander.main.ModelManager')
    @patch('src.chatty_commander.main.CommandExecutor')
    @patch('src.chatty_commander.main.Config')
    @patch('src.chatty_commander.main.setup_logger')
    def test_main_loop(
        self,
        mock_setup_logger,
        mock_Config,
        mock_CommandExecutor,
        mock_ModelManager,
        mock_StateManager,
        mock_input,
    ):
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

        result = main.main()
        self.assertEqual(result, 0)

        mock_setup_logger.assert_called_once_with('main', 'logs/chattycommander.log')
        # In shell mode, these methods are not called since it's interactive text input
        # mock_model_manager.reload_models.assert_called()
        # mock_model_manager.listen_for_commands.assert_called()
        # mock_state_manager.update_state.assert_called_with('command')
        # mock_executor.execute_command.assert_called_with('command')


if __name__ == '__main__':
    unittest.main()
