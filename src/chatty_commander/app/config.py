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

        # Voice/GUI behaviour
        self.voice_only = self.config_data.get("voice_only", False)

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

    @property
    def mic_chunk_size(self) -> int:
        return self.audio_settings.mic_chunk_size

    @property
    def sample_rate(self) -> int:
        return self.audio_settings.sample_rate

    @property
    def audio_format(self) -> str:
        return self.audio_settings.audio_format

    @property
    def debug_mode(self) -> bool:
        return self.general_settings.debug_mode

    @property
    def default_state(self) -> str:
        return self.general_settings.default_state

    @property
    def inference_framework(self) -> str:
        return self.general_settings.inference_framework

    @property
    def start_on_boot(self) -> bool:
        return self.general_settings.start_on_boot

    @start_on_boot.setter
    def start_on_boot(self, value: bool) -> None:
        self.general_settings.start_on_boot = value

    @property
    def check_for_updates(self) -> bool:
        return self.general_settings.check_for_updates

    @check_for_updates.setter
    def check_for_updates(self, value: bool) -> None:
        self.general_settings.check_for_updates = value

    # ------------------------------------------------------------------
    # Serialization helpers

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON serialisable dict of the configuration."""
        data = asdict(self)
        # ``config_file`` is an internal detail and should not be persisted
        data.pop("config_file", None)
        return data

    # ------------------------------------------------------------------
    # Loading helpers

    @classmethod
    def from_dict(cls, data: Dict[str, Any], config_file: str = "config.json") -> "Config":
        """Create a ``Config`` instance from a raw dictionary."""
        model_paths = ModelPaths(**data.get("model_paths", {}))
        api_endpoints = ApiEndpoints(**data.get("api_endpoints", {}))
        audio_settings = AudioSettings(**data.get("audio_settings", {}))
        general_settings = GeneralSettings(**data.get("general_settings", {}))
        advisors_data = data.get("advisors", {})
        advisors = AdvisorsConfig(
            enabled=advisors_data.get("enabled", False),
            llm_api_mode=advisors_data.get("llm_api_mode", "completion"),
            model=advisors_data.get("model", "gpt-oss20b"),
            provider=AdvisorsProvider(**advisors_data.get("provider", {})),
            bridge=AdvisorsBridge(**advisors_data.get("bridge", {})),
            memory=AdvisorsMemory(**advisors_data.get("memory", {})),
            platforms=advisors_data.get("platforms", ["discord", "slack"]),
            personas=advisors_data.get("personas", {"default": "philosophy_advisor"}),
            features=advisors_data.get(
                "features", {"browser_analyst": True, "avatar_talkinghead": False}
            ),
        )

        return cls(
            model_paths=model_paths,
            api_endpoints=api_endpoints,
            model_actions=data.get("model_actions", {}),
            state_models=data.get("state_models")
            or {
                "idle": ["hey_chat_tee", "hey_khum_puter"],
                "computer": ["oh_kay_screenshot"],
                "chatty": ["wax_poetic"],
            },
            audio_settings=audio_settings,
            general_settings=general_settings,
            keybindings=data.get("keybindings", {}),
            commands=data.get("commands", {}),
            command_sequences=data.get("command_sequences", {}),
            advisors=advisors,
            listen_for=data.get("listen_for", {}),
            modes=data.get("modes", {}),
            config_file=config_file,
        )

        # Audio settings
        audio_settings = self.config_data.get("audio_settings", {})
        self.mic_chunk_size = audio_settings.get("mic_chunk_size", 1024)
        self.sample_rate = audio_settings.get("sample_rate", 16000)
        self.audio_format = audio_settings.get("audio_format", "int16")

        # General settings
        general_settings = self.config_data.get("general_settings", {})
        self.debug_mode = general_settings.get("debug_mode", True)
        self.default_state = general_settings.get("default_state", "idle")
        self.inference_framework = general_settings.get("inference_framework", "onnx")
        self.start_on_boot = general_settings.get("start_on_boot", False)
        # Ensure we're using ONNX runtime for ONNX models
        self.check_for_updates = general_settings.get("check_for_updates", True)

        # Logging configuration
        logging_settings = self.config_data.get("logging", {})
        self.log_level = logging_settings.get("level", "INFO")
        self.log_format = logging_settings.get("format", "plain")
        self.log_handlers = logging_settings.get("handlers", ["console"])
        self.log_file = logging_settings.get("file", "logs/chattycommander.log")
        self.log_external_url = logging_settings.get("external_url", "")
        self.telemetry_url = logging_settings.get("telemetry_url", "")
        self.diagnostics_file = logging_settings.get("diagnostics_file", "logs/diagnostics.jsonl")
        self.logging = {
            "level": self.log_level,
            "format": self.log_format,
            "handlers": self.log_handlers,
            "file": self.log_file,
            "external_url": self.log_external_url or None,
            "telemetry_url": self.telemetry_url or None,
            "diagnostics_file": self.diagnostics_file,
        }

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
        provider_base_url = os.environ.get("ADVISORS_PROVIDER_BASE_URL", provider_cfg.get("base_url", ""))
        provider_api_key = os.environ.get("ADVISORS_PROVIDER_API_KEY", provider_cfg.get("api_key", ""))

        self.advisors = {
            "enabled": advisors_cfg.get("enabled", False),
            "llm_api_mode": advisors_cfg.get("llm_api_mode", "completion"),
            "model": advisors_cfg.get("model", "gpt-oss20b"),
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
                    os.environ.get("ADVISORS_MEMORY_PERSIST", str(advisors_cfg.get("memory", {}).get("persistence_enabled", False))).lower()
                    in ["1", "true", "yes"]
                ),
                "persistence_path": os.environ.get(
                    "ADVISORS_MEMORY_PATH",
                    advisors_cfg.get("memory", {}).get("persistence_path", "data/advisors_memory.jsonl"),
                ),
            },
            "platforms": advisors_cfg.get("platforms", ["discord", "slack"]),
            "personas": advisors_cfg.get("personas", {"default": "philosophy_advisor"}),
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
        
    @classmethod
    def load(cls, config_file: str = "config.json") -> "Config":
        """Load configuration from JSON using the search rules of the old class."""
        data = cls._read_config(config_file)
        return cls.from_dict(data, config_file=config_file)

    @staticmethod
    def _read_config(config_file: str) -> Dict[str, Any]:
        """Read configuration data from ``config_file`` with fallbacks."""
        candidates: List[str] = []
        if config_file:
            candidates.append(config_file)
        env_path = os.getenv("CHATCOMM_CONFIG")
        
        if env_path:
            candidates.append(env_path)
        candidates.extend(["default_config.json", "config.json"])

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
        commands_cfg = self.config_data.get(
            "commands",
            {
                "that_ill_do": {
                    "idle": "thanks_chat_tee",
                    "computer": "okay_stop",
                }
            },
        )
        return {"computer": commands_cfg}

    def _load_general_settings(self) -> None:
        general = self.config_data.get("general", {})
        self.default_state = general.get("default_state", self.default_state)

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
        config_file_path = os.path.join(os.path.expanduser("~"), ".config", "autostart", "chatty-commander.desktop")
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
        config_file_path = os.path.join(os.path.expanduser("~"), ".config", "autostart", "chatty-commander.desktop")
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
