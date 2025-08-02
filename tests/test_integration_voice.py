from unittest.mock import patch

import pytest

from config import Config
from model_manager import ModelManager
from state_manager import StateManager


@pytest.fixture
def config():
    return Config()


@pytest.fixture
def state_manager():
    return StateManager()


@pytest.fixture
def model_manager(config):
    return ModelManager(config)


def test_voice_recognition_integration_idle(state_manager, model_manager):
    """Test integration in idle state."""
    state_manager.change_state('idle')
    model_manager.reload_models('idle')
    assert len(model_manager.active_models) > 0
    with (
        patch('model_manager.random.random', return_value=0.01),
        patch('model_manager.random.choice', return_value='hey_chat_tee'),
        patch('time.sleep'),
    ):
        detected = model_manager.listen_for_commands()
        assert detected == 'hey_chat_tee'
        new_state = state_manager.update_state(detected)
        assert new_state == 'chatty'


def test_voice_recognition_integration_chatty(state_manager, model_manager):
    """Test integration in chatty state."""
    state_manager.change_state('chatty')
    model_manager.reload_models('chatty')
    assert len(model_manager.active_models) > 0
    with (
        patch('model_manager.random.random', return_value=0.01),
        patch('model_manager.random.choice', return_value='okay_stop'),
        patch('time.sleep'),
    ):
        detected = model_manager.listen_for_commands()
        assert detected == 'okay_stop'
        new_state = state_manager.update_state(detected)
        assert new_state == 'idle'


def test_no_detection_integration(state_manager, model_manager):
    """Test no detection case."""
    state_manager.change_state('computer')
    model_manager.reload_models('computer')
    with patch('model_manager.random.random', return_value=0.1), patch('time.sleep'):
        detected = model_manager.listen_for_commands()
        assert detected is None
        new_state = state_manager.update_state('invalid')
        assert new_state is None
        assert state_manager.current_state == 'computer'
