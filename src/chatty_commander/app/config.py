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

from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
from typing import Any

logger = logging.getLogger(__name__)

# Default command set used when no `commands` are present in the config file.
DEFAULT_COMMANDS: dict[str, Any] = {
    "hello": {"action": "custom_message", "message": "Hello from ChattyCommander!"},
    "take_screenshot": {"action": "keypress", "keys": "take_screenshot"},
    "paste": {"action": "keypress", "keys": "paste"},
    "submit": {"action": "keypress", "keys": "submit"},
}


class Config:
    def __init__(self, config_file: str = "config.json") -> None:
        self.config_file = config_file
        self.config_data: dict[str, Any] = self._load_config()
<<<<<<< HEAD
=======

        # Track if the original config was valid (not empty due to errors)
        self._config_was_valid: bool = bool(self.config_data)
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        # Expose the raw dict for web handlers/tests that expect it
        self.config: dict[str, Any] = self.config_data

        # Core values with repo-defaults aligned to tests
        self.default_state: str = self.config_data.get("default_state", "idle")
        self.general_models_path: str = self.config_data.get(
            "general_models_path", "models-idle"
        )
        self.system_models_path: str = self.config_data.get(
            "system_models_path", "models-computer"
        )
        self.chat_models_path: str = self.config_data.get(
            "chat_models_path", "models-chatty"
        )

        self.state_models: dict[str, list[str]] = self.config_data.get("state_models", {})
        self.api_endpoints: dict[str, str] = self.config_data.get(
            "api_endpoints",
            {
                "home_assistant": "http://homeassistant.domain.home:8123/api",
                "chatbot_endpoint": "http://localhost:3100/",
            },
        )
        self.wakeword_state_map: dict[str, str] = self.config_data.get(
            "wakeword_state_map", {}
        )
        self.state_transitions: dict[str, dict[str, str]] = self.config_data.get(
            "state_transitions", {}
        )
        self.commands: dict[str, Any] = self.config_data.get(
            "commands", dict(DEFAULT_COMMANDS)
        )

        # Advisors configuration
        advisors_cfg = self.config_data.get("advisors", {})
        self.advisors = {
            "enabled": advisors_cfg.get("enabled", False),
            "llm_api_mode": advisors_cfg.get("llm_api_mode", "completion"),
            "model": advisors_cfg.get("model", "gpt-oss20b"),
        }

        # Voice/GUI behaviour
        self._voice_only: bool = bool(self.config_data.get("voice_only", False))



        # Audio configuration
        self.mic_chunk_size: int = self.config_data.get("mic_chunk_size", 1024)
        self.sample_rate: int = self.config_data.get("sample_rate", 16000)
        self.audio_format: str = self.config_data.get("audio_format", "int16")

        # Wake word configuration
        self.wake_words: list[str] = self.config_data.get(
            "wake_words", ["hey_jarvis", "alexa"]
        )
        self.wake_word_threshold: float = self.config_data.get(
            "wake_word_threshold", 0.5
        )

        # Direct access to general settings
        self.check_for_updates: bool = bool(
            self.config_data.get("general", {}).get("check_for_updates", True)
        )
        self.inference_framework: str = str(
            self.config_data.get("general", {}).get("inference_framework", "onnx")
        )

<<<<<<< HEAD
=======

        # Commands for model actions
        default_commands = {}
        if not self.config_file or "commands" not in self.config_data:  # Use defaults if file missing or commands missing
            default_commands = {
                "hello": {
                    "action": "custom_message",
                    "message": "Hello from ChattyCommander!",
                },
                "take_screenshot": {"action": "keypress", "keys": "take_screenshot"},
                "paste": {"action": "keypress", "keys": "paste"},
                "submit": {"action": "keypress", "keys": "submit"},
            }
        self.commands: dict[str, Any] = self.config_data.get("commands", default_commands)  # type: ignore[no-redef]
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16

        # Start on boot setting
        self.start_on_boot: bool = bool(
            self.config_data.get("general", {}).get("start_on_boot", False)
        )

        # Build model_actions from commands and keybindings
        self.model_actions: dict[str, Any] = self._build_model_actions()

