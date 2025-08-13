"""Configuration handling using dataclasses.

The previous implementation exposed a large ``Config`` class that populated a
collection of dictionaries and performed environment overrides manually.  This
module replaces that ad‑hoc approach with a small hierarchy of dataclasses that
encode defaults, types and environment variable overrides directly in the
schema.  Consumers interact with typed attributes instead of raw dictionaries
which improves discoverability and validation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import logging
import os
import subprocess
from typing import Any, Dict, List


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
    platforms: List[str] = field(default_factory=lambda: ["discord", "slack"])
    personas: Dict[str, str] = field(default_factory=lambda: {"default": "philosophy_advisor"})
    features: Dict[str, bool] = field(
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
    """Application configuration loaded from JSON with env overrides."""

    model_paths: ModelPaths = field(default_factory=ModelPaths)
    api_endpoints: ApiEndpoints = field(default_factory=ApiEndpoints)
    model_actions: Dict[str, Dict[str, str]] = field(default_factory=dict)
    state_models: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "idle": ["hey_chat_tee", "hey_khum_puter"],
            "computer": ["oh_kay_screenshot"],
            "chatty": ["wax_poetic"],
        }
    )
    audio_settings: AudioSettings = field(default_factory=AudioSettings)
    general_settings: GeneralSettings = field(default_factory=GeneralSettings)
    keybindings: Dict[str, str] = field(default_factory=dict)
    commands: Dict[str, Dict[str, str]] = field(default_factory=dict)
    command_sequences: Dict[str, Any] = field(default_factory=dict)
    advisors: AdvisorsConfig = field(default_factory=AdvisorsConfig)
    listen_for: Dict[str, str] = field(default_factory=dict)
    modes: Dict[str, str] = field(default_factory=dict)
    config_file: str = "config.json"

    # ------------------------------------------------------------------
    # Construction helpers

    def __post_init__(self) -> None:  # noqa: D401 - documented on class
        self.api_endpoints.apply_env_overrides()
        self.advisors.apply_env_overrides()
        # Build model actions after commands/keybindings have been loaded
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

        seen: set[str] = set()
        ordered: List[str] = []
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

    def _build_model_actions(self) -> Dict[str, Dict[str, str]]:
        """Build model actions from commands configuration."""
        actions: Dict[str, Dict[str, str]] = {}
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
        if enabled:
            self._enable_start_on_boot()
        else:
            self._disable_start_on_boot()

    def set_check_for_updates(self, enabled: bool) -> None:
        """Enable or disable automatic update checking."""
        self.check_for_updates = enabled
        self._update_general_setting("check_for_updates", enabled)

    def _update_general_setting(self, key: str, value: Any) -> None:
        """Update a general setting in the config data and save to file."""
        setattr(self.general_settings, key, value)
        try:
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
            subprocess.run(["systemctl", "--user", "enable", "chatty-commander.service"], check=True)
            logging.info("Start on boot enabled successfully")
        except Exception as e:  # pragma: no cover - environment specific
            logging.error(f"Failed to enable start on boot: {e}")
            raise

    def _disable_start_on_boot(self) -> None:
        """Disable start on boot by removing systemd user service."""
        try:
            subprocess.run(["systemctl", "--user", "stop", "chatty-commander.service"], check=False)
            subprocess.run(["systemctl", "--user", "disable", "chatty-commander.service"], check=False)
            service_file = os.path.expanduser("~/.config/systemd/user/chatty-commander.service")
            if os.path.exists(service_file):
                os.remove(service_file)
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            logging.info("Start on boot disabled successfully")
        except Exception as e:  # pragma: no cover - environment specific
            logging.error(f"Failed to disable start on boot: {e}")
            raise

    def perform_update_check(self) -> Dict[str, Any] | None:
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


__all__ = ["Config"]

