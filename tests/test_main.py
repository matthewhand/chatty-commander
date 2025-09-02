# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import unittest
from unittest.mock import MagicMock, patch

from chatty_commander import main


class TestMain(unittest.TestCase):
    @patch("sys.argv", ["main.py", "--shell"])
    @patch("builtins.input", side_effect=["exit"])
    @patch("chatty_commander.main.StateManager")
    @patch("chatty_commander.main.ModelManager")
    @patch("chatty_commander.main.CommandExecutor")
    @patch("chatty_commander.main.Config")
    @patch("chatty_commander.main.setup_logger")
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
        mock_config.general_models_path = "path"
        mock_config.system_models_path = "path"
        mock_config.chat_models_path = "path"
        mock_config.model_actions = {"command": "action"}
        mock_Config.return_value = mock_config

        mock_model_manager = MagicMock()
        mock_model_manager.reload_models.return_value = None
        mock_model_manager.listen_for_commands.side_effect = [
            "command",
            KeyboardInterrupt,
        ]
        mock_ModelManager.return_value = mock_model_manager

        mock_state_manager = MagicMock()
        mock_state_manager.current_state = "idle"
        mock_state_manager.update_state.return_value = "new_state"
        mock_StateManager.return_value = mock_state_manager

        mock_executor = MagicMock()
        mock_CommandExecutor.return_value = mock_executor

        result = main.main()
        self.assertEqual(result, 0)

        mock_setup_logger.assert_called_once_with("main", "logs/chattycommander.log")
        # In shell mode, these methods are not called since it's interactive text input
        # mock_model_manager.reload_models.assert_called()
        # mock_model_manager.listen_for_commands.assert_called()
        # mock_state_manager.update_state.assert_called_with('command')
        # mock_executor.execute_command.assert_called_with('command')

    @patch(
        "sys.argv",
        ["main.py", "--web", "--host", "1.2.3.4", "--port", "1234", "--no-auth"],
    )
    @patch("chatty_commander.main.run_web_mode")
    @patch("chatty_commander.main.StateManager")
    @patch("chatty_commander.main.ModelManager")
    @patch("chatty_commander.main.CommandExecutor")
    @patch("chatty_commander.main.Config")
    @patch("chatty_commander.main.setup_logger")
    def test_web_mode_cli_overrides(
        self,
        mock_setup_logger,
        mock_Config,
        mock_CommandExecutor,
        mock_ModelManager,
        mock_StateManager,
        mock_run_web_mode,
    ):
        mock_config = MagicMock()
        mock_config.web_server = {"host": "0.0.0.0", "port": 8100, "auth_enabled": True}
        mock_Config.return_value = mock_config

        result = main.main()
        self.assertEqual(result, 0)

        mock_run_web_mode.assert_called_once()
        _args, kwargs = mock_run_web_mode.call_args
        self.assertEqual(kwargs["host"], "1.2.3.4")
        self.assertEqual(kwargs["port"], 1234)
        self.assertTrue(kwargs["no_auth"])
        self.assertEqual(
            mock_config.web_server,
            {"host": "1.2.3.4", "port": 1234, "auth_enabled": False},
        )


if __name__ == "__main__":
    unittest.main()
