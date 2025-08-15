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

        # General settings from both sources
        general_settings = self.config_data.get("general_settings", {})
        self.debug_mode = general_settings.get("debug_mode", True)
        self.inference_framework = general_settings.get("inference_framework", "onnx")
        self.start_on_boot = general_settings.get("start_on_boot", False)
        self.check_for_updates = general_settings.get("check_for_updates", True)

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

        # Advisor directives
        self.advisors_directives = advisors_cfg.get(
            "directives",
            {
                "parse_models": True,
                "parse_tools": True,
                "parse_mode_switch": True,
            },
        )

        # Tool configurations
        self.tools = self.config_data.get(
            "tools",
            {
                "fs_enabled": True,
                "browser_enabled": True,
            },
        )

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

    def _load_config(self):
        """Load configuration from file or return empty dict if not found."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return data
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                return {}
        else:
            logger.info(f"Config file {self.config_file} not found, returning empty config")
            return {}

    def _build_model_actions(self):
        """Build model actions from commands."""
        actions = {}
        commands = getattr(self, 'commands', {})
        for name, cmd in commands.items():
            action_type = cmd.get('action')
            if action_type == 'keypress':
                actions[name] = {'keypress': cmd.get('keys', '')}
            elif action_type == 'url':
                url = cmd.get('url', '').replace(
                    '{home_assistant}', 'http://homeassistant.domain.home:8123/api'
                )
                actions[name] = {'url': url}
            elif action_type == 'custom_message':
                actions[name] = {'message': cmd.get('message', '')}
        return actions

    def _load_general_settings(self) -> None:
        """Load general settings section from config with defaults."""
        pass

    def validate(self):
        """Validate configuration"""
        if not self.model_actions:
            raise ValueError("Model actions cannot be empty")

        for path in [self.general_models_path, self.system_models_path, self.chat_models_path]:
            if not os.path.exists(path):
                logger.warning(f"Model directory {path} does not exist.")
            elif not os.listdir(path):
                logger.warning(f"Model directory {path} is empty.")

    def set_start_on_boot(self, enabled):
        self.start_on_boot = enabled
        self._update_general_setting("start_on_boot", enabled)

    def set_check_for_updates(self, enabled):
        self.check_for_updates = enabled
        self._update_general_setting("check_for_updates", enabled)

    def _update_general_setting(self, key, value):
        """Update a setting in the general_settings section and save."""
        general_settings = self.config_data.setdefault("general_settings", {})
        general_settings[key] = value
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def _enable_start_on_boot(self):
        """Enable start on boot (placeholder)."""
        import subprocess

        try:
            # This is a placeholder; actual implementation depends on OS
            subprocess.run(["systemctl", "--user", "enable", "chatty-commander"], check=True)
        except subprocess.CalledProcessError:
            logger.error("Failed to enable start on boot")
        except FileNotFoundError:
            logger.warning("systemctl not found; start on boot not configured")

    def _disable_start_on_boot(self):
        """Disable start on boot (placeholder)."""
        import subprocess

        try:
            subprocess.run(["systemctl", "--user", "disable", "chatty-commander"], check=True)
        except subprocess.CalledProcessError:
            logger.error("Failed to disable start on boot")
        except FileNotFoundError:
            logger.warning("systemctl not found; start on boot not configured")

    def perform_update_check(self):
        """Check for updates using git."""
        if not self.check_for_updates:
            return None

        try:
            import subprocess

            # Get git directory
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
            git_dir = result.stdout.strip()

            # Fetch latest changes
            subprocess.run(["git", "fetch"], cwd=git_dir, check=True)

            # Check for updates
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD..origin/HEAD"],
                capture_output=True,
                text=True,
                check=True,
                cwd=git_dir,
            )

            update_count = int(result.stdout.strip())
            if update_count > 0:
                # Get latest commit info
                result = subprocess.run(
                    ["git", "log", "-1", "--pretty=format:%s", "origin/HEAD"],
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=git_dir,
                )
                latest_commit = result.stdout.strip()

                return {
                    "updates_available": True,
                    "update_count": update_count,
                    "latest_commit": latest_commit,
                }
            else:
                return {
                    "updates_available": False,
                }

        except Exception:
            return None

    @classmethod
    def load(cls, config_file="config.json"):
        return cls(config_file)