<<<<<<< HEAD
=======

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        # Additional attributes for config CLI compatibility
        self.listen_for: dict[str, Any] = self.config_data.get("listen_for", {})
        self.modes: dict[str, Any] = self.config_data.get("modes", {})

        # Validate configuration after all attributes are set (moved from line 92)
        # Verify state_models is a dict before trying to validate its children if needed
        self._validate_config()

        # Back-compat general settings wrapper with property-based access
        class _GeneralSettings:
            def __init__(self, outer: Config) -> None:
                self._cfg = outer

            @property
            def default_state(self) -> str:
<<<<<<< HEAD
=======

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                return self._cfg.default_state

            @default_state.setter
            def default_state(self, v: str) -> None:
<<<<<<< HEAD
=======
                """Default State with (self).

                TODO: Add detailed description and parameters.
                """

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                self._cfg.default_state = v
                self._cfg.config_data["default_state"] = v

            @property
            def debug_mode(self) -> bool:
<<<<<<< HEAD
=======
                """Default State with (self, v: str).

                TODO: Add detailed description and parameters.
                """

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                return bool(
                    self._cfg.config_data.get("general", {}).get("debug_mode", True)
                )

            @debug_mode.setter
            def debug_mode(self, v: bool) -> None:
<<<<<<< HEAD
=======
                """Debug Mode with (self).

                TODO: Add detailed description and parameters.
                """

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                self._cfg._update_general_setting("debug_mode", bool(v))

            @property
            def inference_framework(self) -> str:
<<<<<<< HEAD
=======
                """Debug Mode with (self, v: bool).

                TODO: Add detailed description and parameters.
                """

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                return str(
                    self._cfg.config_data.get("general", {}).get(
                        "inference_framework", "onnx"
                    )
                )

            @inference_framework.setter
            def inference_framework(self, v: str) -> None:
<<<<<<< HEAD
=======
                """Inference Framework with (self).

                TODO: Add detailed description and parameters.
                """

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                self._cfg._update_general_setting("inference_framework", v)

            @property
            def start_on_boot(self) -> bool:
<<<<<<< HEAD
=======
                """Inference Framework with (self, v: str).

                TODO: Add detailed description and parameters.
                """

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                return bool(
                    self._cfg.config_data.get("general", {}).get("start_on_boot", False)
                )

            @start_on_boot.setter
            def start_on_boot(self, v: bool) -> None:
<<<<<<< HEAD
=======
                """Start On Boot with (self).

                TODO: Add detailed description and parameters.
                """

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                self._cfg._update_general_setting("start_on_boot", bool(v))

            @property
            def check_for_updates(self) -> bool:
<<<<<<< HEAD
=======
                """Check For Updates with (self)."""
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                return bool(
                    self._cfg.config_data.get("general", {}).get(
                        "check_for_updates", True
                    )
                )

            @check_for_updates.setter
            def check_for_updates(self, v: bool) -> None:
<<<<<<< HEAD
=======
                """Start On Boot with (self, v: bool)."""
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                self._cfg._update_general_setting("check_for_updates", bool(v))

        self.general_settings = _GeneralSettings(self)

        # Apply env overrides and compute web server config
        self._apply_env_overrides()
        self._apply_web_server_config()
        self._load_general_settings()

    def _validate_config(self) -> None:
<<<<<<< HEAD
        """Validate configuration data and log warnings for potential issues."""
=======
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        # Validate state models
        if not isinstance(self.state_models, dict):
            logger.warning("state_models should be a dictionary")
            self.state_models = {}

        # Validate API endpoints
        if not isinstance(self.api_endpoints, dict):
            logger.warning("api_endpoints should be a dictionary")
            self.api_endpoints = {}

        # Validate commands
        if not isinstance(self.commands, dict):
            logger.warning("commands should be a dictionary")
            self.commands = {}

<<<<<<< HEAD
=======

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        # Check for deprecated or invalid configurations
        if "deprecated_field" in self.config_data:
            logger.warning("Found deprecated configuration field: deprecated_field")

        # Validate model paths exist
        for path_attr in [
            "general_models_path",
            "system_models_path",
            "chat_models_path",
        ]:
            path = getattr(self, path_attr)
