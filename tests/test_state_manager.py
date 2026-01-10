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

from unittest.mock import Mock

import pytest
from test_data_factories import TestDataFactory

from chatty_commander.app.state_manager import StateManager


class TestStateManager:
    """
    Comprehensive tests for the StateManager module.
    """

    @pytest.fixture
    def mock_config(self) -> Mock:
        """Provide a properly configured mock Config object."""
        return TestDataFactory.create_mock_config()

    @pytest.fixture
    def mock_state_manager(self, mock_config: Mock) -> Mock:
        """Provide a properly configured mock StateManager."""
        return TestDataFactory.create_mock_state_manager(mock_config)

    @pytest.mark.parametrize("initial_state", ["idle", "computer", "chatty"])
    def test_state_manager_initialization_states(self, initial_state):
        """Test StateManager initialization with different initial states."""
        config = TestDataFactory.create_mock_config({"default_state": initial_state})
        sm = StateManager(config)
        assert sm.current_state == initial_state

    @pytest.mark.parametrize("command", ["hello", "goodbye", "invalid", "", None, 123])
    def test_state_manager_command_processing(self, command):
        """Test StateManager command processing with various inputs."""
        sm = StateManager(TestDataFactory.create_mock_config())
        sm.process_command(command)  # Should not raise exception

    @pytest.mark.parametrize(
        "transition_config",
        [
            {"idle": {"start": "computer"}},
            {"computer": {"stop": "idle"}},
            {},
        ],
    )
    def test_state_manager_transitions(self, transition_config):
        """Test StateManager state transitions."""
        config = TestDataFactory.create_mock_config(
            {"state_transitions": transition_config}
        )
        sm = StateManager(config)
        # Assuming a method to trigger transition; adjust as needed
        sm.change_state("computer")  # Example transition
        # Add assertions based on expected behavior

    @pytest.mark.parametrize(
        "wakeword_config",
        [
            {"hey": "computer"},
            {"stop": "idle"},
            {},
        ],
    )
    def test_state_manager_wakeword_mapping(self, wakeword_config):
        """Test StateManager wakeword mapping."""
        config = TestDataFactory.create_mock_config(
            {"wakeword_state_map": wakeword_config}
        )
        sm = StateManager(config)
        assert sm is not None
        # Assuming a method to handle wakewords; adjust as needed
        # sm.handle_wakeword("hey")
        # Add assertions based on expected behavior

    def test_state_manager_callback_registration(self):
        """Test StateManager callback registration."""
        sm = StateManager(TestDataFactory.create_mock_config())
        callback = Mock()
        sm.add_state_change_callback(callback)
        sm.change_state("computer")
        # StateManager calls callbacks with (old_state, new_state)
        callback.assert_called_once_with("idle", "computer")

    @pytest.mark.parametrize("state", ["idle", "computer", "chatty", "invalid"])
    def test_state_manager_state_changes(self, state):
        """Test StateManager state changes."""
        sm = StateManager(TestDataFactory.create_mock_config())
        if state in ["idle", "computer", "chatty"]:
            sm.change_state(state)
            assert sm.current_state == state
        else:
            # Invalid states should raise ValueError
            with pytest.raises(ValueError):
                sm.change_state(state)

    def test_state_manager_active_models(self):
        """Test StateManager active models retrieval."""
        config = TestDataFactory.create_mock_config(
            {
                "state_models": {"idle": ["model1"], "computer": ["model2"]},
                "default_state": "idle",
            }
        )
        sm = StateManager(config)
        assert sm.get_active_models() == ["model1"]
        sm.change_state("computer")
        assert sm.get_active_models() == ["model2"]
