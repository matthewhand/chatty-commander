"""
state_manager.py

Manages the state transitions and active model sets for the ChattyCommander application.
This module helps in toggling between different operational states based on detected commands
and manages the corresponding model activations. Enhanced to support dynamic state updates
and more complex state dependencies.
"""

import logging
from config import STATE_MODELS, DEFAULT_STATE

class StateManager:
    """
    Manages the different states of the application, such as idle, computer, and chatty,
    with enhancements for dynamic configuration and complex state dependencies.
    """

    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.current_state = DEFAULT_STATE  # Assuming a default state is defined in config
        self.active_models = STATE_MODELS.get(self.current_state, [])
        logging.info(f"StateManager initialized with state: {self.current_state}")

    def change_state(self, new_state):
        """
        Changes the application's state and updates the active models based on the new state,
        with validation checks and error handling for unsupported states.
        """
        if new_state in STATE_MODELS:
            self.current_state = new_state
            self.active_models = STATE_MODELS[new_state]
            logging.info(f"Transitioned to {new_state} state with models: {self.active_models}")
            self.post_state_change_hook(new_state)  # Post-change hook for additional actions
        else:
            logging.error(f"Attempted to transition to an undefined state: {new_state}")
            self.handle_invalid_state_transition(new_state)

    def get_active_models(self):
        """
        Returns the list of active models based on the current state.
        """
        return self.active_models

    def post_state_change_hook(self, new_state):
        """
        Hook to perform additional actions after a state change, such as reconfiguring system parameters
        or triggering external notifications.
        """
        logging.debug(f"Post state change actions for {new_state} executed.")

    def handle_invalid_state_transition(self, state):
        """
        Handles attempts to transition to an undefined state, potentially reverting to a safe default.
        """
        logging.warning(f"Reverting to default state due to invalid transition attempt.")
        self.change_state(DEFAULT_STATE)

    def __repr__(self):
        """
        Provides a detailed representation of the StateManager's state for debugging purposes.
        """
        return f"<StateManager(current_state={self.current_state}, active_models={len(self.active_models)})>"

# Example usage:
if __name__ == "__main__":
    state_manager = StateManager()
    print(state_manager)
    state_manager.change_state('computer')
    print(state_manager.get_active_models())
    state_manager.change_state('undefined_state')  # This should trigger error handling