<<<<<<< HEAD
=======

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            if path and not os.path.exists(path):
                logger.info(f"Model path does not exist: {path}")

    def reload_config(self) -> bool:
<<<<<<< HEAD
        """Reload configuration from file. Returns True if successful."""
        try:
            new_config = self._load_config()
=======

        try:
            new_config = self._load_config()

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            if new_config != self.config_data:
                self.config_data = new_config
                self.config = new_config
                # Refresh top-level derived attributes that callers read directly;
                # otherwise edits to these in the config file are silently ignored.
                self.general_models_path = self.config_data.get(
                    "general_models_path", "models-idle"
                )
                self.system_models_path = self.config_data.get(
                    "system_models_path", "models-computer"
                )
                self.chat_models_path = self.config_data.get(
                    "chat_models_path", "models-chatty"
                )
                self.state_models = self.config_data.get("state_models", {})
                self.api_endpoints = self.config_data.get(
                    "api_endpoints", self.api_endpoints
                )
                self.wakeword_state_map = self.config_data.get(
                    "wakeword_state_map", {}
                )
                self.state_transitions = self.config_data.get("state_transitions", {})
                self.commands = self.config_data.get("commands", self.commands)
                self._validate_config()
                # Re-apply env overrides + web server config so they keep
                # precedence over freshly-loaded file values (matches __init__).
                self._apply_env_overrides()
                self._apply_web_server_config()
                self._load_general_settings()  # Load general settings to update default_state
                # Force re-load of other properties that depend on config_data
                self.model_actions = self._build_model_actions()
                logger.info("Configuration reloaded successfully")
                return True
            return False
<<<<<<< HEAD
=======

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False

    def save_config(self) -> bool:
        """Save current config_data to the config file for persistence."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=2)
            logger.info("Configuration saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    # ------------------------------------------------------------------
    # Helpers
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to the loaded config."""
        # API endpoint overrides
        if os.environ.get("CHATTY_BRIDGE_TOKEN"):
            # Update web_server config data so _apply_web_server_config picks it up
            if "web_server" not in self.config_data:
                self.config_data["web_server"] = {}
            self.config_data["web_server"]["bridge_token"] = os.environ[
                "CHATTY_BRIDGE_TOKEN"
            ]

<<<<<<< HEAD
        if os.environ.get("CHATBOT_ENDPOINT"):
            self.api_endpoints["chatbot_endpoint"] = os.environ["CHATBOT_ENDPOINT"]
=======

        if os.environ.get("CHATBOT_ENDPOINT"):
            self.api_endpoints["chatbot_endpoint"] = os.environ["CHATBOT_ENDPOINT"]

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        if os.environ.get("HOME_ASSISTANT_ENDPOINT"):
            self.api_endpoints["home_assistant"] = os.environ["HOME_ASSISTANT_ENDPOINT"]

        # General settings overrides
        if os.environ.get("CHATCOMM_DEBUG"):
            debug_val = os.environ["CHATCOMM_DEBUG"].lower()
            self.config_data.setdefault("general", {})["debug_mode"] = debug_val in (
                "true",
                "yes",
                "1",
            )

<<<<<<< HEAD
        if os.environ.get("CHATCOMM_DEFAULT_STATE"):
            self.default_state = os.environ["CHATCOMM_DEFAULT_STATE"]

        if os.environ.get("CHATCOMM_INFERENCE_FRAMEWORK"):
            self.inference_framework = os.environ["CHATCOMM_INFERENCE_FRAMEWORK"]

=======

        if os.environ.get("CHATCOMM_DEFAULT_STATE"):
            self.default_state = os.environ["CHATCOMM_DEFAULT_STATE"]


        if os.environ.get("CHATCOMM_INFERENCE_FRAMEWORK"):
            self.inference_framework = os.environ["CHATCOMM_INFERENCE_FRAMEWORK"]


