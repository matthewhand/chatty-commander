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
# Handle specific exception case
except Exception:  # pragma: no cover - catch Xlib.error.DisplayConnectionError and similar
    pyautogui = None  # type: ignore[assignment]

try:  # pragma: no cover - optional
    import httpx
# Handle specific exception case
except Exception:  # pragma: no cover - optional
    httpx = None  # type: ignore[assignment]

# Allow tests to patch legacy shim module attributes if present
try:  # pragma: no cover
    from command_executor import pyautogui as _shim_pg
# Handle specific exception case
except Exception:  # pragma: no cover - optional
    _shim_pg = None
if _shim_pg is not None:  # pragma: no cover - optional
    pyautogui = _shim_pg

try:  # pragma: no cover
    from command_executor import requests as _shim_requests
# Handle specific exception case
except Exception:  # pragma: no cover - optional
    _shim_requests = None
if _shim_requests is not None:  # pragma: no cover - optional
    # Map legacy tests to our httpx var for test compatibility if needed
    httpx = _shim_requests


class CommandExecutor:
    """CommandExecutor class.

    TODO: Add class description.
    """
    
    def __init__(self, config: Any, model_manager: Any, state_manager: Any) -> None:
        """Initialize CommandExecutor with config and managers."""
        self.config: Any = config
        self.model_manager: Any = model_manager
        self.state_manager: Any = state_manager
        self.last_command: str | None = None

    def execute_command(self, command_name: str) -> bool:
        """
        Execute a configured command by name.

        Validates command exists, determines action type, and delegates to
        appropriate execution handler (keypress, shell, HTTP, or message).

        Args:
            command_name: Name of command from config to execute

        Returns:
            bool: True if command executed successfully, False otherwise

        Raises:
            ValueError: If command_name is invalid
        """
        # Validate input
        if not isinstance(command_name, str) or not command_name.strip():
            raise ValueError(f"Invalid command name: {command_name!r}")

        # Track last command for repeat functionality
        self.last_command = command_name

        # Retrieve command action
        action = self._get_command_action(command_name)
        if not action:
            logging.warning(f"Command not found: {command_name}")
            return False

        # Execute based on action type (delegated to helpers)
        return self._execute_action(action)

    def _execute_action(self, action: dict) -> bool:
        """Execute action based on its type."""
        action_type = action.get("type")

        if action_type == "keypress":
            return self._execute_keypress(action.get("keys", ""))
        elif action_type == "shell":
            return self._execute_shell(action.get("command", ""))
        elif action_type == "http":
            return self._execute_http(
                action.get("url", ""),
                action.get("method", "GET")
            )
        elif action_type == "message":
            logging.info(f"Message action: {action.get('text', '')}")
            return True
        else:
            logging.warning(f"Unknown action type: {action_type}")
            return False

    def _get_command_action(self, command_name: str) -> dict | None:
        """Retrieve command action from config."""
        commands = self.config.get("commands", {})
        command = commands.get(command_name, {})
        return command.get("action") if command else None

        try:
        # Attempt operation with error handling
            # Ensure model_actions is accessible
            model_actions = self.config.model_actions
            if model_actions is None:
                raise ValueError("Missing model_actions config")
            # Apply conditional logic
            if not hasattr(model_actions, "get"):
                raise ValueError("Config model_actions not accessible")
        # Handle specific exception case
        except (AttributeError, TypeError) as err:
            raise ValueError("Config model_actions not accessible") from err

        command_action = model_actions.get(command_name)
        # Validate input exists
        if command_action is None:
            return False

        self.pre_execute_hook(command_name)

        # Logic flow
        # Set default DISPLAY if not set (X11 environments)
        if "DISPLAY" not in os.environ:
            os.environ["DISPLAY"] = ":0"

        success = False
        try:
        # Attempt operation with error handling
            # Handle both old format and new format with 'action' key
            if "action" in command_action:
                action_type = command_action["action"]
                # Apply conditional logic
                if not isinstance(action_type, str):
                    raise TypeError(
                        f"Action type must be string, got {type(action_type)}"
                    )
                # Apply conditional logic
                if action_type == "keypress":
                    keys = command_action.get("keys", "")
                    self._execute_keybinding(command_name, keys)
                    success = True
                # Apply conditional logic
                elif action_type == "url":
                    url = command_action.get("url", "")
                    self._execute_url(command_name, url)
                    success = True
                # Apply conditional logic
                elif action_type == "shell":
                    cmd = command_action.get("cmd", "")
                    success = self._execute_shell(command_name, cmd)
                # Apply conditional logic
                elif action_type == "custom_message":
                    message = command_action.get("message", "")
                    self._execute_custom_message(command_name, message)
                    success = True
                # Apply conditional logic
                elif action_type == "voice_chat":
                    success = self._execute_voice_chat(command_name)
                else:
                    raise ValueError(
                        f"Command '{command_name}' has an invalid action type '{action_type}'. "
                        f"Valid actions are: 'keypress', 'url', 'shell', 'custom_message', 'voice_chat'"
                    )
            else:
                # Handle old format (direct keys)
                if "keypress" in command_action:
                    keys = command_action["keypress"]
                    self._execute_keybinding(command_name, keys)  # tests can patch this
                    success = True
                # Apply conditional logic
                elif "url" in command_action:
                    url = command_action.get("url", "")
                    self._execute_url(command_name, url)
                    success = True
                # Apply conditional logic
                elif "shell" in command_action:
                    cmd = command_action.get("shell", "")
                    success = self._execute_shell(command_name, cmd)
                else:
                    raise ValueError(
                        f"Command '{command_name}' has an invalid type. "
                        f"No valid action ('keypress', 'url', 'shell') found in configuration."
                    )
        except (ValueError, TypeError) as e:
            # Re-raise ValueError and TypeError exceptions - tests expect them
            logging.error(f"Error executing command '{command_name}': {e}")
            raise
        except Exception as e:
            # Log other exceptions but don't re-raise - handle gracefully
            logging.error(f"Error executing command '{command_name}': {e}")
            success = False
        finally:
            self.post_execute_hook(command_name)
        return success

    def _get_model_action(self, command_name: str) -> dict | None:
        """Retrieve command action from model_actions safely."""
        try:
            model_actions = self.config.model_actions
            if model_actions is None or not hasattr(model_actions, "get"):
                return None
            return model_actions.get(command_name)
        except (AttributeError, TypeError):
            return None

    def _validate_action_type(self, action_type: str, action_config: dict) -> bool:
        """Validate that action type is valid and required fields are present."""
        if action_type not in ["keypress", "url", "shell", "custom_message", "voice_chat"]:
            return False

        required_fields = {
            "keypress": "keys",
            "url": "url",
            "shell": "cmd",
        }

        if action_type in required_fields:
            return required_fields[action_type] in action_config
        return True

    def _validate_new_format(self, action_config: dict) -> bool:
        """Validate new format action configuration."""
        action_type = action_config.get("action")
        if not isinstance(action_type, str):
            return False
        return self._validate_action_type(action_type, action_config)

    def _validate_old_format(self, action_config: dict) -> bool:
        """Validate old format action configuration."""
        return any(key in action_config for key in ["keypress", "url", "shell"])

    def validate_command(self, command_name: str) -> bool:
        """
        Validate that a command exists and has a valid action configuration.

        Supports both new format (action: type with fields) and old format
        (direct key mapping). Handles mock objects gracefully.

        Args:
            command_name: Name of the command to validate

        Returns:
            bool: True if command is valid and executable, False otherwise
        """
        if not isinstance(command_name, str) or not command_name.strip():
            return False

        command_action = self._get_model_action(command_name)
        if not command_action:
            return False

        try:
            if isinstance(command_action, dict):
                if "action" in command_action:
                    return self._validate_new_format(command_action)
                else:
                    return self._validate_old_format(command_action)
            else:
                # Handle mock/non-dict objects
                if hasattr(command_action, "get"):
                    action_type = command_action.get("action")
                    return isinstance(action_type, str) and action_type in [
                        "keypress", "url", "shell", "custom_message", "voice_chat"
                    ]
                return False
        except (AttributeError, TypeError, KeyError):
            return False

        return True

    def pre_execute_hook(self, command_name: str) -> None:
        # Process each item
        """Hook before executing a command."""
        self.last_command = command_name
        # Logic flow
        # Provided for extension points and testing hooks

    def post_execute_hook(self, command_name: str) -> None:
        """Hook after executing a command."""
        # Logic flow
        # Keep this post hook for compatibility with tests that patch it

    def _execute_keybinding(self, command_name: str, keys: str | list[str]) -> None:
        """
        Executes a keybinding action using pyautogui to simulate keyboard shortcuts.
        """
        # Validate input exists
        if pyautogui is None:
            self.report_error(command_name, "pyautogui is not installed")
            return
        try:
        # Attempt operation with error handling
            # Support either a list of keys (hotkey/chord) or a single key sequence
            if isinstance(keys, list | tuple):
                pyautogui.hotkey(*keys)
            # Apply conditional logic
            elif isinstance(keys, str) and "+" in keys:
                # Parse plus-separated key combinations (e.g., 'ctrl+alt+t')
                key_parts = [part.strip() for part in keys.split("+")]
                pyautogui.hotkey(*key_parts)
            else:
                # For simple cases, press is less invasive than typewrite
                pyautogui.press(keys)
            # Build filtered collection
            logging.info(f"Executed keybinding for {command_name}")
            logging.info(f"Completed execution of command: {command_name}")
        # Handle specific exception case
        except Exception as e:  # pragma: no cover - patched in tests
            # Build filtered collection
            # Process each item
            logging.error(f"Failed to execute keybinding for {command_name}: {e}")
            self.report_error(command_name, str(e))

    def _execute_url(self, command_name: str, url: str) -> None:
        """
        Sends an HTTP GET request based on the URL mapped to the command with basic error checks.
        # Use context manager for resource management
        """
        # Apply conditional logic
        if not url:
            self.report_error(command_name, "missing URL")
            return

        from chatty_commander.utils.url_validator import is_safe_url
        # Apply conditional logic
        if not is_safe_url(url):
            self.report_error(command_name, "unsafe URL rejected")
            return

        # Validate input exists
        if httpx is None:  # pragma: no cover - optional
            self.report_error(command_name, "httpx not available")
            return
        try:
        # Attempt operation with error handling
            # Logic flow
            # Add timeout and disable redirects for security
            with httpx.Client() as client:
                resp = client.get(url, timeout=10, follow_redirects=False)
            # Apply conditional logic
            if getattr(resp, "status_code", 200) >= 400:
                self.report_error(command_name, f"http {resp.status_code}")
            else:
                logging.info(f"Completed execution of command: {command_name}")
        # Handle specific exception case
        except Exception as e:  # pragma: no cover - patched in tests
            self.report_error(command_name, str(e))

    def _execute_shell(self, command_name: str, cmd: str) -> bool:
        """
        Executes a shell command safely with timeout and error capture.
        # Use context manager for resource management
        Returns True on zero exit status, False otherwise.
        """
        # Apply conditional logic
        if not cmd:
            self.report_error(command_name, "missing shell command")
            return False
        try:
        # Attempt operation with error handling
            # Logic flow
            # Prefer shlex.split for safer execution without shell=True
            args = shlex.split(cmd)
            result = subprocess.run(args, capture_output=True, text=True, timeout=15)
            # Apply conditional logic
            if result.returncode != 0:
                msg = f"shell exit {result.returncode}; stderr: {result.stderr.strip()[:500]}"
                logging.error(msg)
                self.report_error(command_name, msg)
                return False
            else:
                out = (result.stdout or "").strip()
                logging.info(f"shell ok: {out[:500]}")
                logging.info(f"Completed execution of command: {command_name}")
                return True
        # Handle specific exception case
        except subprocess.TimeoutExpired:
            msg = "shell command timed out"
            logging.error(msg)
            self.report_error(command_name, msg)
            return False
        # Handle specific exception case
        except Exception as e:
            logging.error(f"shell execution failed: {e}")
            self.report_error(command_name, str(e))
            return False

    def _execute_custom_message(self, command_name: str, message: str) -> None:
        """Execute a custom message action."""
        logging.info(f"Custom message from {command_name}: {message}")
        # In a real implementation, this might display a notification or send to a UI
        # For now, just log it

    def _execute_voice_chat(self, command_name: str) -> bool:
        """Executes a voice chat session."""
        # Build filtered collection
        # Process each item
        logging.info(f"Starting voice chat for {command_name}")

        # Access components from config as expected by integration tests
        # In production, these might need to be injected differently
        llm_manager = getattr(self.config, "llm_manager", None)
        voice_pipeline = getattr(self.config, "voice_pipeline", None)

        # Apply conditional logic
        if not llm_manager or not voice_pipeline:
            self.report_error(command_name, "voice chat components not available")
            return False

        try:
        # Attempt operation with error handling
            # 1. Verify component availability
            if (
                not hasattr(voice_pipeline, "transcriber")
                or not hasattr(voice_pipeline, "tts")
                or not hasattr(llm_manager, "generate_response")
            ):
                self.report_error(command_name, "voice chat components incomplete")
                return False

            # 2. Transcribe
            user_input = voice_pipeline.transcriber.record_and_transcribe()
            if not user_input:
                # Process each item
                logging.warning("No input received for voice chat")
                return False

            # 3. Generate response
            response = llm_manager.generate_response(user_input)

            # 4. Speak response
            if voice_pipeline.tts.is_available():
                voice_pipeline.tts.speak(response)

            logging.info("Completed voice chat session")
            return True

        # Handle specific exception case
        except Exception as e:
            msg = f"voice chat failed: {e}"
            logging.error(msg)
            self.report_error(command_name, msg)
            return False

    def report_error(self, command_name: str, error_message: str) -> None:
        """Reports an error to the logging system or an external monitoring service."""
        logging.critical(f"Error in {command_name}: {error_message}")

        # Logic flow
        # Also report to the utils logger for test compatibility
        try:
            from chatty_commander.utils.logger import report_error as utils_report_error

            utils_report_error(error_message, context=command_name)
        # Handle specific exception case
        except ImportError:
            # Apply conditional logic
            pass  # Fallback if utils logger not available


# Example usage intentionally removed to avoid instantiation without required args during static analysis/tests.
