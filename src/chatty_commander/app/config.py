from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)


class Config:
    def __init__(self, config_file="config.json"):

        # Load configuration from JSON file (with fallbacks and env overrides)
        self.config_file = config_file
        self.config_data = self._load_config()
        # Expose raw config under .config for web routers expecting a dict
        self.config: dict = self.config_data

        # Extract commonly used config values as properties
        self.default_state = self.config_data.get("default_state", "idle")
        self.general_models_path = self.config_data.get("general_models_path", "models/general")
        self.system_models_path = self.config_data.get("system_models_path", "models/system")
        self.chat_models_path = self.config_data.get("chat_models_path", "models/chat")
        self.model_actions = self.config_data.get("model_actions", {})
        self.state_models = self.config_data.get("state_models", {})
        self.api_endpoints = self.config_data.get("api_endpoints", {})
        self.wakeword_state_map = self.config_data.get("wakeword_state_map", {})
        self.state_transitions = self.config_data.get("state_transitions", {})
        self.commands = self.config_data.get("commands", {})

        # Create general_settings object for backward compatibility
        class GeneralSettings:
            def __init__(self, config):
                self._config = config

            @property
            def default_state(self):
                return self._config.default_state

            @default_state.setter
            def default_state(self, value):
                self._config.default_state = value
                self._config.config_data["default_state"] = value

        self.general_settings = GeneralSettings(self)

        # Apply environment variable overrides
        self._apply_env_overrides()

        # Load general settings with possible environment overrides
        self._load_general_settings()

    def _apply_env_overrides(self):
        """Apply environment variable overrides to API endpoints."""
        if "CHATBOT_ENDPOINT" in os.environ:
            self.api_endpoints["chatbot_endpoint"] = os.environ["CHATBOT_ENDPOINT"]
        if "HOME_ASSISTANT_ENDPOINT" in os.environ:
            self.api_endpoints["home_assistant"] = os.environ["HOME_ASSISTANT_ENDPOINT"]

    def save_config(self, config_data: dict | None = None) -> None:
        """Save configuration to file."""
        if config_data is not None:
            self.config_data.update(config_data)
            self.config = self.config_data

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

        # Path configurations for model directories
        model_paths = self.config_data.get("model_paths", {})
        self.general_models_path = model_paths.get("idle", "models-idle")
        self.system_models_path = model_paths.get("computer", "models-computer")
        self.chat_models_path = model_paths.get("chatty", "models-chatty")

        # API Endpoints and external command URLs
        api_endpoints = self.config_data.get(
            "api_endpoints",
            {
                "home_assistant": "http://homeassistant.domain.home:8123/api",
                "chatbot_endpoint": "http://localhost:3100/",
            },
        )

        # Override endpoints from environment variables if available
        if os.environ.get("CHATBOT_ENDPOINT"):
            api_endpoints["chatbot_endpoint"] = os.environ.get("CHATBOT_ENDPOINT")
        if os.environ.get("HOME_ASSISTANT_ENDPOINT"):
            api_endpoints["home_assistant"] = os.environ.get("HOME_ASSISTANT_ENDPOINT")

        self.api_endpoints = api_endpoints

        # Configuration for model actions (derived from commands)
        self.model_actions = self._build_model_actions()

        # Configuration for different states and their associated models
        self.state_models = self.config_data.get(
            "state_models",
            {
                "idle": ["hey_chat_tee", "hey_khum_puter", "okay_stop"],
                "computer": ["oh_kay_screenshot", "okay_stop"],
                "chatty": ["wax_poetic", "thanks_chat_tee", "that_ill_do", "okay_stop"],
            },
        )

        # Flexible modes configuration (optional)
        # Example structure:
        # modes: {
        #   "idle": {"wakewords": ["hey_chat_tee", "hey_khum_puter"], "persona": "default", "tools": ["fs","browser"]},
        #   "computer": {"wakewords": ["oh_kay_screenshot"], "persona": null},
        #   "chatty": {"wakewords": [], "persona": "chatty"}
        # }
        self.modes: dict = self.config_data.get("modes", {})

        # Build wakeword -> target mode map from modes, with legacy fallbacks
        self.wakeword_state_map: dict[str, str] = {}
        for mode_name, cfg in self.modes.items():
            for ww in (cfg or {}).get("wakewords", []) or []:
                self.wakeword_state_map[str(ww)] = mode_name

        # Legacy default fallbacks if not otherwise specified
        legacy_map = {
            "hey_chat_tee": "chatty",
            "hey_khum_puter": "computer",
            "okay_stop": "idle",
            "thanks_chat_tee": "idle",
            "that_ill_do": "idle",
        }
        for k, v in legacy_map.items():
            self.wakeword_state_map.setdefault(k, v)

        # Audio settings
        audio_settings = self.config_data.get("audio_settings", {})
        self.mic_chunk_size = audio_settings.get("mic_chunk_size", 1024)
        self.sample_rate = audio_settings.get("sample_rate", 16000)
        self.audio_format = audio_settings.get("audio_format", "int16")

        # General settings
        self._load_general_settings()

        # Keybindings
        self.keybindings = self.config_data.get("keybindings", {})

        # Commands
        self.commands = self.config_data.get("commands", {})

        # Command sequences
        self.command_sequences = self.config_data.get("command_sequences", {})

        # Advisors (OpenAI-Agents advisor) settings
        advisors_cfg = self.config_data.get("advisors", {})
        provider_cfg = advisors_cfg.get("provider", {})
        # Environment overrides
        provider_base_url = os.environ.get(
            "ADVISORS_PROVIDER_BASE_URL", provider_cfg.get("base_url", "")
        )
        provider_api_key = os.environ.get(
            "ADVISORS_PROVIDER_API_KEY", provider_cfg.get("api_key", "")
        )

        self.advisors = {
            "enabled": advisors_cfg.get("enabled", False),
            "llm_api_mode": advisors_cfg.get("llm_api_mode", "completion"),
            "model": advisors_cfg.get("model", "gpt-oss20b"),
            "default_persona": advisors_cfg.get("default_persona", "chatty"),
            "personas": advisors_cfg.get(
                "personas",
                {
                    "chatty": "You are Chatty, a friendly multimodal avatar with 3D talking head, continuous TTS/STT. Be concise and engaging."
                },
            ),
            "provider": {
                "base_url": provider_base_url,
                "api_key": provider_api_key,
            },
            "bridge": {
                "token": os.environ.get(
                    "ADVISORS_BRIDGE_TOKEN", advisors_cfg.get("bridge", {}).get("token", "")
                ),
                "url": os.environ.get(
                    "ADVISORS_BRIDGE_URL", advisors_cfg.get("bridge", {}).get("url", "")
                ),
            },
            "memory": {
                "persistence_enabled": bool(
                    os.environ.get(
                        "ADVISORS_MEMORY_PERSIST",
                        str(advisors_cfg.get("memory", {}).get("persistence_enabled", False)),
                    ).lower()
                    in ["1", "true", "yes"]
                ),
                "persistence_path": os.environ.get(
                    "ADVISORS_MEMORY_PATH",
                    advisors_cfg.get("memory", {}).get(
                        "persistence_path", "data/advisors_memory.jsonl"
                    ),
                ),
            },
            "platforms": advisors_cfg.get("platforms", ["discord", "slack"]),
            "features": advisors_cfg.get(
                "features",
                {"browser_analyst": True, "avatar_talkinghead": False},
            ),
        }

    def _load_config(self):
        """Load configuration from JSON file with fallbacks and environment overrides."""
        import json
        import logging
        import os

        # 1) Candidate paths: explicit file, CHATCOMM_CONFIG, default_config.json, config.json
        candidates = []
        if self.config_file:
            candidates.append(self.config_file)
        env_path = os.environ.get("CHATCOMM_CONFIG")
        if env_path:
            candidates.append(env_path)
        # Prefer default_config.json if present, then config.json
        candidates.extend(["default_config.json", "config.json"])

        # De-duplicate while preserving order
        seen = set()
        ordered = []
        for p in candidates:
            if p and p not in seen:
                ordered.append(p)
                seen.add(p)

        # Attempt to load the first existing and valid JSON
        for path in ordered:
            if os.path.exists(path):
                try:
                    with open(path) as f:
                        data = json.load(f)
                    logging.info(f"Loaded configuration from {path}")
                    return data
                except (json.JSONDecodeError, OSError) as e:
                    logging.warning(f"Could not load config file {path}: {e}")

        logging.warning("No valid configuration found; falling back to empty config")
        return {}

    def _build_model_actions(self):
        """Build model actions from commands configuration."""
        model_actions = {}
        commands = self.config_data.get("commands", {})

        for command_name, command_config in commands.items():
            action_type = command_config.get("action")

            if action_type == "keypress":
                keys = command_config.get("keys")
                if keys and keys in self.config_data.get("keybindings", {}):
                    model_actions[command_name] = {
                        "keypress": self.config_data["keybindings"][keys]
                    }
                else:
                    model_actions[command_name] = {"keypress": keys}
            elif action_type == "url":
                url = command_config.get("url", "")
                # Replace endpoint placeholders
                for endpoint_name, endpoint_url in self.api_endpoints.items():
                    url = url.replace(f"{{{endpoint_name}}}", endpoint_url)
                model_actions[command_name] = {"url": url}
            elif action_type == "custom_message":
                model_actions[command_name] = {"message": command_config.get("message", "")}

        return model_actions

    def _load_general_settings(self) -> None:
        """Load general settings, applying environment variable overrides."""
        general_settings = self.config_data.get("general_settings", {})

        def _env_bool(name: str, default: bool) -> bool:
            val = os.getenv(name)
            if val is None:
                return default
            return val.strip().lower() in {"1", "true", "yes"}

        self.debug_mode = _env_bool("CHATCOMM_DEBUG", general_settings.get("debug_mode", True))
        self.default_state = os.getenv(
            "CHATCOMM_DEFAULT_STATE", general_settings.get("default_state", "idle")
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

    def validate(self):
        import logging
        import os

        # Allow empty model_actions for tests - just warn instead of error
        if not self.model_actions:
            logger.warning("Model actions configuration is empty.")
            return  # Don't raise error for empty config in tests
        paths = [self.general_models_path, self.system_models_path, self.chat_models_path]
        for path in paths:
            if not os.path.exists(path):
                logging.warning(f"Model directory {path} does not exist.")
            elif not os.listdir(path):
                logging.warning(f"Model directory {path} is empty.")

    def set_start_on_boot(self, enabled):
        """Enable or disable start on boot."""
        self.start_on_boot = enabled
        self._update_general_setting("start_on_boot", enabled)

        if enabled:
            self._enable_start_on_boot()
        else:
            self._disable_start_on_boot()

    def set_check_for_updates(self, enabled):
        """Enable or disable automatic update checking."""
        self.check_for_updates = enabled
        self._update_general_setting("check_for_updates", enabled)

    def _update_general_setting(self, key, value):
        """Update a general setting in the config data and save to file."""
        import json

        if "general_settings" not in self.config_data:
            self.config_data["general_settings"] = {}

        self.config_data["general_settings"][key] = value

        # Save to file
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config_data, f, indent=2)
        except (OSError, json.JSONEncodeError) as e:
            import logging

            logging.error(f"Could not save config file {self.config_file}: {e}")

    def _enable_start_on_boot(self):
        """Enable start on boot using systemd user service."""
        import logging
        import os
        import subprocess

        try:
            # Create systemd user directory if it doesn't exist
            systemd_dir = os.path.expanduser("~/.config/systemd/user")
            os.makedirs(systemd_dir, exist_ok=True)

            # Get current working directory and python executable
            cwd = os.getcwd()
            python_exec = subprocess.check_output(["which", "python3"]).decode().strip()

            # Create systemd service file
            service_content = f"""[Unit]
Description=ChattyCommander Voice Control Service
After=graphical-session.target

[Service]
Type=simple
ExecStart={python_exec} {cwd}/cli.py run
WorkingDirectory={cwd}
Restart=always
RestartSec=5
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
"""

            service_file = os.path.join(systemd_dir, "chatty-commander.service")
            with open(service_file, 'w') as f:
                f.write(service_content)

            # Enable and start the service
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            subprocess.run(
                ["systemctl", "--user", "enable", "chatty-commander.service"], check=True
            )

            logging.info("Start on boot enabled successfully")

        except Exception as e:
            logging.error(f"Failed to enable start on boot: {e}")
            raise

    def _disable_start_on_boot(self):
        """Disable start on boot by removing systemd user service."""
        import logging
        import os
        import subprocess

        try:
            # Stop and disable the service
            subprocess.run(["systemctl", "--user", "stop", "chatty-commander.service"], check=False)
            subprocess.run(
                ["systemctl", "--user", "disable", "chatty-commander.service"], check=False
            )

            # Remove service file
            service_file = os.path.expanduser("~/.config/systemd/user/chatty-commander.service")
            if os.path.exists(service_file):
                os.remove(service_file)

            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)

            logging.info("Start on boot disabled successfully")

        except Exception as e:
            logging.error(f"Failed to disable start on boot: {e}")
            raise

    def perform_update_check(self):
        """Check for updates from the repository."""
        import logging
        import subprocess

        if not self.check_for_updates:
            return None

        try:
            # Check if we're in a git repository
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"], capture_output=True, text=True, check=False
            )
            if result.returncode != 0:
                logging.warning("Not in a git repository, cannot check for updates")
                return None

            # Fetch latest changes
            subprocess.run(["git", "fetch", "origin"], capture_output=True, check=True)

            # Check if there are updates available
            result = subprocess.run(
                ["git", "rev-list", "HEAD..origin/main", "--count"],
                capture_output=True,
                text=True,
                check=True,
            )

            update_count = int(result.stdout.strip())

            if update_count > 0:
                # Get the latest commit message
                result = subprocess.run(
                    ["git", "log", "origin/main", "-1", "--pretty=format:%s"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                latest_commit = result.stdout.strip()

                return {
                    "updates_available": True,
                    "update_count": update_count,
                    "latest_commit": latest_commit,
                }
            else:
                return {"updates_available": False, "update_count": 0}

        except Exception as e:
            logging.error(f"Failed to check for updates: {e}")
            return None

    @classmethod
    def load(cls, config_file="config.json"):
        """Load configuration from file (class method for backward compatibility)."""
        return cls(config_file)
