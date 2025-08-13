import sys
from unittest.mock import patch

from src.chatty_commander import main


def test_main_config_wizard(monkeypatch):
    """Ensure that invoking main with --config triggers ConfigCLI.run_wizard."""
    monkeypatch.setattr(sys, 'argv', ['main.py', '--config'])
    with (
        patch('config_cli.ConfigCLI.__init__', return_value=None),
        patch('config_cli.ConfigCLI.run_wizard') as mock_wizard,
        patch('src.chatty_commander.main.Config'),
        patch('src.chatty_commander.main.ModelManager'),
        patch('src.chatty_commander.main.StateManager'),
        patch('src.chatty_commander.main.CommandExecutor'),
        patch('src.chatty_commander.main.setup_logger'),
        patch('src.chatty_commander.main.generate_default_config_if_needed', return_value=False),
    ):
        result = main.main()
        assert result == 0
        mock_wizard.assert_called_once()
