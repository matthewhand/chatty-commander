import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
import unittest
from unittest.mock import MagicMock

from src.chatty_commander.config import Config
from state_manager import StateManager


class TestStateManager(unittest.TestCase):
    def setUp(self):
        """Setup the StateManager with initial state for testing."""
        self.state_manager = StateManager()
        self.config = Config()
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)

    def test_initial_state(self):
        """Test that the initial state is set to 'idle'."""
        self.logger.debug(f"Initial state: {self.state_manager.current_state}")
        self.assertEqual(self.state_manager.current_state, 'idle')
        self.assertEqual(self.state_manager.get_active_models(), self.config.state_models['idle'])

    def test_state_transition(self):
        """Test transitioning to different states updates the active models correctly."""
        self.state_manager.change_state('computer')
        self.logger.debug(f"State after changing to computer: {self.state_manager.current_state}")
        self.assertEqual(self.state_manager.current_state, 'computer')
        self.assertEqual(
            self.state_manager.get_active_models(), self.config.state_models['computer']
        )

        self.state_manager.change_state('chatty')
        self.logger.debug(f"State after changing to chatty: {self.state_manager.current_state}")
        self.assertEqual(self.state_manager.current_state, 'chatty')
        self.assertEqual(self.state_manager.get_active_models(), self.config.state_models['chatty'])

    def test_invalid_state_transition(self):
        """Test that an invalid state transition raises a ValueError."""
        with self.assertRaises(ValueError):
            self.state_manager.change_state('invalid_state')
        self.logger.debug(
            f"State after invalid transition attempt: {self.state_manager.current_state}"
        )
        self.assertEqual(self.state_manager.current_state, self.config.default_state)

    def test_update_state_specific_commands(self):
        """Test update_state with specific commands."""
        self.assertEqual(self.state_manager.update_state('hey_chat_tee'), 'chatty')
        self.logger.debug(f"State after 'hey_chat_tee': {self.state_manager.current_state}")
        self.assertEqual(self.state_manager.current_state, 'chatty')

        self.assertEqual(self.state_manager.update_state('hey_khum_puter'), 'computer')
        self.logger.debug(f"State after 'hey_khum_puter': {self.state_manager.current_state}")
        self.assertEqual(self.state_manager.current_state, 'computer')

        self.assertEqual(self.state_manager.update_state('okay_stop'), 'idle')
        self.logger.debug(f"State after 'okay_stop': {self.state_manager.current_state}")
        self.assertEqual(self.state_manager.current_state, 'idle')

        self.state_manager.change_state('chatty')  # Set to non-idle state first
        self.assertEqual(self.state_manager.update_state('thanks_chat_tee'), 'idle')
        self.logger.debug(
            f"State after 'thanks_chat_tee' from chatty: {self.state_manager.current_state}"
        )
        self.state_manager.change_state('computer')  # Set to non-idle state first
        self.assertEqual(self.state_manager.update_state('that_ill_do'), 'idle')
        self.logger.debug(
            f"State after 'that_ill_do' from computer: {self.state_manager.current_state}"
        )

    def test_update_state_no_change(self):
        """Test update_state when no transition occurs."""
        self.state_manager.current_state = 'idle'
        self.assertIsNone(self.state_manager.update_state('unknown_command'))
        self.logger.debug(
            f"State after unknown command in idle: {self.state_manager.current_state}"
        )
        self.assertEqual(self.state_manager.current_state, 'idle')

        self.state_manager.current_state = 'chatty'
        self.assertIsNone(self.state_manager.update_state('hey_chat_tee'))
        self.logger.debug(
            f"State after 'hey_chat_tee' in chatty: {self.state_manager.current_state}"
        )
        self.assertEqual(self.state_manager.current_state, 'chatty')

    def test_toggle_mode(self):
        self.state_manager.update_state('toggle_mode')
        self.logger.debug(f"State after first toggle: {self.state_manager.current_state}")
        self.assertEqual(self.state_manager.current_state, 'computer')
        self.state_manager.update_state('toggle_mode')
        self.logger.debug(f"State after second toggle: {self.state_manager.current_state}")
        self.assertEqual(self.state_manager.current_state, 'chatty')
        self.state_manager.update_state('toggle_mode')
        self.logger.debug(f"State after third toggle: {self.state_manager.current_state}")
        self.assertEqual(self.state_manager.current_state, 'idle')

    def test_repr(self):
        """Test __repr__ method."""
        self.state_manager.active_models = ['model1', 'model2']
        self.assertEqual(
            repr(self.state_manager), '<StateManager(current_state=idle, active_models=2)>'
        )
        self.logger.debug(f"Repr: {repr(self.state_manager)}")

    # Expanded tests
    def test_all_state_transitions(self):
        """Test all possible state transitions."""
        transitions = {
            'idle': {
                'hey_chat_tee': 'chatty',
                'hey_khum_puter': 'computer',
                'toggle_mode': 'computer',
            },
            'chatty': {
                'hey_khum_puter': 'computer',
                'okay_stop': 'idle',
                'thanks_chat_tee': 'idle',
                'toggle_mode': 'idle',
            },
            'computer': {
                'hey_chat_tee': 'chatty',
                'okay_stop': 'idle',
                'that_ill_do': 'idle',
                'toggle_mode': 'chatty',
            },
        }
        for start_state, cmds in transitions.items():
            for cmd, end_state in cmds.items():
                self.state_manager.change_state(start_state)
                new_state = self.state_manager.update_state(cmd)
                self.logger.debug(f"Transition from {start_state} with '{cmd}' to {new_state}")
                self.assertEqual(new_state, end_state)
                self.assertEqual(self.state_manager.current_state, end_state)

    def test_invalid_commands_in_all_states(self):
        """Test invalid commands in all states do not change state."""
        states = ['idle', 'chatty', 'computer']
        invalid_cmd = 'invalid_command'
        for state in states:
            self.state_manager.change_state(state)
            self.assertIsNone(self.state_manager.update_state(invalid_cmd))
            self.logger.debug(f"State remains {state} after invalid command")
            self.assertEqual(self.state_manager.current_state, state)

    def test_multiple_toggles(self):
        """Test multiple toggle_mode calls cycle through states correctly."""
        cycles = [('idle', 'computer'), ('computer', 'chatty'), ('chatty', 'idle')]
        self.state_manager.change_state('idle')
        for _ in range(6):  # Two full cycles
            current = self.state_manager.current_state
            self.state_manager.update_state('toggle_mode')
            new = self.state_manager.current_state
            self.logger.debug(f"Toggle from {current} to {new}")
            self.assertEqual(new, next((end for start, end in cycles if start == current), None))

    def test_state_after_error(self):
        """Test state remains unchanged after error in transition."""
        self.state_manager.change_state('chatty')
        with self.assertRaises(ValueError):
            self.state_manager.change_state('invalid')
        self.logger.debug(f"State after error: {self.state_manager.current_state}")
        self.assertEqual(self.state_manager.current_state, 'chatty')

    def test_active_models_update(self):
        """Test active models update on state change."""
        self.state_manager.change_state('computer')
        self.logger.debug(f"Active models in computer: {self.state_manager.get_active_models()}")
        self.assertEqual(
            self.state_manager.get_active_models(), self.config.state_models['computer']
        )

        self.state_manager.change_state('idle')
        self.logger.debug(f"Active models in idle: {self.state_manager.get_active_models()}")
        self.assertEqual(self.state_manager.get_active_models(), self.config.state_models['idle'])

    def test_post_state_change_hook(self):
        """Test post_state_change_hook is called on state change."""
        with self.assertLogs(level='DEBUG') as log:
            self.state_manager.change_state('chatty')
        self.assertTrue(
            any('Post state change actions for chatty' in msg for msg in log.output),
            "Expected log message about post state change actions for chatty not found.",
        )

    def test_change_state_with_callback(self):
        """Test change_state with callback."""
        callback = MagicMock()
        self.state_manager.change_state('computer', callback)
        callback.assert_called_once_with('computer')
        self.assertEqual(self.state_manager.current_state, 'computer')

    def test_update_state_invalid_command(self):
        """Test update_state with invalid command returns None and doesn't change state."""
        current = self.state_manager.current_state
        result = self.state_manager.update_state('invalid')
        self.assertIsNone(result)
        self.assertEqual(self.state_manager.current_state, current)

    def test_repr_with_different_models(self):
        """Test __repr__ with varying active models."""
        self.state_manager.active_models = []
        self.assertEqual(
            repr(self.state_manager), '<StateManager(current_state=idle, active_models=0)>'
        )
        self.state_manager.active_models = ['one']
        self.assertEqual(
            repr(self.state_manager), '<StateManager(current_state=idle, active_models=1)>'
        )


if __name__ == '__main__':
    unittest.main()
