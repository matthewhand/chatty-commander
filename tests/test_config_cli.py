import pytest
import json
from unittest.mock import patch, mock_open
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config_cli import ConfigCLI  # Assuming the class or main function in config_cli.py

@pytest.fixture
def mock_config_file():
    config_data = {
        "model_actions": {},
        "state_models": {}
    }
    with patch("builtins.open", mock_open(read_data=json.dumps(config_data))) as mock_file:
        yield mock_file

def test_set_model_action_non_interactive(mock_config_file):
    cli = ConfigCLI()
    cli.set_model_action('okay_stop', 'ctrl+shift+;')
    mock_file = mock_config_file()
    full_content = ''.join(call[0][0] for call in mock_file.write.call_args_list)
    written_data = json.loads(full_content)
    assert written_data['model_actions']['okay_stop'] == 'ctrl+shift+;'

def test_interactive_mode(monkeypatch, mock_config_file):
    inputs = iter(['model_action', 'hey_chat_tee', 'ctrl+alt+t', 'n'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    cli = ConfigCLI()
    cli.interactive_mode()
    mock_file = mock_config_file()
    full_content = ''.join(call[0][0] for call in mock_file.write.call_args_list)
    written_data = json.loads(full_content)
    assert 'hey_chat_tee' in written_data['model_actions']