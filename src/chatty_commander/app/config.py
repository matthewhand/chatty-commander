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
        model_paths = self.config_data.get("model_paths", {})
        self.general_models_path = model_paths.get("idle", "models-idle")
        self.system_models_path = model_paths.get("computer", "models-computer")
        self.chat_models_path = model_paths.get("chatty", "models-chatty")
        self.commands = self.config_data.get("commands", {})
        self.model_actions = self._build_model_actions()
        self.state_models = self.config_data.get("state_models", {})
        self.api_endpoints = self.config_data.get("api_endpoints", {})
        self.state_transitions = self.config_data.get("state_transitions", {})
        self.modes: dict = self.config_data.get("modes", {})
        self.wakeword_state_map: dict[str, str] = {}
        for mode_name, cfg in self.modes.items():
            for ww in (cfg or {}).get("wakewords", []) or []:
                self.wakeword_state_map[str(ww)] = mode_name
        legacy_map = {
            "hey_chat_tee": "chatty",
            "hey_khum_puter": "computer",
            "okay_stop": "idle",
            "thanks_chat_tee": "idle",
            "that_ill_do": "idle",
        }
        for k, v in legacy_map.items():
            self.wakeword_state_map.setdefault(k, v)

        # Voice/GUI behaviour
        self.voice_only = self.config_data.get("voice_only", False)
        self.debug_mode: bool = False

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

        # Apply web server configuration
        self._apply_web_server_config()
        # Load general settings with possible environment overrides
        self._load_general_settings()

    def _apply_env_overrides(self):
        """Apply environment variable overrides to API endpoints."""
        if "CHATBOT_ENDPOINT" in os.environ:
            self.api_endpoints["chatbot_endpoint"] = os.environ["CHATBOT_ENDPOINT"]
        if "HOME_ASSISTANT_ENDPOINT" in os.environ:
            self.api_endpoints["home_assistant"] = os.environ["HOME_ASSISTANT_ENDPOINT"]

    def _apply_web_server_config(self) -> None:
        """Expose web server settings with defaults."""
        web_cfg = self.config_data.get("web_server", {})
        host = web_cfg.get("host", "0.0.0.0")
        port = web_cfg.get("port", 8100)
        auth = web_cfg.get("auth_enabled", True)
        self.web_server = {"host": host, "port": port, "auth_enabled": auth}
        self.web_host = host
        self.web_port = port
        self.web_auth_enabled = auth

    @staticmethod
    def _get_int_env(var_name: str, fallback: int) -> int:
        """Return an integer from the environment or the provided fallback."""
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

    def save_config(self, config_data: dict | None = None) -> None:
        """Save configuration to file."""
        if config_data is not None:
            self.config_data.update(config_data)
            self.config = self.config_data

        # Persist web server configuration
        self._apply_web_server_config()
        self.config_data["web_server"] = self.web_server
        self.config_data["voice_only"] = self.voice_only

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
        self.mic_chunk_size = self._get_int_env(
            "CHATCOMM_MIC_CHUNK_SIZE", audio_settings.get("mic_chunk_size", 1024)
        )
        self.sample_rate = self._get_int_env(
            "CHATCOMM_SAMPLE_RATE", audio_settings.get("sample_rate", 16000)
        )
        self.audio_format = os.environ.get(
            "CHATCOMM_AUDIO_FORMAT", audio_settings.get("audio_format", "int16")
        )

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

        # Advisors: directives configuration
        self.advisors_directives = advisors_cfg.get(
            "directives",
            {
                "parse_models": True,
                "parse_tools": True,
                "parse_mode_switch": True,
            },
        )

        # Advisors: tools configuration
        self.tools = self.config_data.get(
            "tools",
            {
                "fs_enabled": True,
                "browser_enabled": True,
            },
        )

    def _load_config(self):
        """Load configuration from file or defaults."""
        try:
            with open(self.config_file, encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_file} not found. Using defaults.")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Config file {self.config_file} is not a valid JSON. Using defaults.")
            return {}

    def _build_model_actions(self):
        """Create model action mappings from commands config."""
        return self.config_data.get("commands", {})

    def _load_general_settings(self) -> None:
        general = self.config_data.get("general_settings", self.config_data.get("general", {}))
        self.default_state = general.get("default_state", self.default_state)
        self.debug_mode = general.get("debug_mode", self.debug_mode)

    def validate(self):
        # Validate modes structure if present
        if self.modes:
            if not isinstance(self.modes, dict):
                raise ValueError("'modes' must be a dict of mode configs")
            for name, cfg in self.modes.items():
                if not isinstance(cfg, dict):
                    raise ValueError(f"mode '{name}' must be a dict")
                if 'wakewords' in cfg and not isinstance(cfg['wakewords'], list):
                    raise ValueError(f"mode '{name}'.wakewords must be a list")

    def set_start_on_boot(self, enabled):
        self._update_general_setting("start_on_boot", enabled)

    def set_check_for_updates(self, enabled):
        self._update_general_setting("check_for_updates", enabled)

    def _update_general_setting(self, key, value):
        if "general" not in self.config_data:
            self.config_data["general"] = {}
        self.config_data["general"][key] = value
        self.save_config(self.config_data)

    def _enable_start_on_boot(self):
        config_file_path = os.path.join(
            os.path.expanduser("~"), ".config", "autostart", "chatty-commander.desktop"
        )
        try:
            os.makedirs(os.path.dirname(config_file_path), exist_ok=True)
            with open(config_file_path, "w") as f:
                f.write("[Desktop Entry]\n")
                f.write("Type=Application\n")
                f.write("Name=Chatty Commander\n")
                f.write("Exec=python3 /path/to/main.py\n")
                f.write("X-GNOME-Autostart-enabled=true\n")
        except Exception as e:
            logger.error(f"Failed to enable start on boot: {e}")
            raise

    def _disable_start_on_boot(self):
        config_file_path = os.path.join(
            os.path.expanduser("~"), ".config", "autostart", "chatty-commander.desktop"
        )
        try:
            if os.path.exists(config_file_path):
                os.remove(config_file_path)
        except Exception as e:
            logger.error(f"Failed to disable start on boot: {e}")
            raise

    def perform_update_check(self):
        update_check_config = self.config_data.get("update_check", {})

        enabled = update_check_config.get("enabled", False)
        interval_hours = update_check_config.get("interval_hours", 24)

        if not enabled:
            return None

        # Check last check time and see if it's time to check again
        last_check_time = update_check_config.get("last_check_time", 0)
        import time

        current_time = time.time()
        if current_time - last_check_time < interval_hours * 3600:
            return {
                "status": "skip",
                "reason": "Interval not reached yet.",
            }

        # Actually check the latest version (mocked for now)
        latest_version = "v1.2.3"
        current_version = self.config_data.get("version", "v1.0.0")

        # Update the last check time in the config
        update_check_config["last_check_time"] = current_time
        self.config_data["update_check"] = update_check_config
        self.save_config(self.config_data)

        if latest_version != current_version:
            return {
                "status": "update_available",
                "latest_version": latest_version,
                "current_version": current_version,
            }
        else:
            return {
                "status": "up_to_date",
                "version": current_version,
            }

    @classmethod
    def load(cls, config_file="config.json"):
        return cls(config_file)
