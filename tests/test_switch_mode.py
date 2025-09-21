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
Comprehensive tests for switch mode tool.

Tests system state management, mode switching, and state persistence.
"""

from unittest.mock import Mock

import pytest

from src.chatty_commander.advisors.tools.switch_mode import SwitchModeTool


class TestSwitchModeTool:
    """Comprehensive tests for SwitchModeTool class."""

    @pytest.fixture
    def mock_state_manager(self):
        """Create mock state manager."""
        state_manager = Mock()
        state_manager.change_state.return_value = True
        state_manager.get_current_state.return_value = "idle"
        return state_manager

    @pytest.fixture
    def sample_config(self):
        """Create sample configuration for testing."""
        return {
            "available_modes": ["idle", "chatty", "computer", "avatar"],
            "default_mode": "idle",
            "mode_transitions": {
                "idle": ["chatty", "computer"],
                "chatty": ["idle", "computer", "avatar"],
                "computer": ["idle", "chatty", "avatar"],
                "avatar": ["idle", "chatty", "computer"],
            },
        }

    def test_switch_mode_tool_initialization(self, sample_config):
        """Test SwitchModeTool initialization."""
        tool = SwitchModeTool(sample_config)

        assert tool.config == sample_config
        assert tool.available_modes == ["idle", "chatty", "computer", "avatar"]

    def test_switch_to_valid_mode(self, sample_config, mock_state_manager):
        """Test switching to a valid mode."""
        tool = SwitchModeTool(sample_config)
        tool.state_manager = mock_state_manager

        result = tool.switch_mode("chatty")

        assert result is True
        mock_state_manager.change_state.assert_called_once_with("chatty")

    def test_switch_to_invalid_mode(self, sample_config, mock_state_manager):
        """Test switching to an invalid mode."""
        tool = SwitchModeTool(sample_config)
        tool.state_manager = mock_state_manager

        result = tool.switch_mode("invalid_mode")

        assert result is False
        mock_state_manager.change_state.assert_not_called()

    def test_get_current_mode(self, sample_config, mock_state_manager):
        """Test getting current mode."""
        mock_state_manager.get_current_state.return_value = "computer"

        tool = SwitchModeTool(sample_config)
        tool.state_manager = mock_state_manager

        current_mode = tool.get_current_mode()

        assert current_mode == "computer"
        mock_state_manager.get_current_state.assert_called_once()

    def test_get_available_modes(self, sample_config):
        """Test getting available modes."""
        tool = SwitchModeTool(sample_config)

        modes = tool.get_available_modes()

        assert "idle" in modes
        assert "chatty" in modes
        assert "computer" in modes
        assert "avatar" in modes
        assert len(modes) == 4

    def test_get_possible_transitions(self, sample_config):
        """Test getting possible transitions from current mode."""
        tool = SwitchModeTool(sample_config)

        # Test transitions from idle
        transitions = tool.get_possible_transitions("idle")
        assert "chatty" in transitions
        assert "computer" in transitions
        assert len(transitions) == 2

        # Test transitions from chatty
        transitions = tool.get_possible_transitions("chatty")
        assert "idle" in transitions
        assert "computer" in transitions
        assert "avatar" in transitions
        assert len(transitions) == 3

    def test_switch_with_context(self, sample_config, mock_state_manager):
        """Test switching mode with context information."""
        tool = SwitchModeTool(sample_config)
        tool.state_manager = mock_state_manager

        context = {
            "reason": "User requested mode change",
            "previous_mode": "idle",
            "timestamp": "2024-01-01T10:00:00Z",
        }

        result = tool.switch_mode("chatty", context=context)

        assert result is True
        # Context should be passed to state manager
        mock_state_manager.change_state.assert_called_once()

    def test_forced_mode_switch(self, sample_config, mock_state_manager):
        """Test forced mode switching."""
        mock_state_manager.change_state.return_value = False  # First attempt fails

        tool = SwitchModeTool(sample_config)
        tool.state_manager = mock_state_manager

        result = tool.switch_mode("chatty", force=True)

        # Should attempt the switch even if validation might fail
        mock_state_manager.change_state.assert_called_once_with("chatty")

    def test_mode_validation(self, sample_config):
        """Test mode validation functionality."""
        tool = SwitchModeTool(sample_config)

        assert tool.is_valid_mode("idle") is True
        assert tool.is_valid_mode("chatty") is True
        assert tool.is_valid_mode("invalid") is False
        assert tool.is_valid_mode("") is False

    def test_state_manager_error_handling(self, sample_config, mock_state_manager):
        """Test error handling when state manager fails."""
        mock_state_manager.change_state.side_effect = Exception("State manager error")

        tool = SwitchModeTool(sample_config)
        tool.state_manager = mock_state_manager

        result = tool.switch_mode("chatty")

        assert result is False

    def test_get_mode_info(self, sample_config):
        """Test getting detailed mode information."""
        tool = SwitchModeTool(sample_config)

        info = tool.get_mode_info("chatty")

        assert "name" in info
        assert "transitions" in info
        assert info["name"] == "chatty"
        assert "idle" in info["transitions"]
        assert "computer" in info["transitions"]
        assert "avatar" in info["transitions"]

    def test_batch_mode_operations(self, sample_config, mock_state_manager):
        """Test batch mode switching operations."""
        tool = SwitchModeTool(sample_config)
        tool.state_manager = mock_state_manager

        modes_to_switch = ["chatty", "computer", "avatar"]

        results = tool.batch_switch_modes(modes_to_switch)

        assert len(results) == 3
        assert all(results)  # All should succeed

        # Should have called state manager 3 times
        assert mock_state_manager.change_state.call_count == 3

    def test_mode_persistence(self, sample_config, mock_state_manager):
        """Test mode persistence across sessions."""
        tool = SwitchModeTool(sample_config)
        tool.state_manager = mock_state_manager

        # Switch to a mode
        tool.switch_mode("computer")

        # Get current mode (should persist)
        current = tool.get_current_mode()
        assert current == "computer"

    def test_cyclic_mode_validation(self, sample_config):
        """Test validation of cyclic mode transitions."""
        tool = SwitchModeTool(sample_config)

        # Test that cyclic transitions are properly validated
        # From idle -> chatty -> computer -> avatar -> idle should work
        cycle = ["idle", "chatty", "computer", "avatar", "idle"]

        for i in range(len(cycle) - 1):
            current = cycle[i]
            next_mode = cycle[i + 1]
            assert tool.is_valid_transition(current, next_mode) is True

    def test_invalid_transition_detection(self, sample_config):
        """Test detection of invalid mode transitions."""
        tool = SwitchModeTool(sample_config)

        # These transitions should be invalid
        invalid_transitions = [
            ("idle", "avatar"),  # Can't go directly from idle to avatar
            ("nonexistent", "chatty"),  # Invalid source mode
            ("chatty", "nonexistent"),  # Invalid target mode
        ]

        for current, target in invalid_transitions:
            assert tool.is_valid_transition(current, target) is False

    def test_configuration_override(self, sample_config):
        """Test configuration override functionality."""
        # Create tool with initial config
        tool = SwitchModeTool(sample_config)

        # Override configuration
        new_config = {
            "available_modes": ["simple", "advanced"],
            "default_mode": "simple",
        }

        tool.update_config(new_config)

        assert tool.available_modes == ["simple", "advanced"]
        assert tool.config["default_mode"] == "simple"

    def test_event_callbacks(self, sample_config, mock_state_manager):
        """Test event callback functionality."""
        callback_called = False
        callback_data = None

        def mode_change_callback(old_mode, new_mode, context):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = {"old": old_mode, "new": new_mode, "context": context}

        tool = SwitchModeTool(sample_config)
        tool.state_manager = mock_state_manager
        tool.add_mode_change_callback(mode_change_callback)

        tool.switch_mode("chatty", context={"reason": "test"})

        assert callback_called is True
        assert callback_data["old"] == "idle"  # Default starting mode
        assert callback_data["new"] == "chatty"
        assert callback_data["context"]["reason"] == "test"

    def test_statistics_tracking(self, sample_config, mock_state_manager):
        """Test mode switching statistics tracking."""
        tool = SwitchModeTool(sample_config)
        tool.state_manager = mock_state_manager

        # Perform several mode switches
        tool.switch_mode("chatty")
        tool.switch_mode("computer")
        tool.switch_mode("chatty")
        tool.switch_mode("idle")

        stats = tool.get_switching_statistics()

        assert "total_switches" in stats
        assert "mode_frequency" in stats
        assert "success_rate" in stats
        assert stats["total_switches"] == 4
        assert stats["success_rate"] == 1.0  # All succeeded

    def test_emergency_mode_reset(self, sample_config, mock_state_manager):
        """Test emergency mode reset functionality."""
        tool = SwitchModeTool(sample_config)
        tool.state_manager = mock_state_manager

        # Switch to a problematic mode
        tool.switch_mode("computer")

        # Emergency reset to default
        reset_result = tool.emergency_reset()

        assert reset_result is True
        mock_state_manager.change_state.assert_called_with("idle")
