class Config:
    def __init__(self):
        # Path configurations for model directories
        self.general_models_path = "models-idle"
        self.system_models_path = "models-computer"
        self.chat_models_path = "models-chatty"

        # API Endpoints and external command URLs (Example setup)
        self.api_endpoints = {
            "home_assistant": "http://homeassistant.domain.home:8123/api",
            "chatbot_endpoint": "https://ubuntu-gtx.domain.home/"
        }

        # Configuration for model actions
        self.model_actions = {
            "okay_stop": {"keypress": "ctrl+shift+;"},
            "hey_khum_puter": {"keypress": "ctrl+shift+;"},
            "oh_kay_screenshot": {"keypress": "alt+print_screen"},
            "lights_on": {"url": f"{self.api_endpoints['home_assistant']}/lights_on"},
            "lights_off": {"url": f"{self.api_endpoints['home_assistant']}/lights_off"},
            "wax_poetic": {"url": self.api_endpoints['chatbot_endpoint']}
        }

        # Configuration for different states and their associated models
        self.state_models = {
            "idle": ["hey_chat_tee", "hey_khum_puter"],
            "computer": self.system_models_path,
            "chatty": self.chat_models_path
        }

        # Audio settings
        self.mic_chunk_size = 1024
        self.sample_rate = 16000
        self.audio_format = "int16"

        # Debug settings
        self.debug_mode = True

        # Default state
        self.default_state = "idle"

        # Inference framework (assuming from context)
        self.inference_framework = "onnx"  # Add if needed based on usage

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
