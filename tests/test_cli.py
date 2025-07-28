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

def test_cli_set_state_model(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'config', '--set-state-model', 'idle', 'model1,model2'])
    with patch('cli.ConfigCLI.set_state_model') as mock_set:
        cli_main()
        mock_set.assert_called_with('idle', 'model1,model2')

def test_cli_set_listen_for(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'config', '--set-listen-for', 'param1', 'value1'])
    with patch('cli.ConfigCLI.set_listen_for') as mock_set:
        cli_main()
        mock_set.assert_called_with('param1', 'value1')

def test_cli_set_mode(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'config', '--set-mode', 'mode1', 'option1'])
    with patch('cli.ConfigCLI.set_mode') as mock_set:
        cli_main()
        mock_set.assert_called_with('mode1', 'option1')

def test_cli_help(capsys, monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['cli.py'])
    with pytest.raises(SystemExit):
        cli_main()
    captured = capsys.readouterr()
    assert 'ChattyCommander CLI' in captured.out
    assert 'run' in captured.out
    assert 'config' in captured.out