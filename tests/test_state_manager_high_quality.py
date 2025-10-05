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

"""High-quality tests for StateManager focusing on realistic scenarios and edge cases."""

import logging
from unittest.mock import Mock

import pytest

from src.chatty_commander.app.config import Config
from src.chatty_commander.app.state_manager import StateManager


class TestStateManagerInitialization:
    """Test StateManager initialization with realistic scenarios."""

    def test_state_manager_initialization_with_default_config(self):
        """Test StateManager initialization with default config."""
        state_manager = StateManager()

        assert state_manager.config is not None
        assert state_manager.current_state == "idle"  # default state
        assert isinstance(state_manager.active_models, list)
        assert isinstance(state_manager.callbacks, list)
        assert state_manager.logger.level == logging.DEBUG

    def test_state_manager_initialization_with_custom_config(self):
        """Test StateManager initialization with custom config."""
        custom_config = Config()
        custom_config.default_state = "computer"
        custom_config.state_models = {"computer": ["model1", "model2"]}

        state_manager = StateManager(custom_config)

        assert state_manager.config is custom_config
        assert state_manager.current_state == "computer"
        assert state_manager.active_models == ["model1", "model2"]

    def test_state_manager_initialization_with_missing_state_models(self):
        """Test initialization when current state not in state_models."""
        config = Config()
        config.default_state = "unknown_state"
        config.state_models = {"computer": ["model1"]}  # missing unknown_state

        state_manager = StateManager(config)

        assert state_manager.current_state == "unknown_state"
        assert state_manager.active_models == []  # Should default to empty list


class TestStateManagerStateTransitions:
    """Test state transition functionality."""

    @pytest.fixture
    def config_with_transitions(self):
        """Create a config with state transitions defined."""
        config = Config()
        config.state_transitions = {
            "idle": {"hey_computer": "computer", "start_chatting": "chatty"},
            "computer": {"go_idle": "idle", "start_chatting": "chatty"},
            "chatty": {"go_idle": "idle", "hey_computer": "computer"},
        }
        config.state_models = {
            "idle": ["idle_model1"],
            "computer": ["computer_model1", "computer_model2"],
            "chatty": ["chat_model1"],
        }
        return config

    def test_state_transition_via_state_transitions_config(
        self, config_with_transitions
    ):
        """Test state transition using state_transitions config."""
        state_manager = StateManager(config_with_transitions)

        # Transition from idle to computer
        new_state = state_manager.update_state("hey_computer")
        assert new_state == "computer"
        assert state_manager.current_state == "computer"
        assert state_manager.active_models == ["computer_model1", "computer_model2"]

    def test_state_transition_via_wakeword_mapping(self):
        """Test state transition using wakeword_state_map."""
        config = Config()
        config.wakeword_state_map = {"wake_up": "computer", "sleep": "idle"}
        config.state_models = {"idle": ["idle_model"], "computer": ["computer_model"]}

        state_manager = StateManager(config)

        # Transition via wakeword
        new_state = state_manager.update_state("wake_up")
        assert new_state == "computer"
        assert state_manager.current_state == "computer"

    def test_toggle_mode_cycling(self):
        """Test toggle_mode command cycles through states."""
        config = Config()
        config.state_models = {
            "idle": ["idle_model"],
            "computer": ["computer_model"],
            "chatty": ["chat_model"],
        }

        state_manager = StateManager(config)

        # Start in idle
        assert state_manager.current_state == "idle"

        # Toggle to computer
        new_state = state_manager.update_state("toggle_mode")
        assert new_state == "computer"
        assert state_manager.current_state == "computer"

        # Toggle to chatty
        new_state = state_manager.update_state("toggle_mode")
        assert new_state == "chatty"
        assert state_manager.current_state == "chatty"

        # Toggle back to idle
        new_state = state_manager.update_state("toggle_mode")
        assert new_state == "idle"
        assert state_manager.current_state == "idle"

    def test_no_transition_for_unknown_command(self, config_with_transitions):
        """Test that unknown commands don't change state."""
        state_manager = StateManager(config_with_transitions)
        original_state = state_manager.current_state

        new_state = state_manager.update_state("unknown_command")

        assert new_state is None
        assert state_manager.current_state == original_state

    def test_invalid_command_handling(self, config_with_transitions):
        """Test handling of invalid commands."""
        state_manager = StateManager(config_with_transitions)
        original_state = state_manager.current_state

        # Test empty string
        new_state = state_manager.update_state("")
        assert new_state is None
        assert state_manager.current_state == original_state

        # Test whitespace only
        new_state = state_manager.update_state("   ")
        assert new_state is None
        assert state_manager.current_state == original_state

        # Test non-string input
        new_state = state_manager.update_state(None)  # type: ignore
        assert new_state is None
        assert state_manager.current_state == original_state