>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        if os.environ.get("CHATCOMM_START_ON_BOOT"):
            boot_val = os.environ["CHATCOMM_START_ON_BOOT"].lower()
            self.start_on_boot = boot_val in ("true", "yes", "1")

        if os.environ.get("CHATCOMM_CHECK_FOR_UPDATES"):
            update_val = os.environ["CHATCOMM_CHECK_FOR_UPDATES"].lower()
            self.check_for_updates = update_val not in ("false", "no", "0")

    def _apply_web_server_config(self) -> None:
        web_cfg = self.config_data.get("web_server", {})
        host = web_cfg.get("host", "0.0.0.0")
        port = int(web_cfg.get("port", 8100))
        auth = bool(web_cfg.get("auth_enabled", True))
        bridge_token = web_cfg.get("bridge_token")
        self.web_server = {
            "host": host,
            "port": port,
            "auth_enabled": auth,
            "bridge_token": bridge_token,
        }
        self.web_host = host
        self.web_port = port
        self.web_auth_enabled = auth

    @staticmethod
    def _get_int_env(var_name: str, fallback: int) -> int:
        value = os.environ.get(var_name)
        if value is not None:
            try:
                parsed = int(value)
<<<<<<< HEAD
                if parsed <= 0:
                    raise ValueError
                return parsed
=======
    
                if parsed <= 0:
                    raise ValueError
                return parsed
    
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            except ValueError:
                logger.warning("Invalid %s=%r; using %s", var_name, value, fallback)
        return fallback

    def _load_config(self) -> dict[str, Any]:
<<<<<<< HEAD
        if not isinstance(self.config_file, str):
             raise TypeError("config_file must be a string")
        try:
            with open(self.config_file, encoding="utf-8") as f:
                config_data = json.load(f)
=======

        if not isinstance(self.config_file, str):
             raise TypeError("config_file must be a string")
        try:

            with open(self.config_file, encoding="utf-8") as f:
                config_data = json.load(f)
        
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                # Ensure we always return a dictionary, even if JSON contains null or other non-dict values
                if not isinstance(config_data, dict):
                    logger.warning(
                        "Config file %s contains non-dictionary content (%s). Using defaults.",
                        self.config_file,
                        type(config_data).__name__,
                    )
                    return {}
                return config_data
<<<<<<< HEAD
=======

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        except (FileNotFoundError, PermissionError, OSError):
            logger.warning(
                "Error loading config file %s. Using defaults.", self.config_file
            )
<<<<<<< HEAD
            return {}
=======
            return {"general": {}}

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        except json.JSONDecodeError:
            logger.error(
                "Config file %s is not valid JSON. Using defaults.", self.config_file
            )
            return {}

    def _load_general_settings(self) -> None:
        general_settings = self.config_data.get("general_settings", {})

        def _env_bool(name: str, default: bool) -> bool:
<<<<<<< HEAD
=======
            """Load general settings, applying environment variable overrides."""
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            val = os.getenv(name)
            if val is None:
                return default
            return val.strip().lower() in {"1", "true", "yes"}

<<<<<<< HEAD
        # Set debug mode in config data
        self.config_data.setdefault("general", {})["debug_mode"] = _env_bool(
            "CHATCOMM_DEBUG", general_settings.get("debug_mode", True)
        )
=======

        # Set debug mode in config data only if original config was valid
        if self._config_was_valid:
            if self.config_data.get("general") is None:
                self.config_data["general"] = {}
            self.config_data["general"]["debug_mode"] = _env_bool(
                "CHATCOMM_DEBUG", general_settings.get("debug_mode", True)
            )
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        self.default_state = os.getenv(
            "CHATCOMM_DEFAULT_STATE",
            general_settings.get("default_state", self.config_data.get("default_state", "idle"))
        )
        self.inference_framework = os.getenv(
            "CHATCOMM_INFERENCE_FRAMEWORK",
            general_settings.get("inference_framework", "onnx"),
        )
        self.start_on_boot = _env_bool(
            "CHATCOMM_START_ON_BOOT", general_settings.get("start_on_boot", False)
        )
        self.check_for_updates = _env_bool(
            "CHATCOMM_CHECK_FOR_UPDATES",
            general_settings.get("check_for_updates", True),
        )

    # Build model_actions from the high-level 'commands' section
    def _build_model_actions(self) -> dict[str, dict[str, str]]:
        actions: dict[str, dict[str, str]] = {}
        # Ensure commands is a dict
        commands_cfg = self.commands if isinstance(self.commands, dict) else {}
        keybindings = self.config_data.get("keybindings", {}) or {}
        for name, cfg in commands_cfg.items():
