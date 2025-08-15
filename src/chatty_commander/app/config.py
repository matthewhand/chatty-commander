from __future__ import annotations

import json
import logging
import os
import subprocess
<<<<<<< HEAD
=======
from dataclasses import asdict, dataclass, field
>>>>>>> update/pr-38
from typing import Any

# ---------------------------------------------------------------------------
# Dataclass models for individual configuration sections


@dataclass
class ModelPaths:
    idle: str = "models-idle"
    computer: str = "models-computer"
    chatty: str = "models-chatty"


@dataclass
class ApiEndpoints:
    home_assistant: str = "http://homeassistant.domain.home:8123/api"
    chatbot_endpoint: str = "http://localhost:3100/"

    def apply_env_overrides(self) -> None:
        """Override endpoint values from environment variables."""
        self.chatbot_endpoint = os.getenv("CHATBOT_ENDPOINT", self.chatbot_endpoint)
        self.home_assistant = os.getenv("HOME_ASSISTANT_ENDPOINT", self.home_assistant)


@dataclass
class AudioSettings:
    mic_chunk_size: int = 1024
    sample_rate: int = 16000
    audio_format: str = "int16"


@dataclass
class GeneralSettings:
    debug_mode: bool = True
    default_state: str = "idle"
    inference_framework: str = "onnx"
    start_on_boot: bool = False
    check_for_updates: bool = True


# --- Advisors -----------------------------------------------------------------


@dataclass
class AdvisorsProvider:
    base_url: str = ""
    api_key: str = ""

    def apply_env_overrides(self) -> None:
        self.base_url = os.getenv("ADVISORS_PROVIDER_BASE_URL", self.base_url)
        self.api_key = os.getenv("ADVISORS_PROVIDER_API_KEY", self.api_key)


@dataclass
class AdvisorsBridge:
    token: str = ""
    url: str = ""

    def apply_env_overrides(self) -> None:
        self.token = os.getenv("ADVISORS_BRIDGE_TOKEN", self.token)
        self.url = os.getenv("ADVISORS_BRIDGE_URL", self.url)


@dataclass
class AdvisorsMemory:
    persistence_enabled: bool = False
    persistence_path: str = "data/advisors_memory.jsonl"

    def apply_env_overrides(self) -> None:
        persist = os.getenv("ADVISORS_MEMORY_PERSIST")
        if persist is not None:
            self.persistence_enabled = persist.lower() in {"1", "true", "yes"}
        path = os.getenv("ADVISORS_MEMORY_PATH")
        if path is not None:
            self.persistence_path = path


@dataclass
class AdvisorsConfig:
    enabled: bool = False
    llm_api_mode: str = "completion"
    model: str = "gpt-oss20b"
    provider: AdvisorsProvider = field(default_factory=AdvisorsProvider)
    bridge: AdvisorsBridge = field(default_factory=AdvisorsBridge)
    memory: AdvisorsMemory = field(default_factory=AdvisorsMemory)
    platforms: list[str] = field(default_factory=lambda: ["discord", "slack"])
    personas: dict[str, str] = field(default_factory=lambda: {"default": "philosophy_advisor"})
    features: dict[str, bool] = field(
        default_factory=lambda: {"browser_analyst": True, "avatar_talkinghead": False}
    )

    def apply_env_overrides(self) -> None:
        self.provider.apply_env_overrides()
        self.bridge.apply_env_overrides()
        self.memory.apply_env_overrides()


# ---------------------------------------------------------------------------
# Root configuration dataclass


@dataclass
class Config:
<<<<<<< HEAD
    def __init__(self, config_file: str = "config.json") -> None:
        self.config_file = config_file
        self.config_data: dict[str, Any] = self._load_config()
        # Expose the raw dict for web handlers/tests that expect it
        self.config: dict[str, Any] = self.config_data
=======
    def __init__(self, config_file="config.json"):

    model_paths: ModelPaths = field(default_factory=ModelPaths)
    api_endpoints: ApiEndpoints = field(default_factory=ApiEndpoints)
    model_actions: dict[str, dict[str, str]] = field(default_factory=dict)
    state_models: dict[str, list[str]] = field(
        default_factory=lambda: {
            "idle": ["hey_chat_tee", "hey_khum_puter"],
            "computer": ["oh_kay_screenshot"],
            "chatty": ["wax_poetic"],
        }
    )
    audio_settings: AudioSettings = field(default_factory=AudioSettings)
    general_settings: GeneralSettings = field(default_factory=GeneralSettings)
    keybindings: dict[str, str] = field(default_factory=dict)
    commands: dict[str, dict[str, str]] = field(default_factory=dict)
    command_sequences: dict[str, Any] = field(default_factory=dict)
    advisors: AdvisorsConfig = field(default_factory=AdvisorsConfig)
    listen_for: dict[str, str] = field(default_factory=dict)
    modes: dict[str, str] = field(default_factory=dict)
    config_file: str = "config.json"
>>>>>>> update/pr-38

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

<<<<<<< HEAD
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
=======
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
>>>>>>> update/pr-38
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
<<<<<<< HEAD
            result = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True, check=False)
=======
            with open(self.config_file, "w") as f:  # noqa: PTH123 - user path
                json.dump(self.to_dict(), f, indent=2)
        except (OSError, TypeError, ValueError) as e:  # pragma: no cover - log only
            logging.error(f"Could not save config file {self.config_file}: {e}")

    # --- Systemd helpers ------------------------------------------------

    def _enable_start_on_boot(self) -> None:
        """Enable start on boot using systemd user service."""
        try:
            systemd_dir = os.path.expanduser("~/.config/systemd/user")
            os.makedirs(systemd_dir, exist_ok=True)
            cwd = os.getcwd()
            python_exec = subprocess.check_output(["which", "python3"]).decode().strip()
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
            with open(service_file, "w") as f:  # noqa: PTH123 - user path
                f.write(service_content)
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            subprocess.run(
                ["systemctl", "--user", "enable", "chatty-commander.service"], check=True
            )
            logging.info("Start on boot enabled successfully")
        except Exception as e:  # pragma: no cover - environment specific
            logging.error(f"Failed to enable start on boot: {e}")
            raise

    def _disable_start_on_boot(self):
        config_file_path = os.path.join(os.path.expanduser("~"), ".config", "autostart", "chatty-commander.desktop")
        try:
            subprocess.run(["systemctl", "--user", "stop", "chatty-commander.service"], check=False)
            subprocess.run(
                ["systemctl", "--user", "disable", "chatty-commander.service"], check=False
            )
            service_file = os.path.expanduser("~/.config/systemd/user/chatty-commander.service")
            if os.path.exists(service_file):
                os.remove(service_file)
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            logging.info("Start on boot disabled successfully")
        except Exception as e:  # pragma: no cover - environment specific
            logging.error(f"Failed to disable start on boot: {e}")
            raise

    def perform_update_check(self) -> dict[str, Any] | None:
        """Check for updates from the repository."""
        if not self.check_for_updates:
            return None
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"], capture_output=True, text=True, check=False
            )
>>>>>>> update/pr-38
            if result.returncode != 0:
                logging.warning("Not in a git repository, cannot check for updates")
                return None
            subprocess.run(["git", "fetch", "origin"], capture_output=True, check=True)
            result = subprocess.run(
<<<<<<< HEAD
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

=======
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

__all__ = ["Config"]
>>>>>>> update/pr-38
