from __future__ import annotations

import json
import logging
import os
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


class Config:
    def __init__(self, config_file: str = "config.json") -> None:
        self.config_file = config_file
        self.config_data: dict[str, Any] = self._load_config()
        # Expose the raw dict for web handlers/tests that expect it
        self.config: dict[str, Any] = self.config_data

        # Core values with repo-defaults aligned to tests
        self.default_state: str = self.config_data.get("default_state", "idle")
        self.general_models_path: str = self.config_data.get("general_models_path", "models-idle")
        self.system_models_path: str = self.config_data.get("system_models_path", "models-computer")
        self.chat_models_path: str = self.config_data.get("chat_models_path", "models-chatty")

        self.state_models: dict[str, list[str]] = self.config_data.get("state_models", {})
        self.api_endpoints: dict[str, str] = self.config_data.get(
            "api_endpoints",
            {
                "home_assistant": "http://homeassistant.domain.home:8123/api",
                "chatbot_endpoint": "http://localhost:3100/",
            },
        )
        self.wakeword_state_map: dict[str, str] = self.config_data.get("wakeword_state_map", {})
        self.state_transitions: dict[str, dict[str, str]] = self.config_data.get("state_transitions", {})
        self.commands: dict[str, Any] = self.config_data.get("commands", {})

        # Voice/GUI behaviour
        self.voice_only: bool = bool(self.config_data.get("voice_only", False))

        # Build model_actions from commands and keybindings
        self.model_actions: dict[str, Any] = self._build_model_actions()

        # Back-compat general settings wrapper with property-based access
        class _GeneralSettings:
            def __init__(self, outer: "Config") -> None:
                self._cfg = outer

            @property
            def default_state(self) -> str:
                return self._cfg.default_state

            @default_state.setter
            def default_state(self, v: str) -> None:
                self._cfg.default_state = v
                self._cfg.config_data["default_state"] = v

            @property
            def debug_mode(self) -> bool:
                return bool(self._cfg.config_data.get("general", {}).get("debug_mode", True))

            @debug_mode.setter
            def debug_mode(self, v: bool) -> None:
                self._cfg._update_general_setting("debug_mode", bool(v))

            @property
            def inference_framework(self) -> str:
                return str(self._cfg.config_data.get("general", {}).get("inference_framework", "onnx"))

            @inference_framework.setter
            def inference_framework(self, v: str) -> None:
                self._cfg._update_general_setting("inference_framework", v)

            @property
            def start_on_boot(self) -> bool:
                return bool(self._cfg.config_data.get("general", {}).get("start_on_boot", False))

            @start_on_boot.setter
            def start_on_boot(self, v: bool) -> None:
                self._cfg._update_general_setting("start_on_boot", bool(v))

            @property
            def check_for_updates(self) -> bool:
                return bool(self._cfg.config_data.get("general", {}).get("check_for_updates", True))

            @check_for_updates.setter
            def check_for_updates(self, v: bool) -> None:
                self._cfg._update_general_setting("check_for_updates", bool(v))

        self.general_settings = _GeneralSettings(self)

        # Apply env overrides and compute web server config
        self._apply_env_overrides()
        self._apply_web_server_config()
        self._load_general_settings()

    # ------------------------------------------------------------------
    # Helpers
    def _apply_env_overrides(self) -> None:
        if os.environ.get("CHATBOT_ENDPOINT"):
            self.api_endpoints["chatbot_endpoint"] = os.environ["CHATBOT_ENDPOINT"]
        if os.environ.get("HOME_ASSISTANT_ENDPOINT"):
            self.api_endpoints["home_assistant"] = os.environ["HOME_ASSISTANT_ENDPOINT"]

    def _apply_web_server_config(self) -> None:
        web_cfg = self.config_data.get("web_server", {})
        host = web_cfg.get("host", "0.0.0.0")
        port = int(web_cfg.get("port", 8100))
        auth = bool(web_cfg.get("auth_enabled", True))
        self.web_server = {"host": host, "port": port, "auth_enabled": auth}
        self.web_host = host
        self.web_port = port
        self.web_auth_enabled = auth

    @staticmethod
    def _get_int_env(var_name: str, fallback: int) -> int:
        value = os.environ.get(var_name)
        if value is not None:
            try:
                parsed = int(value)
                if parsed <= 0:
                    raise ValueError
                return parsed
            except ValueError:
                logger.warning("Invalid %s=%r; using %s", var_name, value, fallback)
        return fallback

    def _load_config(self) -> dict[str, Any]:
        try:
            with open(self.config_file, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Config file %s not found. Using defaults.", self.config_file)
            return {}
        except json.JSONDecodeError:
            logger.error("Config file %s is not valid JSON. Using defaults.", self.config_file)
            return {}

    def _load_general_settings(self) -> None:
        general = self.config_data.get("general", {})
        self.default_state = general.get("default_state", self.default_state)

    # Build model_actions from the high-level 'commands' section
    def _build_model_actions(self) -> dict[str, dict[str, str]]:
        actions: dict[str, dict[str, str]] = {}
        commands_cfg = self.config_data.get("commands", {}) or {}
        keybindings = self.config_data.get("keybindings", {}) or {}
        for name, cfg in commands_cfg.items():
            action_type = cfg.get("action")
            if action_type == "keypress":
                keys = cfg.get("keys")
                mapped = keybindings.get(keys, keys)
                if mapped:
                    actions[name] = {"keypress": mapped}
            elif action_type == "url":
                url = cfg.get("url", "")
                url = url.replace("{home_assistant}", self.api_endpoints.get("home_assistant", ""))
                url = url.replace("{chatbot_endpoint}", self.api_endpoints.get("chatbot_endpoint", ""))
                actions[name] = {"url": url}
            elif action_type == "custom_message":
                msg = cfg.get("message", "")
                actions[name] = {"shell": f"echo {msg}"}
        return actions

    # Convenience property for tests expecting top-level 'debug_mode'
    @property
    def debug_mode(self) -> bool:
        return bool(self.config_data.get("general_settings", {}).get("debug_mode", True))

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
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config_data, f, indent=2)

    def validate(self) -> None:
        if not self.model_actions:
            raise ValueError("Model actions configuration is empty.")
        for path in [self.general_models_path, self.system_models_path, self.chat_models_path]:
            if not os.path.exists(path):
                logging.warning(f"Model directory {path} does not exist.")
            elif not os.listdir(path):
                logging.warning(f"Model directory {path} is empty.")

    # Start-on-boot and update checks
    def set_start_on_boot(self, enabled: bool) -> None:
        self.general_settings.start_on_boot = enabled

    def set_check_for_updates(self, enabled: bool) -> None:
        self._update_general_setting("check_for_updates", bool(enabled))

    def _update_general_setting(self, key: str, value: Any) -> None:
        if "general" not in self.config_data:
            self.config_data["general"] = {}
        self.config_data["general"][key] = value
        self.save_config(self.config_data)

    def perform_update_check(self) -> dict[str, Any] | None:
        if not self.general_settings.check_for_updates:
            return None
        try:
            result = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                logging.warning("Not in a git repository, cannot check for updates")
                return None
            subprocess.run(["git", "fetch", "origin"], capture_output=True, check=True)
            result = subprocess.run(
                ["git", "rev-list", "HEAD..origin/main", "--count"], capture_output=True, text=True, check=True
            )
            update_count = int((result.stdout or "0").strip())
            if update_count > 0:
                result = subprocess.run(
                    ["git", "log", "origin/main", "-1", "--pretty=format:%s"], capture_output=True, text=True, check=True
                )
                latest_commit = (result.stdout or "").strip()
                return {"updates_available": True, "update_count": update_count, "latest_commit": latest_commit}
            else:
                return {"updates_available": False, "update_count": 0}
        except Exception as e:  # pragma: no cover
            logging.error(f"Failed to check for updates: {e}")
            return None

    @classmethod
    def load(cls, config_file: str = "config.json") -> "Config":
        return cls(config_file)