class TestStateManagerProcessCommand:
    """Test the process_command method."""

    def test_process_command_success(self):
        """Test successful command processing."""
        config = Config()
        config.wakeword_state_map = {"test": "computer"}
        config.state_models = {"idle": [], "computer": []}

        state_manager = StateManager(config)

        result = state_manager.process_command("test")
        assert result is True
        assert state_manager.current_state == "computer"

    def test_process_command_toggle_mode(self):
        """Test process_command with toggle_mode."""
        config = Config()
        config.state_models = {"idle": [], "computer": []}

        state_manager = StateManager(config)

        result = state_manager.process_command("toggle_mode")
        assert result is True  # toggle_mode should always return True

    def test_process_command_failure(self):
        """Test process_command with invalid command."""
        state_manager = StateManager()

        result = state_manager.process_command("invalid_command")
        assert result is False

    def test_process_command_exception_handling(self):
        """Test process_command handles exceptions gracefully."""
        state_manager = StateManager()

        # Test with non-string input
        result = state_manager.process_command(123)  # type: ignore
        assert result is False


class TestStateManagerCallbacks:
    """Test callback functionality."""

    def test_callback_registration_and_execution(self):
        """Test that callbacks are registered and executed."""
        config = Config()
        config.wakeword_state_map = {"test": "computer"}
        config.state_models = {"idle": [], "computer": []}

        state_manager = StateManager(config)

        # Register a callback
        callback_calls = []

        def test_callback(old_state: str, new_state: str):
            callback_calls.append((old_state, new_state))

        state_manager.callbacks.append(test_callback)

        # Trigger state change
        state_manager.update_state("test")

        # Check callback was called
        assert len(callback_calls) == 1
        assert callback_calls[0] == ("idle", "computer")

    def test_multiple_callbacks_execution(self):
        """Test that multiple callbacks are executed in order."""
        config = Config()
        config.wakeword_state_map = {"test": "computer"}
        config.state_models = {"idle": [], "computer": []}

        state_manager = StateManager(config)

        # Register multiple callbacks
        execution_order = []

        def callback1(old_state: str, new_state: str):
            execution_order.append("callback1")

        def callback2(old_state: str, new_state: str):
            execution_order.append("callback2")

        state_manager.callbacks.extend([callback1, callback2])

        # Trigger state change
        state_manager.update_state("test")

        # Check both callbacks were called in order
        assert execution_order == ["callback1", "callback2"]

    def test_callback_exception_handling(self):
        """Test that callback exceptions are propagated."""
        config = Config()
        config.wakeword_state_map = {"test": "computer"}
        config.state_models = {"idle": [], "computer": []}

        state_manager = StateManager(config)

        # Register a callback that raises an exception
        def failing_callback(old_state: str, new_state: str):
            raise Exception("Callback error")

        callback_state = {"called": False}

        def working_callback(old_state: str, new_state: str):
            callback_state["called"] = True

        # Put working callback first, failing callback second
        state_manager.callbacks.extend([working_callback, failing_callback])

        # Trigger state change - should raise exception from failing callback
        with pytest.raises(Exception, match="Callback error"):
            state_manager.update_state("test")

        # State should still change despite exception
        assert state_manager.current_state == "computer"
        # Working callback should be called before exception
        assert callback_state["called"] is True


