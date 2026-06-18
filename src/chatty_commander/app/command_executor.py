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
except Exception:  # pragma: no cover - catch Xlib.error.DisplayConnectionError and similar
    pyautogui = None  # type: ignore[assignment]

try:  # pragma: no cover - optional
    import httpx
except Exception:  # pragma: no cover - optional
    httpx = None  # type: ignore[assignment]

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
    # Map legacy tests to our httpx var for test compatibility if needed
    httpx = _shim_requests


class CommandExecutor:
    """CommandExecutor handles execution of configured commands (keypress, shell, url, etc.)."""

    def __init__(self, config: Any, model_manager: Any, state_manager: Any) -> None:
        self.config: Any = config
        self.model_manager: Any = model_manager
        self.state_manager: Any = state_manager
        self.last_command: str | None = None

    def _get_command_action(self, command_name: str) -> Any:
        """Get command action from config, with validation.
        Extracted from execute_command to reduce complexity (addresses qa rank 3 _get_command_action).
        Preserves all error raising and behavior.
        """
        try:
            model_actions = self.config.model_actions
            if model_actions is None:
                raise ValueError("Missing model_actions config")
            if not hasattr(model_actions, "get"):
                raise ValueError("Config model_actions not accessible")
        except (AttributeError, TypeError) as err:
            raise ValueError("Config model_actions not accessible") from err
        return model_actions.get(command_name)

    def _get_action_safely(self, command_name: str) -> Any | None:
        """Safe fetch of command action (returns None on bad/missing config or action).

        Small helper extracted from validate_command (qa rank 4 complexity hotspot)
        to reduce duplication with _get_command_action while preserving exact
        tolerant behavior (no raises, just False path in validate).
        """
        try:
            model_actions = self.config.model_actions
            if model_actions is None:
                return None
            if not hasattr(model_actions, "get"):
                return None
            return model_actions.get(command_name)
        except (AttributeError, TypeError):
            return None

    def execute_command(self, command_name: str) -> bool:
        """
        Execute a configured command by name.

        Returns:
            bool: True if the command action executed successfully, False otherwise.
        """
        command_action = self._get_command_action(command_name)
        if command_action is None:
            return False

        self.pre_execute_hook(command_name)

        if "DISPLAY" not in os.environ:
            os.environ["DISPLAY"] = ":0"

        success = False
        try:
            if "action" in command_action:
                success = self._execute_new_format(command_name, command_action)
            else:
                success = self._execute_old_format(command_name, command_action)
        except (ValueError, TypeError) as e:
            logging.error(f"Error executing command '{command_name}': {e}")
            raise
        except Exception as e:
            logging.error(f"Error executing command '{command_name}': {e}")
            success = False
        finally:
            self.post_execute_hook(command_name)
        return success

    def _execute_new_format(self, command_name: str, command_action: dict) -> bool:
        """Dispatch for the modern {'action': '...', ...} format."""
        action_type = command_action["action"]
        if not isinstance(action_type, str):
            raise TypeError(f"Action type must be string, got {type(action_type)}")
        if action_type == "keypress":
            keys = command_action.get("keys", "")
            self._execute_keybinding(command_name, keys)
            return True
        elif action_type == "url":
            url = command_action.get("url", "")
            self._execute_url(command_name, url)
            return True
        elif action_type == "shell":
            cmd = command_action.get("cmd", "")
            return self._execute_shell(command_name, cmd)
        elif action_type == "custom_message":
            message = command_action.get("message", "")
            return self._execute_custom_message_action(command_name, message)
        elif action_type == "voice_chat":
            return self._execute_voice_chat_action(command_name)
        elif action_type == "dograh_call":
            return self._execute_dograh_call(command_name, command_action)
        else:
            raise ValueError(
                f"Command '{command_name}' has an invalid action type '{action_type}'. "
                f"Valid actions are: 'keypress', 'url', 'shell', 'custom_message', 'voice_chat', 'dograh_call'"
            )

    def _execute_custom_message_action(self, command_name: str, message: str) -> bool:
        """Small helper extracted from _execute_new_format (qa rank3 complexity hotspot)."""
        self._execute_custom_message(command_name, message)
        return True

    def _execute_voice_chat_action(self, command_name: str) -> bool:
        """Small helper extracted from _execute_new_format (qa rank3 complexity hotspot)."""
        return self._execute_voice_chat(command_name)

    def _execute_old_format(self, command_name: str, command_action: dict) -> bool:
        """Dispatch for the legacy direct-key format (e.g. {'keypress': ...})."""
        if "keypress" in command_action:
            keys = command_action["keypress"]
            self._execute_keybinding(command_name, keys)
            return True
        elif "url" in command_action:
            url = command_action.get("url", "")
            self._execute_url(command_name, url)
            return True
        elif "shell" in command_action:
            cmd = command_action.get("shell", "")
            return self._execute_shell(command_name, cmd)
        else:
            raise ValueError(
                f"Command '{command_name}' has an invalid type. "
                f"No valid action ('keypress', 'url', 'shell') found in configuration."
            )

    def _is_valid_action_type(self, action_type: Any) -> bool:
        """Return True if the action type string is one of the supported values (including dograh_call)."""
        if not isinstance(action_type, str):
            return False
        return action_type in [
            "keypress",
            "url",
            "shell",
            "custom_message",
            "voice_chat",
            "dograh_call",
        ]

    def _validate_action_fields(self, command_action: dict, action_type: str) -> bool:
        """Return True if all required fields for the action type are present."""
        if action_type == "keypress":
            return "keys" in command_action
        if action_type == "url":
            return "url" in command_action
        if action_type == "shell":
            return "cmd" in command_action
        # custom_message and voice_chat require no additional mandatory fields
        return True

    def _validate_new_format_action(self, command_action: dict) -> bool:
        """Validate new-format {'action': ..., ...} command_action dict."""
        action_type = command_action.get("action")
        if not self._is_valid_action_type(action_type):
            return False
        return self._validate_action_fields(command_action, str(action_type))

    def _validate_old_format_action(self, command_action: dict) -> bool:
        """Validate legacy direct-key format (contains at least one of keypress/url/shell)."""
        return any(key in command_action for key in ["keypress", "url", "shell"])

    def _validate_non_dict_action(self, command_action: Any) -> bool:
        """Handle mock/non-dict action objects (return True only for valid action_type via .get)."""
        if hasattr(command_action, "get"):
            action_type = command_action.get("action")
            if self._is_valid_action_type(action_type):
                return True
        return False

    def _validate_dograh_workflow_if_needed(self, command_action: dict) -> bool:
        """Return False only if dograh_call action is missing the required workflow_id field."""
        action_type = command_action.get("action")
        if action_type == "dograh_call" and "workflow_id" not in command_action:
            return False
        return True

    def validate_command(self, command_name: str) -> bool:
        if not isinstance(command_name, str) or not command_name.strip():
            return False

        command_action = self._get_action_safely(command_name)
        if not command_action:
            return False

        try:
            if isinstance(command_action, dict):
                if "action" in command_action:
                    # New format validation - delegates to extracted helper
                    if not self._validate_new_format_action(command_action):
                        return False
                    if not self._validate_dograh_workflow_if_needed(command_action):
                        return False
                else:
                    # Old format validation - use extracted helper
                    if not self._validate_old_format_action(command_action):
                        return False
            else:
                # For mocks or non-dict - use extracted helper
                if not self._validate_non_dict_action(command_action):
                    return False
        except (AttributeError, TypeError, KeyError):
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
            self._perform_key_action(keys)
            logging.info(f"Executed keybinding for {command_name}")
            logging.info(f"Completed execution of command: {command_name}")
        except Exception as e:  # pragma: no cover - patched in tests
            logging.error(f"Failed to execute keybinding for {command_name}: {e}")
            self.report_error(command_name, str(e))

    def _perform_key_action(self, keys: str | list[str]) -> None:
        """Pure helper extracted from _execute_keybinding.

        Handles list/tuple (hotkey), '+'-separated strings (e.g. ctrl+alt+t), or simple key press.
        Extracted to reduce complexity in the keybinding executor (addresses qa listed
        command_executor complexity hotspots) while preserving exact behavior.
        """
        if isinstance(keys, list | tuple):
            pyautogui.hotkey(*keys)
        elif isinstance(keys, str) and "+" in keys:
            key_parts = [part.strip() for part in keys.split("+")]
            pyautogui.hotkey(*key_parts)
        else:
            pyautogui.press(keys)

    def _execute_url(self, command_name: str, url: str) -> None:
        """
        Sends an HTTP GET request based on the URL mapped to the command with basic error checks.
        """
        if not url:
            self.report_error(command_name, "missing URL")
            return

        from chatty_commander.utils.url_validator import is_safe_url
        if not is_safe_url(url):
            self.report_error(command_name, "unsafe URL rejected")
            return

        if httpx is None:  # pragma: no cover - optional
            self.report_error(command_name, "httpx not available")
            return
        try:
            # Add timeout and disable redirects for security
            with httpx.Client() as client:
                resp = client.get(url, timeout=10, follow_redirects=False)
            if getattr(resp, "status_code", 200) >= 400:
                self.report_error(command_name, f"http {resp.status_code}")
            else:
                logging.info(f"Completed execution of command: {command_name}")
        except Exception as e:  # pragma: no cover - patched in tests
            self.report_error(command_name, str(e))

    def _run_shell_process(self, cmd: str) -> tuple[subprocess.CompletedProcess | None, str | None]:
        """Small pure helper extracted from _execute_shell (addresses qa-listed complexity).
        Runs shlex+subprocess with fixed safety params; returns (result, error_msg or None).
        """
        if not cmd:
            return None, "missing shell command"
        try:
            args = shlex.split(cmd)
            result = subprocess.run(args, capture_output=True, text=True, timeout=15)
            return result, None
        except subprocess.TimeoutExpired:
            return None, "shell command timed out"
        except Exception as e:
            return None, str(e)

    def _execute_shell(self, command_name: str, cmd: str) -> bool:
        """
        Executes a shell command safely with timeout and error capture.
        Returns True on zero exit status, False otherwise.
        """
        result, err = self._run_shell_process(cmd)
        if err is not None or result is None:
            msg = err or "shell execution produced no result"
            if msg == "missing shell command":
                self.report_error(command_name, msg)
            else:
                logging.error(f"shell execution failed: {msg}")
                self.report_error(command_name, msg)
            return False
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

    def _validate_dograh_call_params(
        self, command_name: str, action: dict[str, Any]
    ) -> tuple[int | None, str | None, int | None]:
        """Thin helper extracted from _execute_dograh_call to lower complexity (qa target).
        Returns (workflow_id, phone, telephony_id) or (None, None, None) after reporting error.
        Preserves exact error messages and return False path.
        """
        workflow_id = action.get("workflow_id")
        if not isinstance(workflow_id, int):
            self.report_error(command_name, "dograh_call missing integer workflow_id")
            return None, None, None
        phone_number = action.get("phone_number")
        telephony_configuration_id = action.get("telephony_configuration_id")
        return workflow_id, phone_number, telephony_configuration_id

    def _initiate_dograh_call(
        self, workflow_id: int, phone_number: str | None, telephony_configuration_id: int | None
    ) -> tuple[bool, Any | None, str | None]:
        """Thin helper extracted from _execute_dograh_call: import + initiate.
        Returns (success, result_or_None, error_msg_or_None). Exact error strings preserved.
        """
        try:
            from chatty_commander.integrations.dograh_client import (
                DograhClient,
                DograhError,
            )
        except ImportError as e:
            return False, None, f"dograh integration import failed: {e}"

        try:
            with DograhClient() as client:
                result = client.initiate_call(
                    workflow_id,
                    phone_number=phone_number,
                    telephony_configuration_id=telephony_configuration_id,
                )
            return True, result, None
        except DograhError as e:
            return False, None, f"dograh unavailable: {e}"
        except Exception as e:
            return False, None, f"dograh call failed: {e}"

    def _execute_dograh_call(self, command_name: str, action: dict[str, Any]) -> bool:
        """Place an outbound phone call via a Dograh telephony workflow.

        Expected action shape::

            {"action": "dograh_call",
             "workflow_id": 42,
             "phone_number": "+15555550100",            # optional
             "telephony_configuration_id": 7}           # optional

        Requires ``DOGRAH_BASE_URL`` and ``DOGRAH_API_KEY`` env vars; if either
        is missing the command fails gracefully via ``report_error`` so CC
        continues running without the dograh overlay.
        """
        workflow_id, phone_number, telephony_configuration_id = self._validate_dograh_call_params(
            command_name, action
        )
        if workflow_id is None:
            return False

        success, result, error_msg = self._initiate_dograh_call(
            workflow_id, phone_number, telephony_configuration_id
        )
        if not success:
            self.report_error(command_name, error_msg or "dograh call failed")
            return False

        logging.info(f"dograh_call ok: workflow {workflow_id} result={result}")

        # Auto-start the call-state poller so the dashboard CallStateBadge
        # lights up without a manual /track. This is a no-op unless a web
        # server has registered its event loop; it never raises or blocks.
        self._request_dograh_call_state_start(workflow_id, result)

        logging.info(f"Completed execution of command: {command_name}")
        return True

    @staticmethod
    def _request_dograh_call_state_start(workflow_id: int, result: Any) -> None:
        """Best-effort auto-start of the dograh call-state poller.

        Extracts the run id from the initiate_call result and asks the
        process-wide poller registry to start polling. Safe no-op when no
        web server is running. Never raises (the call already succeeded).
        """
        try:
            from chatty_commander.integrations.dograh_call_state import (
                extract_run_id,
                get_poller_registry,
            )

            run_id = extract_run_id(result if isinstance(result, dict) else {})
            if run_id is None:
                logging.debug(
                    "dograh_call: no run id in initiate_call result; "
                    "skipping call-state auto-start"
                )
                return
            get_poller_registry().request_start(workflow_id, run_id)
        except Exception as exc:  # noqa: BLE001 - never crash a successful call
            logging.debug("dograh call-state auto-start failed: %s", exc)

    def _execute_custom_message(self, command_name: str, message: str) -> None:
        """Execute a custom message action."""
        logging.info(f"Custom message from {command_name}: {message}")
        # In a real implementation, this might display a notification or send to a UI
        # For now, just log it

    def _verify_voice_chat_components(self, command_name: str, llm_manager: Any, voice_pipeline: Any) -> bool:
        """Thin helper extracted from _execute_voice_chat (qa target complexity).
        Returns False and reports error on missing/incomplete components.
        """
        if not llm_manager or not voice_pipeline:
            self.report_error(command_name, "voice chat components not available")
            return False
        if (
            not hasattr(voice_pipeline, "transcriber")
            or not hasattr(voice_pipeline, "tts")
            or not hasattr(llm_manager, "generate_response")
        ):
            self.report_error(command_name, "voice chat components incomplete")
            return False
        return True

    def _perform_voice_chat_flow(self, llm_manager: Any, voice_pipeline: Any) -> bool:
        """Transcribe + LLM generate + optional TTS speak.

        Extracted from _execute_voice_chat (one helper to reduce its length/complexity
        per qa command_executor hotspot while preserving exact logs, returns and paths).
        """
        # 2. Transcribe
        user_input = voice_pipeline.transcriber.record_and_transcribe()
        if not user_input:
            logging.warning("No input received for voice chat")
            return False

        # 3. Generate response
        response = llm_manager.generate_response(user_input)

        # 4. Speak response
        if voice_pipeline.tts.is_available():
            voice_pipeline.tts.speak(response)

        logging.info("Completed voice chat session")
        return True

    def _execute_voice_chat(self, command_name: str) -> bool:
        """Executes a voice chat session."""
        logging.info(f"Starting voice chat for {command_name}")

        # Access components from config as expected by integration tests
        # In production, these might need to be injected differently
        llm_manager = getattr(self.config, "llm_manager", None)
        voice_pipeline = getattr(self.config, "voice_pipeline", None)

        if not self._verify_voice_chat_components(command_name, llm_manager, voice_pipeline):
            return False

        try:
            return self._perform_voice_chat_flow(llm_manager, voice_pipeline)
        except Exception as e:
            msg = f"voice chat failed: {e}"
            logging.error(msg)
            self.report_error(command_name, msg)
            return False

    def report_error(self, command_name: str, error_message: str) -> None:
        logging.critical(f"Error in {command_name}: {error_message}")

        # Also report to the utils logger for test compatibility
        try:
            from chatty_commander.utils.logger import report_error as utils_report_error

            utils_report_error(error_message, context=command_name)
        except ImportError:
            pass  # Fallback if utils logger not available


# Example usage intentionally removed to avoid instantiation without required args during static analysis/tests.

