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

"""Manage application state transitions.

This module toggles between different operational states based on detected
commands and manages the corresponding model activations. It supports dynamic
state updates and complex state dependencies.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from chatty_commander.app.config import Config


class StateManager:
    def __init__(self, config: Config | None = None) -> None:
        self.config: Config = config or Config()
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.current_state: str = self.config.default_state
        self.active_models: list[str] = self.config.state_models.get(
            self.current_state, []
        )
        self.callbacks: list[Callable[[str, str], None]] = []
        self.logger.info(f"StateManager initialized with state: {self.current_state}")

    def process_command(self, command: str) -> bool:
        """Process a command and return success status.

        This method provides a simple interface for command processing
        that returns a boolean success status.

        Args:
            command: The command to process

        Returns:
            True if command was processed successfully, False otherwise
        """
        try:
            result = self.update_state(command)
            # Return True if state changed or command was recognized
            return result is not None or command in ["toggle_mode"]
        except (ValueError, AttributeError, TypeError):
            # Handle invalid commands gracefully
            return False

    def update_state(self, command: str) -> str | None:
        """Update state based on a command.

        Returns the new state if a transition occurred, otherwise ``None``.
        """
        if not isinstance(command, str) or not command.strip():
            return None

        new_state: str | None = None

        # Check for state transitions from the current state
        if (
            hasattr(self.config, "state_transitions")
            and getattr(self.config, "state_transitions", None) is not None
            and isinstance(getattr(self.config, "state_transitions", None), dict)
            and self.current_state in self.config.state_transitions
            and command in self.config.state_transitions[self.current_state]
        ):
            new_state = self.config.state_transitions[self.current_state][command]
        # Flexible resolution via config-defined wakeword mapping
        elif (
            hasattr(self.config, "wakeword_state_map")
            and self.config.wakeword_state_map is not None
            and command in self.config.wakeword_state_map
        ):
            new_state = self.config.wakeword_state_map[command]
        elif command == "toggle_mode":
            states = list(self.config.state_models.keys()) or [
                "idle",
                "computer",
                "chatty",
            ]
            if self.current_state in states:
                current_index = states.index(self.current_state)
            else:
                current_index = 0
            new_state = states[(current_index + 1) % len(states)]

        if new_state and new_state != self.current_state:
            self.change_state(new_state)
            return new_state
        return None

    def add_state_change_callback(self, callback: Callable[[str, str], None]) -> None:
        self.callbacks.append(callback)

    def change_state(
        self, new_state: str, callback: Callable[[str], None] | None = None
    ) -> None:
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
        return (
            f"<StateManager(current_state={self.current_state}, "
            f"active_models={len(self.active_models)})>"
        )