class TestStateManagerEdgeCases:
    """Test edge cases and error conditions."""

    def test_missing_config_attributes(self):
        """Test behavior when config attributes are missing."""
        config = Mock(spec=Config)
        config.default_state = "idle"
        config.state_models = {}
        # Missing state_transitions and wakeword_state_map

        state_manager = StateManager(config)

        # Should not crash and should handle missing attributes gracefully
        result = state_manager.update_state("any_command")
        assert result is None

    def test_invalid_config_attribute_types(self):
        """Test behavior when config attributes have wrong types."""
        config = Mock(spec=Config)
        config.default_state = "idle"
        config.state_models = {"idle": []}
        config.state_transitions = "not_a_dict"  # Wrong type
        config.wakeword_state_map = None

        state_manager = StateManager(config)

        # Should handle wrong types gracefully
        result = state_manager.update_state("any_command")
        assert result is None

    def test_empty_state_models(self):
        """Test behavior with empty state_models."""
        config = Config()
        config.state_models = {}

        state_manager = StateManager(config)

        # Should default to empty active_models
        assert state_manager.active_models == []

    def test_get_active_models_method(self):
        """Test get_active_models method."""
        config = Config()
        config.state_models = {
            "idle": ["idle_model1", "idle_model2"],
            "computer": ["computer_model1"],
        }

        state_manager = StateManager(config)

        # Test getting active models for current state
        active_models = state_manager.get_active_models()
        assert active_models == ["idle_model1", "idle_model2"]

        # Change state and test again using change_state method
        state_manager.change_state("computer")
        active_models = state_manager.get_active_models()
        assert active_models == ["computer_model1"]

    def test_change_state_method(self):
        """Test change_state method."""
        config = Config()
        config.state_models = {"idle": ["idle_model"], "computer": ["computer_model"]}

        state_manager = StateManager(config)

        # Test changing to valid state
        state_manager.change_state("computer")
        assert state_manager.current_state == "computer"
        assert state_manager.active_models == ["computer_model"]

        # Test changing to invalid state
        with pytest.raises(ValueError, match="Invalid state: invalid"):
            state_manager.change_state("invalid")


class TestStateManagerIntegration:
    """Integration tests for StateManager."""

    def test_full_state_lifecycle(self):
        """Test complete state management lifecycle."""
        config = Config()
        config.state_transitions = {
            "idle": {"activate": "computer"},
            "computer": {"deactivate": "idle"},
        }
        config.wakeword_state_map = {"wake": "computer", "sleep": "idle"}
        config.state_models = {
            "idle": ["idle_model"],
            "computer": ["computer_model1", "computer_model2"],
        }

        state_manager = StateManager(config)

        # Track state changes
        state_changes = []

        def track_changes(old_state: str, new_state: str):
            state_changes.append((old_state, new_state))

        state_manager.callbacks.append(track_changes)

        # Initial state
        assert state_manager.current_state == "idle"
        assert state_manager.get_active_models() == ["idle_model"]

        # Transition via state_transitions
        new_state = state_manager.update_state("activate")
        assert new_state == "computer"
        assert state_manager.current_state == "computer"
        assert state_manager.get_active_models() == [
            "computer_model1",
            "computer_model2",
        ]

        # Transition via wakeword
        new_state = state_manager.update_state("sleep")
        assert new_state == "idle"
        assert state_manager.current_state == "idle"
        assert state_manager.get_active_models() == ["idle_model"]

        # Verify callbacks were called
        assert len(state_changes) == 2
        assert state_changes[0] == ("idle", "computer")
        assert state_changes[1] == ("computer", "idle")

    def test_concurrent_state_changes(self):
        """Test behavior with rapid state changes."""
        config = Config()
        config.state_models = {
            "idle": ["idle_model"],
            "computer": ["computer_model"],
            "chatty": ["chat_model"],
        }

        state_manager = StateManager(config)

        # Rapid state changes
        states = []
        for _ in range(10):
            state_manager.update_state("toggle_mode")
            states.append(state_manager.current_state)

        # Should have cycled through states
        unique_states = set(states)
        assert len(unique_states) >= 2  # At least idle and one other state
        assert "idle" in unique_states
