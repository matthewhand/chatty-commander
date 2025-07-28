import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from state_manager import StateManager
from config import Config

class TestStateManager(unittest.TestCase):
    def setUp(self):
        """Setup the StateManager with initial state for testing."""
        self.state_manager = StateManager()
        self.config = Config()

    def test_initial_state(self):
        """Test that the initial state is set to 'idle'."""
        self.assertEqual(self.state_manager.current_state, 'idle')
        self.assertEqual(self.state_manager.get_active_models(), self.config.state_models['idle'])

    def test_state_transition(self):
        """Test transitioning to different states updates the active models correctly."""
        self.state_manager.change_state('computer')
        self.assertEqual(self.state_manager.current_state, 'computer')
        self.assertEqual(self.state_manager.get_active_models(), self.config.state_models['computer'])

        self.state_manager.change_state('chatty')
        self.assertEqual(self.state_manager.current_state, 'chatty')
        self.assertEqual(self.state_manager.get_active_models(), self.config.state_models['chatty'])

    def test_invalid_state_transition(self):
        """Test that an invalid state transition raises a ValueError."""
        with self.assertRaises(ValueError):
            self.state_manager.change_state('invalid_state')
        self.assertEqual(self.state_manager.current_state, self.config.default_state)

    def test_update_state_specific_commands(self):
        """Test update_state with specific commands."""
        self.assertEqual(self.state_manager.update_state('hey_chat_tee'), 'chatty')
        self.assertEqual(self.state_manager.current_state, 'chatty')

        self.assertEqual(self.state_manager.update_state('hey_khum_puter'), 'computer')
        self.assertEqual(self.state_manager.current_state, 'computer')

        self.assertEqual(self.state_manager.update_state('okay_stop'), 'idle')
        self.assertEqual(self.state_manager.current_state, 'idle')

        self.state_manager.change_state('chatty')  # Set to non-idle state first
        self.assertEqual(self.state_manager.update_state('thanks_chat_tee'), 'idle')
        self.state_manager.change_state('computer')  # Set to non-idle state first
        self.assertEqual(self.state_manager.update_state('that_ill_do'), 'idle')

    def test_update_state_no_change(self):
        """Test update_state when no transition occurs."""
        self.state_manager.current_state = 'idle'
        self.assertIsNone(self.state_manager.update_state('unknown_command'))
        self.assertEqual(self.state_manager.current_state, 'idle')

        self.state_manager.current_state = 'chatty'
        self.assertIsNone(self.state_manager.update_state('hey_chat_tee'))
        self.assertEqual(self.state_manager.current_state, 'chatty')

    def test_toggle_mode(self):
        self.state_manager.update_state('toggle_mode')
        self.assertEqual(self.state_manager.current_state, 'computer')
        self.state_manager.update_state('toggle_mode')
        self.assertEqual(self.state_manager.current_state, 'chatty')
        self.state_manager.update_state('toggle_mode')
        self.assertEqual(self.state_manager.current_state, 'idle')

    def test_repr(self):
        """Test __repr__ method."""
        self.state_manager.active_models = ['model1', 'model2']
        self.assertEqual(repr(self.state_manager), '<StateManager(current_state=idle, active_models=2)>')

if __name__ == '__main__':
    unittest.main()
