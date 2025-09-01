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

"""Configuration CLI wizard for ChattyCommander."""

import json
import logging
import os
import sys
from typing import Any

logger = logging.getLogger(__name__)


class Config:
    """Mock config object for testing."""

    def __init__(self, data: dict[str, Any]):
        self.model_actions = data.get("model_actions", {})
        self.state_models = data.get("state_models", {})
        self.listen_for = data.get("listen_for", {})
        self.modes = data.get("modes", {})


class ConfigCLI:
    """Interactive configuration wizard for ChattyCommander."""

    def __init__(self, config_file: str = "config.json") -> None:
        """Initialize the configuration CLI."""
        self.config_file = config_file
        self.config_data: dict[str, Any] = {
            "model_actions": {},
            "state_models": {},
            "listen_for": {},
            "modes": {},
        }
        self.config = Config(self.config_data)

        # Try to load existing config
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file) as f:
                    self.config_data = json.load(f)
                self.config = Config(self.config_data)
            except json.JSONDecodeError as e:
                print(
                    f"Error: Invalid JSON in {self.config_file}: {e}", file=sys.stderr
                )
                # Keep default config
            except Exception as e:
                print(f"Error loading config: {e}", file=sys.stderr)

    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config_data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}", file=sys.stderr)

    def set_model_action(self, action: str, value: str) -> None:
        """Set a model action."""
        if "model_actions" not in self.config_data:
            self.config_data["model_actions"] = {}
        self.config_data["model_actions"][action] = value
        self.config.model_actions[action] = value
        self._save_config()

    def set_state_model(self, state: str, models: str) -> None:
        """Set state models."""
        if "state_models" not in self.config_data:
            self.config_data["state_models"] = {}
        self.config_data["state_models"][state] = models.split(",")
        self.config.state_models[state] = models.split(",")
        self._save_config()

    def set_listen_for(self, param: str, value: str) -> None:
        """Set listen_for parameter."""
        if "listen_for" not in self.config_data:
            self.config_data["listen_for"] = {}
        self.config_data["listen_for"][param] = value
        self.config.listen_for[param] = value
        self._save_config()

    def set_mode(self, mode: str, option: str) -> None:
        """Set mode configuration."""
        if "modes" not in self.config_data:
            self.config_data["modes"] = {}
        self.config_data["modes"][mode] = option
        self.config.modes[mode] = option
        self._save_config()

    def list_config(self) -> None:
        """List current configuration."""
        print("Current Configuration:")
        print(json.dumps(self.config_data, indent=2))

    def interactive_mode(self) -> None:
        """Run interactive configuration mode."""
        print("Interactive Configuration Mode")
        print("Type 'help' for commands, 'quit' to exit")

        while True:
            try:
                cmd = input("> ").strip().lower()
                if cmd == "quit":
                    break
                elif cmd == "help":
                    print("Commands: model_action, state_model, listen_for, mode, quit")
                elif cmd == "model_action":
                    action = input("Action: ").strip()
                    value = input("Value: ").strip()
                    self.set_model_action(action, value)
                    print(f"Set model_action {action} = {value}")
                elif cmd == "state_model":
                    state = input("State: ").strip()
                    models = input("Models (comma-separated): ").strip()
                    self.set_state_model(state, models)
                    print(f"Set state_model {state} = {models}")
                elif cmd == "listen_for":
                    param = input("Parameter: ").strip()
                    value = input("Value: ").strip()
                    self.set_listen_for(param, value)
                    print(f"Set listen_for {param} = {value}")
                elif cmd == "mode":
                    mode = input("Mode: ").strip()
                    option = input("Option: ").strip()
                    self.set_mode(mode, option)
                    print(f"Set mode {mode} = {option}")
                else:
                    print("Unknown command. Type 'help' for commands.")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

    def run_wizard(self) -> None:
        """Run the configuration wizard."""
        logger.info("Configuration wizard started")
        self.interactive_mode()
        logger.info("Configuration wizard completed")


def handle_config_cli(args: Any) -> int:
    """Handle configuration CLI commands."""
    config_cli = ConfigCLI()
    config_cli.run_wizard()
    return 0
