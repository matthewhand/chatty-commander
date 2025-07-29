class Config:
    def __init__(self, config_file="config.json"):
        import json
        import os
        
        # Load configuration from JSON file
        self.config_file = config_file
        self.config_data = self._load_config()
        
        # Path configurations for model directories
        model_paths = self.config_data.get("model_paths", {})
        self.general_models_path = model_paths.get("idle", "models-idle")
        self.system_models_path = model_paths.get("computer", "models-computer")
        self.chat_models_path = model_paths.get("chatty", "models-chatty")

        # API Endpoints and external command URLs
        api_endpoints = self.config_data.get("api_endpoints", {
            "home_assistant": "http://homeassistant.domain.home:8123/api",
            "chatbot_endpoint": "http://localhost:3100/"
        })
        
        # Override endpoints from environment variables if available
        import os
        if os.environ.get("CHATBOT_ENDPOINT"):
            api_endpoints["chatbot_endpoint"] = os.environ.get("CHATBOT_ENDPOINT")
        if os.environ.get("HOME_ASSISTANT_ENDPOINT"):
            api_endpoints["home_assistant"] = os.environ.get("HOME_ASSISTANT_ENDPOINT")
            
        self.api_endpoints = api_endpoints

        # Configuration for model actions (derived from commands)
        self.model_actions = self._build_model_actions()

        # Configuration for different states and their associated models
        self.state_models = self.config_data.get("state_models", {
            "idle": ["hey_chat_tee", "hey_khum_puter"],
            "computer": ["oh_kay_screenshot"],
            "chatty": ["wax_poetic"]
        })

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
        
        # Keybindings
        self.keybindings = self.config_data.get("keybindings", {})
        
        # Commands
        self.commands = self.config_data.get("commands", {})
        
        # Command sequences
        self.command_sequences = self.config_data.get("command_sequences", {})
        
    def _load_config(self):
        """Load configuration from JSON file."""
        import json
        import os
        
        if not os.path.exists(self.config_file):
            return {}
            
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            import logging
            logging.warning(f"Could not load config file {self.config_file}: {e}")
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
                    model_actions[command_name] = {"keypress": self.config_data["keybindings"][keys]}
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

    def validate(self):
        import logging
        import os
        if not self.model_actions:
            raise ValueError("Model actions configuration is empty.")
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
        import os
        
        if "general_settings" not in self.config_data:
            self.config_data["general_settings"] = {}
        
        self.config_data["general_settings"][key] = value
        
        # Save to file
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config_data, f, indent=2)
        except (IOError, json.JSONEncodeError) as e:
            import logging
            logging.error(f"Could not save config file {self.config_file}: {e}")
    
    def _enable_start_on_boot(self):
        """Enable start on boot using systemd user service."""
        import os
        import subprocess
        import logging
        
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
            subprocess.run(["systemctl", "--user", "enable", "chatty-commander.service"], check=True)
            
            logging.info("Start on boot enabled successfully")
            
        except Exception as e:
            logging.error(f"Failed to enable start on boot: {e}")
            raise
    
    def _disable_start_on_boot(self):
        """Disable start on boot by removing systemd user service."""
        import os
        import subprocess
        import logging
        
        try:
            # Stop and disable the service
            subprocess.run(["systemctl", "--user", "stop", "chatty-commander.service"], check=False)
            subprocess.run(["systemctl", "--user", "disable", "chatty-commander.service"], check=False)
            
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
        import subprocess
        import logging
        
        if not self.check_for_updates:
            return None
        
        try:
            # Check if we're in a git repository
            result = subprocess.run(["git", "rev-parse", "--git-dir"], 
                                  capture_output=True, text=True, check=False)
            if result.returncode != 0:
                logging.warning("Not in a git repository, cannot check for updates")
                return None
            
            # Fetch latest changes
            subprocess.run(["git", "fetch", "origin"], capture_output=True, check=True)
            
            # Check if there are updates available
            result = subprocess.run(["git", "rev-list", "HEAD..origin/main", "--count"], 
                                  capture_output=True, text=True, check=True)
            
            update_count = int(result.stdout.strip())
            
            if update_count > 0:
                # Get the latest commit message
                result = subprocess.run(["git", "log", "origin/main", "-1", "--pretty=format:%s"], 
                                      capture_output=True, text=True, check=True)
                latest_commit = result.stdout.strip()
                
                return {
                    "updates_available": True,
                    "update_count": update_count,
                    "latest_commit": latest_commit
                }
            else:
                return {
                    "updates_available": False,
                    "update_count": 0
                }
                
        except Exception as e:
            logging.error(f"Failed to check for updates: {e}")
            return None
