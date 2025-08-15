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

        self.model_actions: dict[str, Any] = self.config_data.get("model_actions", {})
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

    # --- Convenience attribute accessors ---------------------------------

    @property
    def general_models_path(self) -> str:
        return self.model_paths.idle

    @general_models_path.setter
    def general_models_path(self, value: str) -> None:
        self.model_paths.idle = value

    @property
    def system_models_path(self) -> str:
        return self.model_paths.computer

    @system_models_path.setter
    def system_models_path(self, value: str) -> None:
        self.model_paths.computer = value

    @property
    def chat_models_path(self) -> str:
        return self.model_paths.chatty

    @chat_models_path.setter
    def chat_models_path(self, value: str) -> None:
        self.model_paths.chatty = value

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

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON serialisable dict of the configuration."""
        data = asdict(self)
        # ``config_file`` is an internal detail and should not be persisted
        data.pop("config_file", None)
        return data

    # ------------------------------------------------------------------
    # Loading helpers

    @classmethod
    def from_dict(cls, data: dict[str, Any], config_file: str = "config.json") -> Config:
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
<<<<<<< HEAD
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

        # Authentication settings
        auth_cfg = self.config_data.get("auth", {})
        self.auth = {
            "enabled": auth_cfg.get("enabled", False),
            # Environment variable override for API key
            "api_key": os.environ.get(
                "CHATCOMM_API_KEY", auth_cfg.get("api_key", "")
            ),
            "allowed_origins": auth_cfg.get(
                "allowed_origins", ["http://localhost:3000"]
            ),
        }

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
=======
            state_transitions=data.get("state_transitions")
            or {
                "idle": {
                    "hey_chat_tee": "chatty",
                    "hey_khum_puter": "computer",
                    "toggle_mode": "computer",
                },
                "chatty": {
                    "hey_khum_puter": "computer",
                    "okay_stop": "idle",
                    "thanks_chat_tee": "idle",
                    "toggle_mode": "idle",
                },
                "computer": {
                    "hey_chat_tee": "chatty",
                    "okay_stop": "idle",
                    "that_ill_do": "idle",
                    "toggle_mode": "chatty",
>>>>>>> update/pr-52
                },
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

    @classmethod
    def load(cls, config_file: str = "config.json") -> Config:
        """Load configuration from JSON using the search rules of the old class."""
        data = cls._read_config(config_file)
        return cls.from_dict(data, config_file=config_file)

    @staticmethod
    def _read_config(config_file: str) -> dict[str, Any]:
        """Read configuration data from ``config_file`` with fallbacks."""
        candidates: list[str] = []
        if config_file:
            candidates.append(config_file)
        env_path = os.getenv("CHATCOMM_CONFIG")
        if env_path:
            candidates.append(env_path)
        candidates.extend(["default_config.json", "config.json"])

        seen: set[str] = set()
        ordered: list[str] = []
        for p in candidates:
            if p and p not in seen:
                ordered.append(p)
                seen.add(p)

        for path in ordered:
            if os.path.exists(path):
                try:
                    with open(path) as f:  # noqa: PTH123 - user provided path
                        data = json.load(f)
                    logging.info(f"Loaded configuration from {path}")
                    return data
                except (json.JSONDecodeError, OSError) as e:  # pragma: no cover - log only
                    logging.warning(f"Could not load config file {path}: {e}")

        logging.warning("No valid configuration found; falling back to empty config")
        return {}

    # ------------------------------------------------------------------
    # Behavioural helpers (largely ported from previous implementation)

    def _build_model_actions(self) -> dict[str, dict[str, str]]:
        """Build model actions from commands configuration."""
        actions: dict[str, dict[str, str]] = {}
        for command_name, command_config in self.commands.items():
            action_type = command_config.get("action")
            if action_type == "keypress":
                keys = command_config.get("keys")
                if keys and keys in self.keybindings:
                    actions[command_name] = {"keypress": self.keybindings[keys]}
                else:
                    actions[command_name] = {"keypress": keys}
            elif action_type == "url":
                url = command_config.get("url", "")
                for endpoint_name, endpoint_url in asdict(self.api_endpoints).items():
                    url = url.replace(f"{{{endpoint_name}}}", endpoint_url)
                actions[command_name] = {"url": url}
            elif action_type == "custom_message":
                actions[command_name] = {"message": command_config.get("message", "")}
        return actions

    # --- Public API ----------------------------------------------------

    def validate(self) -> None:
        """Validate configuration values."""
        if not self.model_actions:
            raise ValueError("Model actions configuration is empty.")

        paths = [self.general_models_path, self.system_models_path, self.chat_models_path]
        for path in paths:
            if not os.path.exists(path):  # noqa: PTH110
                logging.warning(f"Model directory {path} does not exist.")
            elif not os.listdir(path):
                logging.warning(f"Model directory {path} is empty.")

    # --- Start on boot / update checks ---------------------------------

    def set_start_on_boot(self, enabled: bool) -> None:
        """Enable or disable start on boot."""
        self.start_on_boot = enabled
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

    def perform_update_check(self) -> dict[str, Any] | None:
        """Check for updates from the repository."""
        if not self.check_for_updates:
            return None
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"], capture_output=True, text=True, check=False
            )
            if result.returncode != 0:
                logging.warning("Not in a git repository, cannot check for updates")
                return None
            subprocess.run(["git", "fetch", "origin"], capture_output=True, check=True)
            result = subprocess.run(
                ["git", "rev-list", "HEAD..origin/main", "--count"],
                capture_output=True,
                text=True,
                check=True,
            )
            update_count = int(result.stdout.strip())
            if update_count > 0:
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
        except Exception as e:  # pragma: no cover - log only
            logging.error(f"Failed to check for updates: {e}")
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
