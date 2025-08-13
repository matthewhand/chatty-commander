"""
state_manager.py

Manages the state transitions and active model sets for the ChattyCommander application.
This module helps in toggling between different operational states based on detected commands
and manages the corresponding model activations. Enhanced to support dynamic state updates
and more complex state dependencies.
"""

import logging
from collections.abc import Callable

from chatty_commander.app.config import Config


class StateManager:
    def __init__(self) -> None:
        self.config: Config = Config()
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.current_state: str = self.config.default_state
        self.active_models: list[str] = self.config.state_models.get(self.current_state, [])
        self.callbacks: list[Callable[[str, str], None]] = []
        self.logger.info(f"StateManager initialized with state: {self.current_state}")

    def update_state(self, command: str) -> str | None:
        """
        Updates the state based on the detected command.
        Returns the new state if a transition occurred, otherwise None.
        """
        new_state: str | None = None
        if command == 'hey_chat_tee':
            new_state = 'chatty'
        elif command == 'hey_khum_puter':
            new_state = 'computer'
        elif command in ['okay_stop', 'thanks_chat_tee', 'that_ill_do']:
            new_state = 'idle'
        elif command == 'toggle_mode':
            states = ['idle', 'computer', 'chatty']
            current_index = states.index(self.current_state)
            new_state = states[(current_index + 1) % len(states)]

        if new_state and new_state != self.current_state:
            self.change_state(new_state)
            return new_state
        return None

    def add_state_change_callback(self, callback: Callable[[str, str], None]) -> None:
        self.callbacks.append(callback)

    def change_state(self, new_state: str, callback: Callable[[str], None] | None = None) -> None:
        if new_state in self.config.state_models:
            old_state = self.current_state
            self.current_state = new_state
            self.active_models = self.config.state_models[new_state]
            self.logger.info(
                f"Transitioned to {new_state} state. Active models: {self.active_models}"
            )
            self.post_state_change_hook(new_state)
            for cb in self.callbacks:
                cb(old_state, new_state)
            if callback:
                callback(new_state)
        else:
            raise ValueError(f"Invalid state: {new_state}")

    def get_active_models(self) -> list[str]:
        return self.active_models

    def post_state_change_hook(self, new_state: str) -> None:
        self.logger.debug(f"Post state change actions for {new_state} executed.")

    def __repr__(self) -> str:
        return f"<StateManager(current_state={self.current_state}, active_models={len(self.active_models)})>"


# Example usage:
if __name__ == "__main__":
    state_manager = StateManager()
    print(state_manager)
    state_manager.change_state('computer')
    print(state_manager.get_active_models())
    state_manager.change_state('undefined_state')  # This should trigger error handling
