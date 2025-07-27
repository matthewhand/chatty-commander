import pytest
from unittest.mock import patch, call
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli import main  # Assuming cli.py will have a main function for CLI

def test_chatty_run(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['chatty', 'run'])
    with patch('cli.run_application') as mock_run:
        main()
        mock_run.assert_called_once()

def test_chatty_config_interactive(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['chatty', 'config'])
    with patch('cli.ConfigCLI.interactive_mode') as mock_interactive:
        main()
        mock_interactive.assert_called_once()

def test_chatty_config_non_interactive(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['chatty', 'config', '--model-action', 'okay_stop', 'ctrl+shift+;'])
    with patch('cli.ConfigCLI.set_model_action') as mock_set:
        main()
        mock_set.assert_called_with('okay_stop', 'ctrl+shift+;')