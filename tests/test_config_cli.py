import json
import os
import sys
from unittest.mock import mock_open, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from chatty_commander.config_cli import (
    ConfigCLI,  # Assuming the class or main function in config_cli.py
)


@pytest.fixture
def mock_config_file():
    config_data = {"model_actions": {}, "state_models": {}, "listen_for": {}, "modes": {}}
    with patch("builtins.open", mock_open(read_data=json.dumps(config_data))) as mock_file:
        yield mock_file


def test_set_model_action_non_interactive(mock_config_file):
    cli = ConfigCLI()
    cli.set_model_action('okay_stop', 'ctrl+shift+;')
    mock_file = mock_config_file()
    full_content = ''.join(call[0][0] for call in mock_file.write.call_args_list)
    written_data = json.loads(full_content)
    assert written_data['model_actions']['okay_stop'] == 'ctrl+shift+;'


def test_set_state_model(mock_config_file):
    cli = ConfigCLI()
    cli.set_state_model('idle', 'model1,model2')
    mock_file = mock_config_file()
    full_content = ''.join(call[0][0] for call in mock_file.write.call_args_list)
    written_data = json.loads(full_content)
    assert written_data['state_models']['idle'] == ['model1', 'model2']


def test_set_listen_for(mock_config_file):
    cli = ConfigCLI()
    cli.set_listen_for('param1', 'value1')
    mock_file = mock_config_file()
    full_content = ''.join(call[0][0] for call in mock_file.write.call_args_list)
    written_data = json.loads(full_content)
    assert written_data['listen_for']['param1'] == 'value1'


def test_set_mode(mock_config_file):
    cli = ConfigCLI()
    cli.set_mode('mode1', 'option1')
    mock_file = mock_config_file()
    full_content = ''.join(call[0][0] for call in mock_file.write.call_args_list)
    written_data = json.loads(full_content)
    assert written_data['modes']['mode1'] == 'option1'


def test_list_config(capsys, mock_config_file):
    cli = ConfigCLI()
    cli.list_config()
    captured = capsys.readouterr()
    assert 'Current Configuration:' in captured.out


def test_load_config_error(monkeypatch, capsys):
    monkeypatch.setattr('builtins.open', mock_open(read_data='invalid json'))
    monkeypatch.setattr('os.path.exists', lambda p: True)
    cli = ConfigCLI()
    captured = capsys.readouterr()
    assert 'Error: Invalid JSON' in captured.err
    assert cli.config.model_actions == {}
    assert cli.config.state_models == {}
    # No need to call load_config again as it's called in __init__


def test_interactive_mode(monkeypatch, mock_config_file):
    inputs = iter(
        [
            'model_action',
            'test_model',
            'test_action',
            'y',
            'state_model',
            'test_state',
            'model1,model2',
            'n',
        ]
    )
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    cli = ConfigCLI()
    cli.interactive_mode()
    assert 'test_model' in cli.config.model_actions
    assert cli.config.model_actions['test_model'] == 'test_action'
    assert 'test_state' in cli.config.state_models
    assert cli.config.state_models['test_state'] == ['model1', 'model2']
