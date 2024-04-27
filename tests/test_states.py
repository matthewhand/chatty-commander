import unittest
from state_manager import StateManager
from config import STATE_MODELS

class TestStateManager(unittest.TestCase):
    def setUp(self):
        """Setup the StateManager with initial state for testing."""
        self.state_manager = StateManager()

    def test_initial_state(self):
        """Test that the initial state is set to 'idle'."""
        self.assertEqual(self.state_manager.current_state, 'idle')
        self.assertEqual(self.state_manager.get_active_models(), STATE_MODELS['idle'])

    def test_state_transition(self):
        """Test transitioning to different states updates the active models correctly."""
        self.state_manager.change_state('computer')
        self.assertEqual(self.state_manager.current_state, 'computer')
        self.assertEqual(self.state_manager.get_active_models(), STATE_MODELS['computer'])

        self.state_manager.change_state('chatty')
        self.assertEqual(self.state_manager.current_state, 'chatty')
        self.assertEqual(self.state_manager.get_active_models(), STATE_MODELS['chatty'])

    def test_invalid_state_transition(self):
        """Test that transitioning to an undefined state does not change the current state or models."""
        original_state = self.state_manager.current_state
        original_models = self.state_manager.get_active_models()
        self.state_manager.change_state('undefined')
        self.assertEqual(self.state_manager.current_state, original_state)
        self.assertEqual(self.state_manager.get_active_models(), original_models)

    def test_state_transition_with_callback(self):
        """Test state transitions with a callback to ensure models are loaded as expected."""
        with self.assertLogs('state_manager', level='INFO') as log:
            self.state_manager.change_state('computer')
            self.assertIn("Transitioned to computer state.", log.output[0])
            self.assertIn("Active models:", log.output[0])

if __name__ == '__main__':
    unittest.main()
