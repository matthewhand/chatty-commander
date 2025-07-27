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

    def test_state_transition_with_callback(self):
        """Test state transition with a callback function."""
        def callback(new_state):
            self.callback_called = True
            self.callback_state = new_state

        self.callback_called = False
        self.state_manager.change_state('computer', callback)
        self.assertTrue(self.callback_called)
        self.assertEqual(self.callback_state, 'computer')
        """Test state transitions with a callback to ensure models are loaded as expected."""
        with self.assertLogs('state_manager', level='INFO') as log:
            self.state_manager.change_state('computer')
            self.assertIn("Transitioned to computer state.", log.output[0])
            self.assertIn("Active models:", log.output[0])

if __name__ == '__main__':
    unittest.main()
