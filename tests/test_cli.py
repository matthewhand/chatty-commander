import types
import sys
# Patch sys.modules to mock openwakeword and openwakeword.model for test imports
sys.modules['openwakeword'] = types.ModuleType('openwakeword')
mock_model_mod = types.ModuleType('openwakeword.model')
setattr(mock_model_mod, 'Model', type('Model', (), {}))
sys.modules['openwakeword.model'] = mock_model_mod
import pytest
from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli import cli_main

import cli  # For patching internal functions

def test_cli_run(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'run'])
    with patch('cli.run_app') as mock_run:
        cli_main()
        mock_run.assert_called_once()

def test_cli_config_interactive(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'config', '--interactive'])
    with patch('cli.ConfigCLI.interactive_mode') as mock_interactive:
        cli_main()
        mock_interactive.assert_called_once()

def test_cli_config_list(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'config', '--list'])
    with patch('cli.ConfigCLI.list_config') as mock_list:
        cli_main()
        mock_list.assert_called_once()

def test_cli_set_state_model(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'config', '--set-state-model', 'idle', 'model1,model2'])
    with patch('cli.ConfigCLI.set_state_model'):
        with pytest.raises(SystemExit):
            cli_main()
    captured = capsys.readouterr()
    assert "Invalid model(s) for --set-state-model" in captured.err

def test_cli_set_listen_for(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'config', '--set-listen-for', 'param1', 'value1'])
    with patch('cli.ConfigCLI.set_listen_for') as mock_set:
        cli_main()
        mock_set.assert_called_with('param1', 'value1')

def test_cli_set_mode(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'config', '--set-mode', 'mode1', 'option1'])
    with patch('cli.ConfigCLI.set_mode'):
        with pytest.raises(SystemExit):
            cli_main()
    captured = capsys.readouterr()
    assert "Invalid mode" in captured.err

def test_cli_help(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['cli.py'])
    # Patch input to immediately exit the shell
    monkeypatch.setattr('builtins.input', lambda _: 'exit')
    with pytest.raises(SystemExit):
        cli_main()
    captured = capsys.readouterr()
    assert 'ChattyCommander Interactive Shell' in captured.out
    assert 'exit' in captured.out or 'Exiting shell.' in captured.out
def test_cli_config_wizard(monkeypatch):
    # Simulate: chatty-commander config wizard
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'config', 'wizard'])
    with patch('cli.ConfigCLI.run_wizard') as mock_wizard:
        cli_main()
        mock_wizard.assert_called_once()

def test_cli_interactive_shell_exit(monkeypatch):
    # Simulate running with no arguments, then typing 'exit'
    monkeypatch.setattr(sys, 'argv', ['cli.py'])
    inputs = iter(['exit'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    # Patch parser.print_help to avoid printing
    with patch('cli.HelpfulArgumentParser.print_help'):
        with pytest.raises(SystemExit):
            cli_main()

def test_cli_argument_validation_invalid_model(monkeypatch, capsys):
    # --set-model-action with invalid model
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'config', '--set-model-action', 'invalid_model', 'summarize'])
    with patch('cli.ConfigCLI.set_model_action'):
        with pytest.raises(SystemExit):
            cli_main()
    captured = capsys.readouterr()
    assert "Invalid model name" in captured.err

def test_cli_system_update_check(monkeypatch):
    # Simulate: chatty-commander system updates check
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'system', 'updates', 'check'])
    with patch('config.Config.perform_update_check', return_value={"updates_available": False, "update_count": 0}):
        with patch('builtins.print') as mock_print:
            cli_main()
            mock_print.assert_any_call("No updates available.")

def test_cli_system_start_on_boot_enable(monkeypatch):
    # Simulate: chatty-commander system start-on-boot enable
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'system', 'start-on-boot', 'enable'])
    with patch('config.Config.set_start_on_boot') as mock_set:
        with patch('builtins.print') as mock_print:
            cli_main()
            mock_set.assert_called_with(True)
            mock_print.assert_any_call("Start on boot enabled successfully.")