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

"""
command_executor.py

Handles the execution of commands in response to recognized voice commands from the models.
This includes executing system commands, sending HTTP requests, and emulating keystrokes.
"""

import requests
import subprocess
import logging
import os

try:
    import pyautogui
except ImportError:
    pyautogui = None
    logging.warning("pyautogui not available. Keybinding commands will be skipped.")
from config import Config


class CommandExecutor:
    def __init__(self, config, model_manager, state_manager):
        self.config = config
        self.model_manager = model_manager
        self.state_manager = state_manager
        logging.info("Command Executor initialized.")

    def execute_command(self, command_name):
        if not self.validate_command(command_name):
            return
        self.pre_execute_hook(command_name)
        command_action = self.config.model_actions.get(command_name)

        # Set default DISPLAY if not set
        if "DISPLAY" not in os.environ:
            os.environ["DISPLAY"] = ":0"

        if "keypress" in command_action:
            if pyautogui:  # Only attempt if pyautogui is available
                self._execute_keybinding(command_name, command_action["keypress"])
            else:
                logging.error(
                    f"Cannot execute keypress command '{command_name}': pyautogui is not installed or available."
                )
                self.report_error(command_name, "pyautogui not available")
        elif "url" in command_action:
            self._execute_url(command_name, command_action["url"])

        self.post_execute_hook(command_name)

    def validate_command(self, command_name):
        command_action = self.config.model_actions.get(command_name)
        if not command_action:
            logging.error(f"No configuration found for command: {command_name}")
            raise ValueError(f"Invalid command: {command_name}")
        return True

    def pre_execute_hook(self, command_name):
        """
        Hook before executing a command.
        """
        logging.info(f"Preparing to execute command: {command_name}")

    def post_execute_hook(self, command_name):
        """
        Hook after executing a command.
        """
        logging.info(f"Completed execution of command: {command_name}")

    def _execute_keybinding(self, command_name, keys):
        """
        Executes a keybinding action using pyautogui to simulate keyboard shortcuts.
        """
        try:
            if isinstance(keys, list):
                pyautogui.hotkey(*keys)
            elif "+" in keys:
                pyautogui.hotkey(*keys.split("+"))
            else:
                pyautogui.press(keys)
            logging.info(f"Executed keybinding for {command_name}: {keys}")
        except Exception as e:
            logging.error(f"Failed to execute keybinding for {command_name}: {e}")
            self.report_error(command_name, str(e))

    def _execute_url(self, command_name, url):
        """
        Sends an HTTP request based on the URL mapped to the command.
        """
        try:
            response = requests.get(url)
            logging.info(f"URL request to {url} returned {response.status_code}")
        except Exception as e:
            logging.error(f"Failed to execute URL request for {command_name}: {e}")

    def report_error(self, command_name, error_message):
        """
        Reports an error to the logging system or an external monitoring service.
        """
        logging.critical(f"Error in {command_name}: {error_message}")


# Example usage:
if __name__ == "__main__":
    executor = CommandExecutor()
    executor.execute_command("screenshot")  # Assuming a command mapped in config
