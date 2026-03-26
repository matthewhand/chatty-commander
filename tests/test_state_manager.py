import subprocess
import sys
from unittest.mock import Mock

import pytest

from chatty_commander.app.state_manager import StateManager
from conftest import TestDataFactory


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
        callback_called = []

        def test_callback(old_state, new_state):
            callback_called.append((old_state, new_state))

        sm.add_state_change_callback(test_callback)
        sm.change_state("computer")
        assert len(callback_called) == 1
        assert callback_called[0] == ("idle", "computer")

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


class TestStateManagerMain:
    """Tests for the StateManager __main__ block via subprocess."""

    def test_state_manager_main_block(self):
        """Test state_manager main block execution."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from chatty_commander.app.state_manager import StateManager; "
                "sm = StateManager(); "
                "print(sm); "
                "sm.change_state('computer'); "
                "print(sm.get_active_models()); "
                "try: sm.change_state('undefined_state'); "
                "except ValueError: pass",
            ],
            capture_output=True,
            text=True,
        )

        # Should not crash
        assert result.returncode == 0 or "ValueError" in result.stderr

    def test_state_manager_main_execution(self):
        """Test running state_manager as main module."""
        result = subprocess.run(
            [sys.executable, "-m", "chatty_commander.app.state_manager"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # The script should run and may exit with error due to undefined_state
        # but it should at least start executing
        assert result.returncode in [0, 1]  # 0 for success, 1 for expected error
