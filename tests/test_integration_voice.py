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

from unittest.mock import patch

import pytest

from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager


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
    state_manager.change_state("idle")
    model_manager.reload_models("idle")
    assert len(model_manager.active_models) > 0
    with (
        patch("chatty_commander.app.model_manager.random.random", return_value=0.01),
        patch(
            "chatty_commander.app.model_manager.random.choice",
            return_value="hey_chat_tee",
        ),
        patch("time.sleep"),
    ):
        detected = model_manager.listen_for_commands()
        assert detected == "hey_chat_tee"
        new_state = state_manager.update_state(detected)
        assert new_state == "chatty"


def test_voice_recognition_integration_chatty(state_manager, model_manager):
    """Test integration in chatty state."""
    state_manager.change_state("chatty")
    model_manager.reload_models("chatty")
    assert len(model_manager.active_models) > 0
    with (
        patch("chatty_commander.app.model_manager.random.random", return_value=0.01),
        patch(
            "chatty_commander.app.model_manager.random.choice", return_value="okay_stop"
        ),
        patch("time.sleep"),
    ):
        detected = model_manager.listen_for_commands()
        assert detected == "okay_stop"
        new_state = state_manager.update_state(detected)
        assert new_state == "idle"


def test_no_detection_integration(state_manager, model_manager):
    """Test no detection case."""
    state_manager.change_state("computer")
    model_manager.reload_models("computer")
    with (
        patch("chatty_commander.app.model_manager.random.random", return_value=0.1),
        patch("time.sleep"),
    ):
        detected = model_manager.listen_for_commands()
        assert detected is None
        new_state = state_manager.update_state("invalid")
        assert new_state is None
        assert state_manager.current_state == "computer"