<<<<<<< HEAD
            if not isinstance(cfg, dict):
                continue
            action_type = cfg.get("action")
            if action_type == "keypress":
                keys = cfg.get("keys")
                if isinstance(keys, str):
                   mapped = keybindings.get(keys, keys)
                   if mapped:
                       actions[name] = {"keypress": mapped}
=======

            if not isinstance(cfg, dict):
                continue
            action_type = cfg.get("action")

            if action_type == "keypress":
                keys = cfg.get("keys")
    
                if isinstance(keys, str):
                   mapped = keybindings.get(keys, keys)
       
                   if mapped:
                       actions[name] = {"keypress": mapped}

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            elif action_type == "url":
                url = cfg.get("url", "")
                url = url.replace(
                    "{home_assistant}", self.api_endpoints.get("home_assistant", "")
                )
                url = url.replace(
                    "{chatbot_endpoint}", self.api_endpoints.get("chatbot_endpoint", "")
                )
                actions[name] = {"url": url}
<<<<<<< HEAD
            elif action_type == "custom_message":
                msg = cfg.get("message", "")
                actions[name] = {"shell": f"echo {shlex.quote(msg)}"}
=======

            elif action_type == "custom_message":
                msg = cfg.get("message", "")
                actions[name] = {"shell": f"echo {shlex.quote(msg)}"}

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            elif action_type == "voice_chat":
                # Voice chat action - pass through the entire config
                actions[name] = {"action": "voice_chat"}
        return actions

    # Convenience property for tests expecting top-level 'debug_mode'
    @property
    def debug_mode(self) -> bool:
        return bool(self.config_data.get("general", {}).get("debug_mode", True))

    @debug_mode.setter
    def debug_mode(self, value: bool) -> None:
<<<<<<< HEAD
        self.config_data.setdefault("general", {})["debug_mode"] = bool(value)

    @property
    def voice_only(self) -> bool:
        return self._voice_only

    @voice_only.setter
    def voice_only(self, value: Any) -> None:
        self._voice_only = bool(value)

    # ------------------------------------------------------------------
    # Public API
    def save_config(self, config_data: dict | None = None) -> None:
        if config_data is not None:
            self.config_data.update(config_data)
            self.config = self.config_data
        # Persist web server config and voice_only
        self._apply_web_server_config()
        self.config_data["web_server"] = self.web_server
        self.config_data["voice_only"] = self.voice_only
        if not self.config_file:
            # Skip saving when config_file is empty (for tests)
            return
        try:
            # Write atomically: serialize to a sibling temp file, then replace.
            # This prevents a crash mid-write from corrupting the live config.
            import os as _os
            import tempfile as _tempfile

            target_dir = _os.path.dirname(_os.path.abspath(self.config_file)) or "."
            fd, tmp_path = _tempfile.mkstemp(
                prefix=".config-", suffix=".tmp", dir=target_dir
            )
            try:
                with _os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(self.config_data, f, indent=2)
                _os.replace(tmp_path, self.config_file)
            except BaseException:
                # Never leave a temp file behind on failure.
                try:
                    _os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        except (TypeError, ValueError, OSError) as e:
            logger.error(f"Could not save config file: {e}")

    def validate(self) -> None:
