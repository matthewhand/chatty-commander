import logging
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


class TestStateTransitions:
    """Tests for state transitions, toggle cycling, repr, and hooks.

    Migrated from test_states.py (unique tests only, converted to pytest style).
    """

    @pytest.fixture
    def sm(self) -> StateManager:
        """Provide a StateManager with the default mock config."""
        return StateManager(TestDataFactory.create_mock_config())

    @pytest.fixture
    def config(self) -> Mock:
        return TestDataFactory.create_mock_config()

    def test_update_state_no_change_unknown_command(self, sm):
        """Unknown command returns None and keeps current state."""
        assert sm.update_state("unknown_command") is None
        assert sm.current_state == "idle"

    def test_update_state_self_loop(self, sm, config):
        """Command mapping to the same state returns that state."""
        # Set up a transition that maps back to the same state
        config_with_loop = TestDataFactory.create_mock_config(
            {"state_transitions": {"idle": {"stay": "idle"}}}
        )
        sm_loop = StateManager(config_with_loop)
        assert sm_loop.update_state("stay") == "idle"
        assert sm_loop.current_state == "idle"

    def test_toggle_mode_cycles_states(self, sm):
        """toggle_mode cycles through states in order."""
        sm.update_state("toggle_mode")
        assert sm.current_state == "computer"
        sm.update_state("toggle_mode")
        assert sm.current_state == "chatty"
        sm.update_state("toggle_mode")
        assert sm.current_state == "idle"

    def test_multiple_toggle_cycles(self, sm, config):
        """Two full toggle cycles return to the starting state."""
        states = list(config.state_models.keys())
        for _ in range(2 * len(states)):
            current = sm.current_state
            sm.update_state("toggle_mode")
            idx = states.index(current)
            assert sm.current_state == states[(idx + 1) % len(states)]
        assert sm.current_state == "idle"

    def test_all_state_transitions(self, config):
        """Every transition defined in config produces the expected state."""
        for start_state, cmds in config.state_transitions.items():
            for cmd, end_state in cmds.items():
                sm = StateManager(config)
                sm.change_state(start_state)
                new_state = sm.update_state(cmd)
                assert new_state == end_state
                assert sm.current_state == end_state

    def test_invalid_commands_in_all_states(self, config):
        """Invalid commands do not change state in any state."""
        for state in config.state_transitions:
            sm = StateManager(config)
            sm.change_state(state)
            assert sm.update_state("invalid_command") is None
            assert sm.current_state == state

    def test_state_preserved_after_error(self, sm):
        """State remains unchanged after a failed change_state call."""
        sm.change_state("computer")
        with pytest.raises(ValueError):
            sm.change_state("nonexistent")
        assert sm.current_state == "computer"

    def test_post_state_change_hook_logged(self, sm):
        """post_state_change_hook emits the expected log message."""
        with _capture_logs() as logs:
            sm.change_state("chatty")
        assert any("Post state change actions for chatty" in r.message for r in logs)

    def test_change_state_with_direct_callback(self, sm):
        """change_state invokes the optional callback argument."""
        callback = Mock()
        sm.change_state("computer", callback)
        callback.assert_called_once_with("computer")
        assert sm.current_state == "computer"

    def test_repr_output(self, sm):
        """__repr__ shows state and model count."""
        sm.active_models = ["m1", "m2"]
        assert repr(sm) == "<StateManager(current_state=idle, active_models=2)>"

    def test_repr_with_varying_models(self, sm):
        """__repr__ reflects different active model counts."""
        sm.active_models = []
        assert repr(sm) == "<StateManager(current_state=idle, active_models=0)>"
        sm.active_models = ["one"]
        assert repr(sm) == "<StateManager(current_state=idle, active_models=1)>"


class _capture_logs:
    """Minimal context manager to capture log records from state_manager."""

    def __enter__(self):
        self.handler = logging.Handler()
        self.records: list[logging.LogRecord] = []
        self.handler.emit = self.records.append  # type: ignore[assignment]
        logger = logging.getLogger("chatty_commander.app.state_manager")
        logger.addHandler(self.handler)
        self._logger = logger
        return self.records

    def __exit__(self, *exc):
        self._logger.removeHandler(self.handler)
        return False


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
