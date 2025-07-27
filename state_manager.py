"""
state_manager.py

Manages the state transitions and active model sets for the ChattyCommander application.
This module helps in toggling between different operational states based on detected commands
and manages the corresponding model activations. Enhanced to support dynamic state updates
and more complex state dependencies.
"""

import logging
from config import Config

class StateManager:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.current_state = self.config.default_state
        self.active_models = self.config.state_models.get(self.current_state, [])
        self.logger.info(f"StateManager initialized with state: {self.current_state}")

    def change_state(self, new_state, callback=None):
        if new_state in self.config.state_models:
            self.current_state = new_state
            self.active_models = self.config.state_models[new_state]
            self.logger.info(f"Transitioned to {new_state} state. Active models: {self.active_models}")
            self.post_state_change_hook(new_state)
            if callback:
                callback(new_state)
        else:
            raise ValueError(f"Invalid state: {new_state}")

    def get_active_models(self):
        return self.active_models

    def post_state_change_hook(self, new_state):
        self.logger.debug(f"Post state change actions for {new_state} executed.")

    def __repr__(self):
        return f"<StateManager(current_state={self.current_state}, active_models={len(self.active_models)})>"

# Example usage:
if __name__ == "__main__":
    state_manager = StateManager()
    print(state_manager)
    state_manager.change_state('computer')
    print(state_manager.get_active_models())
    state_manager.change_state('undefined_state')  # This should trigger error handling
