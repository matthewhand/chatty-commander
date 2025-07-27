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

def test_cli_config_non_interactive(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['cli.py', 'config', '--model', 'okay_stop', '--action', 'ctrl+shift+;'])
    with patch('cli.ConfigCLI.set_model_action') as mock_set:
        cli_main()
        mock_set.assert_called_with('okay_stop', 'ctrl+shift+;')

def test_cli_help(capsys, monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['cli.py'])
    with pytest.raises(SystemExit):
        cli_main()
    captured = capsys.readouterr()
    assert 'ChattyCommander CLI' in captured.out
    assert 'run' in captured.out
    assert 'config' in captured.out