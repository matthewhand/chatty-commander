"""
command_executor.py

This module executes the actions associated with voice commands detected by the ChattyCommander application.
It interacts with system utilities, web requests, and simulates keyboard inputs based on command specifications.
"""

import requests
import subprocess
import logging

class CommandExecutor:
    def __init__(self, config):
        self.config = config

    def execute_command(self, command, model_name):
        """Execute the action associated with a detected voice command."""
        if command in self.config.url_commands:
            self.execute_url(command)
        elif command in self.config.keypress_commands:
            self.execute_keypress(command)
        elif command in self.config.system_commands:
            self.execute_system_command(command)

    def execute_url(self, command):
        """Make an HTTP request to the URL associated with the command."""
        url = self.config.url_commands[command]
        headers = {'Authorization': f'Bearer {self.config.auth_token}'} if self.config.auth_token else {}
        response = requests.get(url, headers=headers)
        logging.info(f"Executed URL command {command}: {response.status_code}")

    def execute_keypress(self, command):
        """Simulate keypresses associated with the command."""
        keys = self.config.keypress_commands[command]
        try:
            import pyautogui
            if isinstance(keys, list):
                pyautogui.hotkey(*keys)
            else:
                pyautogui.press(keys)
        except Exception as e:
            logging.error(f"Could not execute keypress: {e}")
        logging.info(f"Executed keypress for {command}: {'+'.join(keys) if isinstance(keys, list) else keys}")

    def execute_system_command(self, command):
        """Execute system-specific commands like taking screenshots or running shell commands."""
        try:
            import pyautogui
            if command == 'take_screenshot':
                pyautogui.screenshot().save(self.config.screenshot_save_path)
                logging.info("Screenshot taken and saved.")
            elif command == 'start_run':
                subprocess.run(['start', 'run'], shell=True)
                logging.info("Run dialog opened.")
            elif command == 'cycle_window':
                pyautogui.hotkey('alt', 'tab')
                logging.info("Window cycled.")
            elif command == 'send_newline':
                pyautogui.press('enter')
                logging.info("Newline sent.")
        except Exception as e:
            logging.error(f"Could not execute system command: {e}")
        
        if command == 'wax_poetic':
            # Placeholder for a chatbot endpoint call
            logging.info("Wax poetic command triggered.")

    def __repr__(self):
        return f"<CommandExecutor(url_commands={len(self.config.url_commands)}, keypress_commands={len(self.config.keypress_commands)}, system_commands={len(self.config.system_commands)})>"
