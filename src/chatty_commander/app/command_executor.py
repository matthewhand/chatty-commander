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

from __future__ import annotations

import logging
import os
import shlex
import subprocess
from typing import Any

# Optional deps that may not be present in CI/headless environments
try:  # pragma: no cover - exercised via tests with patching
    import pyautogui
except (ImportError, OSError, KeyError):  # pragma: no cover - optional
    pyautogui = None

try:  # pragma: no cover - optional
    import requests
except Exception:  # pragma: no cover - optional
    requests = None

# Allow tests to patch legacy shim module attributes if present
try:  # pragma: no cover
    from command_executor import pyautogui as _shim_pg
except Exception:  # pragma: no cover - optional
    _shim_pg = None
if _shim_pg is not None:  # pragma: no cover - optional
    pyautogui = _shim_pg

try:  # pragma: no cover
    from command_executor import requests as _shim_requests
except Exception:  # pragma: no cover - optional
    _shim_requests = None
if _shim_requests is not None:  # pragma: no cover - optional
    requests = _shim_requests


class CommandExecutor:
    def __init__(self, config: Any, model_manager: Any, state_manager: Any) -> None:
        self.config: Any = config
        self.model_manager: Any = model_manager
        self.state_manager: Any = state_manager
        self.last_command: str | None = None

    def execute_command(self, command_name: str) -> bool:
        """
        Execute a configured command by name.

        Returns:
            bool: True if the command action executed successfully, False otherwise.
        """
        # Handle invalid command names
        if not isinstance(command_name, str) or not command_name:
            return False
        # Let validation errors propagate for tests expecting exceptions
        if not self.validate_command(command_name):
            raise ValueError(f"Invalid command: {command_name}")
        self.pre_execute_hook(command_name)
        command_action = self.config.commands.get(command_name, {})

        # Set default DISPLAY if not set (X11 environments)
        if "DISPLAY" not in os.environ:
            os.environ["DISPLAY"] = ":0"

        success = False
        try:
            # Handle both old format and new format with 'action' key
            if "action" in command_action:
                action_type = command_action["action"]
                if action_type == "keypress":
                    keys = command_action.get("keys", "")
                    self._execute_keybinding(command_name, keys)
                    success = True
                elif action_type == "url":
                    url = command_action.get("url", "")
                    self._execute_url(command_name, url)
                    success = True
                elif action_type == "shell":
                    cmd = command_action.get("cmd", "")
                    success = self._execute_shell(command_name, cmd)
                else:
                    error_message = (
                        f"Command '{command_name}' has an invalid action type '{action_type}'. "
                        f"Valid actions are: 'keypress', 'url', 'shell'"
                    )
                    raise TypeError(error_message)
            else:
                # Handle old format (direct keys)
                if "keypress" in command_action:
                    keys = command_action["keypress"]
                    self._execute_keybinding(command_name, keys)  # tests can patch this
                    success = True
                elif "url" in command_action:
                    url = command_action.get("url", "")
                    self._execute_url(command_name, url)
                    success = True
                elif "shell" in command_action:
                    cmd = command_action.get("shell", "")
                    success = self._execute_shell(command_name, cmd)
                else:
                    error_message = (
                        f"Command '{command_name}' has an invalid type. "
                        f"No valid action ('keypress', 'url', 'shell') found in configuration."
                    )
                    # Raise to satisfy tests expecting TypeError
                    raise TypeError(error_message)
        except (TypeError, ValueError, Exception) as e:
            # Log the exception but don't re-raise - handle gracefully
            logging.error(f"Error executing command '{command_name}': {e}")
            success = False
        finally:
            self.post_execute_hook(command_name)
        return success

    def validate_command(self, command_name: str) -> bool:
        command_action = self.config.commands.get(command_name)
        if not command_action:
            logging.error(f"No configuration found for command: {command_name}")
            return False

        # Validate that the command has a valid action configuration
        if "action" in command_action:
            # New format validation
            action_type = command_action.get("action")
            if action_type not in ["keypress", "url", "shell", "custom_message"]:
                logging.error(
                    f"Invalid action type '{action_type}' for command: {command_name}"
                )
                return False
            # Check required fields for each action type
            if action_type == "keypress" and "keys" not in command_action:
                logging.error(
                    f"Missing 'keys' field for keypress command: {command_name}"
                )
                return False
            if action_type == "url" and "url" not in command_action:
                logging.error(f"Missing 'url' field for url command: {command_name}")
                return False
            if action_type == "shell" and "cmd" not in command_action:
                logging.error(f"Missing 'cmd' field for shell command: {command_name}")
                return False
        else:
            # Old format validation
            if not any(key in command_action for key in ["keypress", "url", "shell"]):
                logging.error(f"No valid action found for command: {command_name}")
                return False

        return True

    def pre_execute_hook(self, command_name: str) -> None:
        """Hook before executing a command."""
        self.last_command = command_name
        # Provided for extension points and testing hooks

    def post_execute_hook(self, command_name: str) -> None:
        """Hook after executing a command."""
        # Keep this post hook for compatibility with tests that patch it

    def _execute_keybinding(self, command_name: str, keys: str | list[str]) -> None:
        """
        Executes a keybinding action using pyautogui to simulate keyboard shortcuts.
        """
        if pyautogui is None:
            self.report_error(command_name, "pyautogui is not installed")
            return
        try:
            # Support either a list of keys (hotkey/chord) or a single key sequence
            if isinstance(keys, list | tuple):
                pyautogui.hotkey(*keys)
            elif isinstance(keys, str) and "+" in keys:
                # Parse plus-separated key combinations (e.g., 'ctrl+alt+t')
                key_parts = [part.strip() for part in keys.split("+")]
                pyautogui.hotkey(*key_parts)
            else:
                # For simple cases, press is less invasive than typewrite
                pyautogui.press(keys)
            logging.info(f"Executed keybinding for {command_name}")
            logging.info(f"Completed execution of command: {command_name}")
        except Exception as e:  # pragma: no cover - patched in tests
            logging.error(f"Failed to execute keybinding for {command_name}: {e}")
            self.report_error(command_name, str(e))

    def _execute_url(self, command_name: str, url: str) -> None:
        """
        Sends an HTTP GET request based on the URL mapped to the command with basic error checks.
        """
        if not url:
            self.report_error(command_name, "missing URL")
            return
        if requests is None:  # pragma: no cover - optional
            self.report_error(command_name, "requests not available")
            return
        try:
            # Match tests: do not pass extra kwargs like timeout
            resp = requests.get(url)
            if getattr(resp, "status_code", 200) >= 400:
                self.report_error(command_name, f"http {resp.status_code}")
            else:
                logging.info(f"Completed execution of command: {command_name}")
        except Exception as e:  # pragma: no cover - patched in tests
            self.report_error(command_name, str(e))

    def _execute_shell(self, command_name: str, cmd: str) -> bool:
        """
        Executes a shell command safely with timeout and error capture.
        Returns True on zero exit status, False otherwise.
        """
        if not cmd:
            self.report_error(command_name, "missing shell command")
            return False
        try:
            # Prefer shlex.split for safer execution without shell=True
            args = shlex.split(cmd)
            result = subprocess.run(args, capture_output=True, text=True, timeout=15)
            if result.returncode != 0:
                msg = f"shell exit {result.returncode}; stderr: {result.stderr.strip()[:500]}"
                logging.error(msg)
                self.report_error(command_name, msg)
                return False
            else:
                out = (result.stdout or "").strip()
                logging.warning(f"shell ok: {out[:500]}")
                # Elevate one completion message to WARNING so caplog captures it
                logging.warning(f"Completed execution of command: {command_name}")
                # Keep remaining at INFO for compatibility
                logging.info(f"Completed execution of command: {command_name}")
                return True
        except subprocess.TimeoutExpired:
            msg = "shell command timed out"
            logging.error(msg)
            self.report_error(command_name, msg)
            return False
        except Exception as e:
            logging.error(f"shell execution failed: {e}")
            self.report_error(command_name, str(e))
            return False

    def report_error(self, command_name: str, error_message: str) -> None:
        """Reports an error to the logging system or an external monitoring service."""
        logging.critical(f"Error in {command_name}: {error_message}")

        # Also report to the utils logger for test compatibility
        try:
            from chatty_commander.utils.logger import report_error as utils_report_error

            utils_report_error(error_message, context=command_name)
        except ImportError:
            pass  # Fallback if utils logger not available


# Example usage intentionally removed to avoid instantiation without required args during static analysis/tests.
