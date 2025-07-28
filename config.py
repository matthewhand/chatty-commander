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
            "chatbot_endpoint": "http://localhost:3000/"
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