=======
        if "general" not in self.config_data:
            self.config_data["general"] = {}
        self.config_data["general"]["debug_mode"] = bool(value)

    @property
    def voice_only(self) -> bool:
        """Voice Only with (self)."""
        return bool(self._voice_only)

    @voice_only.setter
    def voice_only(self, value: Any) -> None:
        """Voice Only with (self, value: Any)."""
        self._voice_only = bool(value)
        self.config_data.setdefault("general", {})["voice_only"] = self._voice_only

    def validate(self) -> None:
        """Validate with (self)."""
        # already done in __init__ and reload, but keep for API
        self._validate_config()

    def _enable_start_on_boot(self) -> None:
        """Enable start on boot functionality."""
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        if not self.model_actions:
            raise ValueError("Model actions configuration is empty.")
        for path in [
            self.general_models_path,
            self.system_models_path,
            self.chat_models_path,
        ]:
            if not os.path.exists(path):
                logging.warning(f"Model directory {path} does not exist.")
            elif not os.listdir(path):
                logging.warning(f"Model directory {path} is empty.")

    def set_start_on_boot(self, enabled: bool) -> None:
<<<<<<< HEAD
=======
        """Update with (self, enabled: bool)."""
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        self._update_general_setting("start_on_boot", bool(enabled))
        self.start_on_boot = bool(enabled)
        if enabled:
            self._enable_start_on_boot()
        else:
            self._disable_start_on_boot()
<<<<<<< HEAD

    def _enable_start_on_boot(self) -> None:
        """Enable start-on-boot at the OS level.

        Platform-specific autostart integration (systemd user unit / launchd /
        Windows registry) is not implemented yet. The preference is persisted in
        config so it can be honored once implemented; warn so the caller isn't
        misled into thinking autostart was actually configured.
        """
        logging.warning(
            "start_on_boot enabled in config, but OS-level autostart is not yet "
            "implemented for this platform; no autostart entry was created."
        )

    def _disable_start_on_boot(self) -> None:
        """Disable start-on-boot at the OS level (see _enable_start_on_boot)."""
        logging.warning(
            "start_on_boot disabled in config, but OS-level autostart is not yet "
            "implemented for this platform; no autostart entry was removed."
        )

    def set_check_for_updates(self, enabled: bool) -> None:
        self._update_general_setting("check_for_updates", bool(enabled))
        self.check_for_updates = bool(enabled)

    def _update_general_setting(self, key: str, value: Any) -> None:
        if "general" not in self.config_data:
            self.config_data["general"] = {}
        self.config_data["general"][key] = value
        self.save_config(self.config_data)

    def perform_update_check(self) -> dict[str, Any] | None:
        if not self.check_for_updates:
            return None
        try:
=======
        pass

    def _disable_start_on_boot(self) -> None:
        pass

    def set_check_for_updates(self, enabled: bool) -> None:
        """Disable start on boot functionality."""
        """Update with (self, enabled: bool).

        TODO: Add detailed description and parameters.
        TODO: Add detailed description and parameters.
        """
        
        # Validate preconditions
        if not self.check_for_updates:
            return None
        try:

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                check=False,
            )
<<<<<<< HEAD
            if result.returncode != 0:
=======

            if result.returncode != 0:

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                logging.warning("Not in a git repository, cannot check for updates")
                return None
            subprocess.run(["git", "fetch", "origin"], capture_output=True, check=True)
            result = subprocess.run(
                ["git", "rev-list", "HEAD..origin/main", "--count"],
                capture_output=True,
                text=True,
                check=True,
            )
            update_count = int((result.stdout or "0").strip())
