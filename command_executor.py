"""
command_executor.py

Handles the execution of commands in response to recognized voice commands from the models.
This includes executing system commands, sending HTTP requests, and emulating keystrokes.
"""

import pyautogui
import requests
import subprocess
import logging
from config import Config

class CommandExecutor:
    def __init__(self):
        self.config = Config()
        logging.info("Command Executor initialized.")

    def execute_command(self, command_name):
        if not self.validate_command(command_name):
            return
        self.pre_execute_hook(command_name)
        command_action = self.config.model_actions.get(command_name)

        if 'keypress' in command_action:
            self._execute_keybinding(command_name, command_action['keypress'])
        elif 'url' in command_action:
            self._execute_url(command_name, command_action['url'])

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
            if '+' in keys:
                pyautogui.hotkey(*keys.split('+'))
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
    executor.execute_command('screenshot')  # Assuming a command mapped in config
