"""Small CLI helper for editing configuration files.

The original version of this module manipulated a nested dictionary.  After
switching the configuration system to dataclasses we expose a thin wrapper that
loads/saves :class:`chatty_commander.app.config.Config` instances and mutates
their typed attributes directly.
"""

from __future__ import annotations

import json
import os
import sys

from chatty_commander.app.config import Config

XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
APP_CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, "chatty-commander")
DEFAULT_CONFIG_PATH = os.path.join(APP_CONFIG_DIR, "config.json")


class ConfigCLI:
    """Helper class used by tests and the command line interface."""

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH) -> None:
        os.makedirs(APP_CONFIG_DIR, exist_ok=True)
        self.config_path = config_path
        self.config = self.load_config()

    # ------------------------------------------------------------------
    # Loading / saving

    def load_config(self) -> Config:
        """Load configuration from ``config_path``."""
        try:
            if os.path.exists(self.config_path):  # noqa: PTH110
                with open(self.config_path) as f:  # noqa: PTH123 - user path
                    data = json.load(f)
                return Config.from_dict(data, config_file=self.config_path)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {self.config_path}", file=sys.stderr)
        # Fallback to empty config on error
        return Config(
            model_actions={},
            state_models={},
            listen_for={},
            modes={},
            config_file=self.config_path,
        )

    def save_config(self) -> None:
        with open(self.config_path, "w") as f:  # noqa: PTH123 - user path
            json.dump(self.config.to_dict(), f, indent=4)

    # ------------------------------------------------------------------
    # Mutators used by tests

    def set_model_action(self, model_name: str, action: str) -> None:
        self.config.model_actions[model_name] = action
        self.save_config()

    def set_state_model(self, state: str, models_str: str) -> None:
        self.config.state_models[state] = [m.strip() for m in models_str.split(",")]
        self.save_config()

    def set_listen_for(self, key: str, value: str) -> None:
        self.config.listen_for[key] = value
        self.save_config()

    def set_mode(self, mode: str, value: str) -> None:
        self.config.modes[mode] = value
        self.save_config()

    # ------------------------------------------------------------------
    # Display helpers

    def list_config(self) -> None:
        print("Current Configuration:")
        print("\nModel Actions:")
        for model, action in self.config.model_actions.items():
            if isinstance(action, dict):
                keybinding = action.get("keypress", "N/A")
                print(f"- {model}: Action={action}, Keybinding={keybinding}")
            else:
                print(f"- {model}: Action={action}, Keybinding=N/A")
        print("\nState Models:")
        for state, models in self.config.state_models.items():
            print(f"- {state}: Models={', '.join(models)}")
        print("\nListen For:")
        for key, value in self.config.listen_for.items():
            print(f"- {key}: {value}")
        print("\nModes:")
        for mode, value in self.config.modes.items():
            print(f"- {mode}: {value}")
        print("\nAvailable Models:")
        for dir_name in ["models-idle", "models-computer", "models-chatty"]:
            if os.path.exists(dir_name):  # noqa: PTH110
                models = [f for f in os.listdir(dir_name) if f.endswith(".onnx")]
                print(f"- {dir_name}: {', '.join(models)}")

    # ------------------------------------------------------------------
    # Interactive helper used in tests

    def interactive_mode(self) -> None:
        while True:
            config_type = input("Enter configuration type (model_action or state_model): ")
            if config_type == "model_action":
                model_name = input("Enter model name: ")
                action = input("Enter action: ")
                self.set_model_action(model_name, action)
            elif config_type == "state_model":
                state = input("Enter state: ")
                models = input("Enter comma-separated model paths: ").split(",")
                self.config.state_models[state] = [m.strip() for m in models]
                self.save_config()
            else:
                print("Invalid type")
                continue
            continue_input = input("Add another? (y/n): ")
            if continue_input.lower() != "y":
                break


__all__ = ["ConfigCLI"]