<<<<<<< HEAD
            if update_count > 0:
                result = subprocess.run(
=======

            if update_count > 0:
                result = subprocess.run(
                    # Build filtered collection
    
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                    ["git", "log", "origin/main", "-1", "--pretty=format:%s"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                latest_commit = (result.stdout or "").strip()
                return {
                    "updates_available": True,
                    "update_count": update_count,
                    "latest_commit": latest_commit,
                }
            else:
                return {"updates_available": False, "update_count": 0}
<<<<<<< HEAD
        except Exception as e:  # pragma: no cover
=======

        except Exception as e:  # pragma: no cover
            # Build filtered collection
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            logging.error(f"Failed to check for updates: {e}")
            return None

    @classmethod
<<<<<<< HEAD
    def load(cls, config_file: str = "config.json") -> Config:
=======
    def load(cls, config_file: str = "config.json") -> "Config":
        """Load config from file (convenience)."""
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        return cls(config_file)

    @classmethod
    def from_dict(
        cls, data: dict[str, Any], config_file: str = "config.json"
    ) -> "Config":
        """Create a Config instance from a dictionary (for tests/web reloads)."""
        instance = cls.__new__(cls)
        instance.config_file = config_file
<<<<<<< HEAD
        instance.config_data = data.copy()
        # Mirror __init__: web handlers/tests expect `.config` as the raw dict.
        instance.config = instance.config_data
=======
        instance.config_data = (data or {}).copy()
        instance.config = instance.config_data
        instance._config_was_valid = bool(instance.config_data)
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16

        # Core values (mirrors __init__ population)
        instance.default_state = instance.config_data.get("default_state", "idle")
        instance.general_models_path = instance.config_data.get(
            "general_models_path", instance.config_data.get("general", {}).get("models_path", "models-idle")
        )
<<<<<<< HEAD
        # system/chat model paths were omitted here (only general was set), so
        # ModelManager built from a from_dict() Config couldn't find them.
        instance.system_models_path = instance.config_data.get(
            "system_models_path", "models-computer"
        )
        instance.chat_models_path = instance.config_data.get(
            "chat_models_path", "models-chatty"
        )
=======
        instance.system_models_path = instance.config_data.get("system_models_path", "models-computer")
        instance.chat_models_path = instance.config_data.get("chat_models_path", "models-chatty")

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        instance.state_models = instance.config_data.get("state_models", {})
        instance.api_endpoints = instance.config_data.get(
            "api_endpoints",
            {
                "home_assistant": "http://homeassistant.domain.home:8123/api",
                "chatbot_endpoint": "http://localhost:3100/",
            },
        )
        instance.wakeword_state_map = instance.config_data.get("wakeword_state_map", {})
        instance.state_transitions = instance.config_data.get("state_transitions", {})
        instance.commands = instance.config_data.get("commands", {})
        instance.advisors = instance.config_data.get("advisors", {})

        instance._voice_only = bool(
            instance.config_data.get("voice_only", False)
            or instance.config_data.get("general", {}).get("voice_only", False)
        )
        instance.mic_chunk_size = int(
            instance.config_data.get("mic_chunk_size", instance.config_data.get("general", {}).get("mic_chunk_size", 1024))
        )
        instance.sample_rate = int(
            instance.config_data.get("sample_rate", instance.config_data.get("general", {}).get("sample_rate", 16000))
        )
        instance.audio_format = instance.config_data.get("general", {}).get(
            "audio_format", "int16"
        )
<<<<<<< HEAD
=======

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        instance.check_for_updates = bool(
            instance.config_data.get("general", {}).get("check_for_updates", True)
        )
        instance.inference_framework = instance.config_data.get("general", {}).get(
            "inference_framework", "onnx"
        )
        instance.start_on_boot = bool(
            instance.config_data.get("general", {}).get("start_on_boot", False)
        )
<<<<<<< HEAD
=======

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        instance.listen_for = instance.config_data.get("listen_for", {})
        instance.modes = instance.config_data.get("modes", {})

        # Init dependent structures
        instance.model_actions = instance._build_model_actions()
        instance._load_general_settings()
        instance._apply_env_overrides()
        instance._apply_web_server_config()
        instance._validate_config()

        return instance

    def to_dict(self) -> dict[str, Any]:
<<<<<<< HEAD
        """Convert the config back to a dictionary for serialization."""
=======
        """Serialize current config state (for persistence/web)."""
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        result = self.config_data.copy()
        result["model_actions"] = self.model_actions
        result["state_models"] = self.state_models
        result["listen_for"] = self.listen_for
        result["modes"] = self.modes
        result["default_state"] = self.default_state

        if "general" not in result:
            result["general"] = {}
        result["general"]["models_path"] = self.general_models_path
        result["general"]["voice_only"] = self.voice_only
        result["general"]["mic_chunk_size"] = self.mic_chunk_size
        result["general"]["sample_rate"] = self.sample_rate
        result["general"]["audio_format"] = self.audio_format
        result["general"]["check_for_updates"] = self.check_for_updates
        result["general"]["inference_framework"] = self.inference_framework
        result["general"]["start_on_boot"] = self.start_on_boot

        return result
