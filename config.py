"""
config.py

Configuration settings for the ChattyCommander application. This file contains constants and settings
used throughout the application to manage different modes and operational settings.
"""

# Path configurations for model directories
GENERAL_MODELS_PATH = "models/general"
SYSTEM_MODELS_PATH = "models/system"
CHAT_MODELS_PATH = "models/chat"

# API Endpoints and external command URLs (Example setup)
API_ENDPOINTS = {
    "home_assistant": "http://homeassistant.domain.home:8123/api",
    "chatbot_endpoint": "https://ubuntu-gtx.domain.home/"
}

# Configuration for model actions
MODEL_ACTIONS = {
    "okay_stop": {"keypress": "ctrl+shift+;"},
    "hey_khum_puter": {"keypress": "ctrl+shift+;"},
    "oh_kay_screenshot": {"keypress": "alt+print_screen"},
    "lights_on": {"url": f"{API_ENDPOINTS['home_assistant']}/lights_on"},
    "lights_off": {"url": f"{API_ENDPOINTS['home_assistant']}/lights_off"},
    "wax_poetic": {"url": API_ENDPOINTS['chatbot_endpoint']}
}

# Configuration for different states and their associated models
STATE_MODELS = {
    "idle": ["hey_chat_tee", "hey_khum_puter"],
    "computer": SYSTEM_MODELS_PATH,
    "chatty": CHAT_MODELS_PATH
}

# Audio settings
MIC_CHUNK_SIZE = 1024
SAMPLE_RATE = 16000
AUDIO_FORMAT = "int16"

# Debug settings
DEBUG_MODE = True
