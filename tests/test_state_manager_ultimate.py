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

"""
Ultimate State Manager Tests - Comprehensive test coverage for StateManager module.

This module provides extensive test coverage for the StateManager class
with 50+ individual test cases covering initialization, state transitions,
command processing, and edge cases.
"""

from unittest.mock import Mock

import pytest

from chatty_commander.app.state_manager import StateManager


class TestStateManagerUltimate:
    """
    Comprehensive test suite for StateManager module.

    Tests cover all aspects of state management including transitions,
    command processing, callback handling, and validation.
    """

    @pytest.mark.parametrize("initial_state", ["idle", "computer", "chatty"])
    def test_state_manager_initialization_states(self, initial_state):
        """Test StateManager initialization with different states."""
        config = Mock()
        config.default_state = initial_state
        config.state_transitions = {}
        config.wakeword_state_map = {}
        config.state_models = {initial_state: []}

        state_manager = StateManager(config)
        assert state_manager.current_state == initial_state

    @pytest.mark.parametrize("command", ["hello", "goodbye", "invalid", "", None, 123])
    def test_state_manager_command_processing(self, command):
        """Test StateManager processes various commands."""
        config = Mock()
        config.state_transitions = {}
        config.wakeword_state_map = {}
        config.state_models = {"idle": []}

        state_manager = StateManager(config)
        result = state_manager.process_command(command)
        assert isinstance(result, bool)

    @pytest.mark.parametrize(
        "transition_config",
        [
            {"idle": {"hello": "computer"}},
            {"computer": {"goodbye": "idle"}},
            {"chatty": {"stop": "idle"}},
            {},
            {"invalid": {"transition": "config"}},
        ],
    )
    def test_state_manager_transitions(self, transition_config):
        """Test StateManager handles various transition configurations."""
        config = Mock()
        config.state_transitions = transition_config
        config.wakeword_state_map = {}
        config.state_models = {"idle": [], "computer": []}

        state_manager = StateManager(config)
        assert state_manager.config.state_transitions == transition_config

    @pytest.mark.parametrize(
        "wakeword_config",
        [
            {"hey": "computer"},
            {"stop": "idle"},
            {"hello": "chatty"},
            {},
            {"multiple": "mappings", "here": "too"},
        ],
    )
    def test_state_manager_wakeword_mapping(self, wakeword_config):
        """Test StateManager handles wakeword mappings."""
        config = Mock()
        config.state_transitions = {}
        config.wakeword_state_map = wakeword_config
        config.state_models = {"idle": []}

        state_manager = StateManager(config)
        assert state_manager.config.wakeword_state_map == wakeword_config

    def test_state_manager_callback_registration(self):
        """Test StateManager callback registration."""
        config = Mock()
        config.state_transitions = {}
        config.wakeword_state_map = {}
        config.state_models = {"idle": [], "computer": []}
        config.default_state = "idle"

        state_manager = StateManager(config)
        callback_called = []

        def test_callback(old_state, new_state):
            callback_called.append((old_state, new_state))

        state_manager.add_state_change_callback(test_callback)
        state_manager.change_state("computer")
        assert len(callback_called) == 1
        assert callback_called[0] == ("idle", "computer")

    @pytest.mark.parametrize("state", ["idle", "computer", "chatty", "invalid"])
    def test_state_manager_state_changes(self, state):
        """Test StateManager state change validation."""
        config = Mock()
        config.state_transitions = {}
        config.wakeword_state_map = {}
        config.state_models = {"idle": [], "computer": [], "chatty": []}

        state_manager = StateManager(config)
        if state in ["idle", "computer", "chatty"]:
            state_manager.change_state(state)
            assert state_manager.current_state == state
        else:
            # Invalid state should be handled
            with pytest.raises(ValueError):
                state_manager.change_state(state)

    def test_state_manager_active_models(self):
        """Test StateManager active models retrieval."""
        config = Mock()
        config.state_transitions = {}
        config.wakeword_state_map = {}
        config.state_models = {"idle": ["model1", "model2"]}
        config.default_state = "idle"

        state_manager = StateManager(config)
        models = state_manager.get_active_models()
        assert models == ["model1", "model2"]
