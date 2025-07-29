import json
import os
import sys

XDG_CONFIG_HOME = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
APP_CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, 'chatty-commander')
DEFAULT_CONFIG_PATH = os.path.join(APP_CONFIG_DIR, 'config.json')

class ConfigCLI:
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        os.makedirs(APP_CONFIG_DIR, exist_ok=True)
        self.config_path = config_path
        self.config = self.load_config()

    def run_wizard(self):
        """
        Guided configuration wizard for all key options.
        Prompts user, validates input, allows skip/default, writes to config file.
        """
        print("=== ChattyCommander Configuration Wizard ===")
        print("You will be guided through the most important configuration options.")
        print("Press Enter to accept the default or current value shown in [brackets]. Type 'skip' to leave unchanged.\n")

        # Helper for prompting
        def prompt_option(prompt, default=None, explanation=None, validator=None, cast=None):
            if explanation:
                print(f"\n{explanation}")
            prompt_str = f"{prompt}"
            if default is not None:
                prompt_str += f" [{default}]"
            prompt_str += ": "
            while True:
                val = input(prompt_str).strip()
                if val.lower() == "skip" or (val == "" and default is not None):
                    return default
                if val == "" and default is None:
                    print("Please enter a value or type 'skip'.")
                    continue
                if cast:
                    try:
                        val_cast = cast(val)
                    except Exception:
                        print(f"Invalid value type. Expected {cast.__name__}.")
                        continue
                else:
                    val_cast = val
                if validator and not validator(val_cast):
                    print("Invalid value. Please try again.")
                    continue
                return val_cast

        # --- Model Paths ---
        print("\n--- Model Paths ---")
        model_paths = self.config.get("model_paths", {
            "idle": "models-idle",
            "computer": "models-computer",
            "chatty": "models-chatty"
        })
        for key in ["idle", "computer", "chatty"]:
            explanation = f"Directory path for {key} mode models."
            default = model_paths.get(key, f"models-{key}")
            val = prompt_option(
                f"Path for {key} models", default=default, explanation=explanation
            )
            model_paths[key] = val
        self.config["model_paths"] = model_paths

        # --- API Endpoints ---
        print("\n--- API Endpoints ---")
        api_endpoints = self.config.get("api_endpoints", {
            "home_assistant": "http://homeassistant.domain.home:8123/api",
            "chatbot_endpoint": "http://localhost:3100/"
        })
        for key, default_url in [
            ("home_assistant", "http://homeassistant.domain.home:8123/api"),
            ("chatbot_endpoint", "http://localhost:3100/")
        ]:
            explanation = f"URL for {key.replace('_', ' ').title()} API endpoint."
            default = api_endpoints.get(key, default_url)
            val = prompt_option(
                f"API endpoint for {key}", default=default, explanation=explanation,
                validator=lambda v: v.startswith("http://") or v.startswith("https://")
            )
            api_endpoints[key] = val
        self.config["api_endpoints"] = api_endpoints

        # --- Audio Settings ---
        print("\n--- Audio Settings ---")
        audio_settings = self.config.get("audio_settings", {
            "mic_chunk_size": 1024,
            "sample_rate": 16000,
            "audio_format": "int16"
        })
        audio_settings["mic_chunk_size"] = prompt_option(
            "Microphone chunk size",
            default=audio_settings.get("mic_chunk_size", 1024),
            explanation="Number of audio samples per chunk (affects latency and performance).",
            cast=int,
            validator=lambda v: isinstance(v, int) and v > 0
        )
        audio_settings["sample_rate"] = prompt_option(
            "Audio sample rate (Hz)",
            default=audio_settings.get("sample_rate", 16000),
            explanation="Sample rate for audio input (e.g., 16000 for most speech models).",
            cast=int,
            validator=lambda v: isinstance(v, int) and v > 0
        )
        audio_settings["audio_format"] = prompt_option(
            "Audio format",
            default=audio_settings.get("audio_format", "int16"),
            explanation="Audio format (e.g., int16, float32).",
            validator=lambda v: v in ["int16", "float32"]
        )
        self.config["audio_settings"] = audio_settings

        # --- General Settings ---
        print("\n--- General Settings ---")
        general_settings = self.config.get("general_settings", {
            "debug_mode": True,
            "default_state": "idle",
            "inference_framework": "onnx",
            "start_on_boot": False,
            "check_for_updates": True
        })
        general_settings["debug_mode"] = prompt_option(
            "Enable debug mode? (True/False)",
            default=general_settings.get("debug_mode", True),
            explanation="Enable verbose debug output for troubleshooting.",
            validator=lambda v: str(v).lower() in ["true", "false"],
            cast=lambda v: str(v).lower() == "true"
        )
        general_settings["default_state"] = prompt_option(
            "Default state",
            default=general_settings.get("default_state", "idle"),
            explanation="Initial state when the application starts (idle, computer, chatty).",
            validator=lambda v: v in ["idle", "computer", "chatty"]
        )
        general_settings["inference_framework"] = prompt_option(
            "Inference framework",
            default=general_settings.get("inference_framework", "onnx"),
            explanation="Framework for running models (onnx, pytorch, etc).",
            validator=lambda v: v in ["onnx", "pytorch"]
        )
        general_settings["start_on_boot"] = prompt_option(
            "Start on boot? (True/False)",
            default=general_settings.get("start_on_boot", False),
            explanation="Should ChattyCommander start automatically on system boot?",
            validator=lambda v: str(v).lower() in ["true", "false"],
            cast=lambda v: str(v).lower() == "true"
        )
        general_settings["check_for_updates"] = prompt_option(
            "Enable automatic update checks? (True/False)",
            default=general_settings.get("check_for_updates", True),
            explanation="Check for updates to ChattyCommander automatically at startup.",
            validator=lambda v: str(v).lower() in ["true", "false"],
            cast=lambda v: str(v).lower() == "true"
        )
        self.config["general_settings"] = general_settings

        # --- Save and finish ---
        self.save_config()
        print("\nConfiguration wizard complete! Your settings have been saved to:")
        print(f"  {self.config_path}\n")
        print("You can re-run the wizard at any time with: chatty-commander config wizard")
        print("Or further customize advanced options using other config commands.")

    def load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {self.config_path}", file=sys.stderr)
        return {'model_actions': {}, 'state_models': {}}

    def save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def set_model_action(self, model_name, action):
        self.config['model_actions'][model_name] = action
        self.save_config()

    def interactive_mode(self):
        while True:
            config_type = input('Enter configuration type (model_action or state_model): ')
            if config_type == 'model_action':
                model_name = input('Enter model name: ')
                action = input('Enter action: ')
                self.set_model_action(model_name, action)
            elif config_type == 'state_model':
                state = input('Enter state: ')
                models = input('Enter comma-separated model paths: ').split(',')
                self.config['state_models'][state] = [m.strip() for m in models]
                self.save_config()
            else:
                print('Invalid type')
                continue
            continue_input = input('Add another? (y/n): ')
            if continue_input.lower() != 'y':
                break

    def set_state_model(self, state, models_str):
        models = [m.strip() for m in models_str.split(',')]
        self.config['state_models'][state] = models
        self.save_config()

    def set_listen_for(self, key, value):
        if 'listen_for' not in self.config:
            self.config['listen_for'] = {}
        self.config['listen_for'][key] = value
        self.save_config()

    def set_mode(self, mode, value):
        if 'modes' not in self.config:
            self.config['modes'] = {}
        self.config['modes'][mode] = value
        self.save_config()

    def list_config(self):
        print("Current Configuration:")
        print("\nModel Actions:")
        for model, action in self.config.get('model_actions', {}).items():
            if isinstance(action, dict):
                keybinding = action.get('keypress', 'N/A')
                print(f"- {model}: Action={action}, Keybinding={keybinding}")
            else:
                print(f"- {model}: Action={action}, Keybinding=N/A")
        print("\nState Models:")
        for state, models in self.config.get('state_models', {}).items():
            print(f"- {state}: Models={', '.join(models)}")
        print("\nListen For:")
        for key, value in self.config.get('listen_for', {}).items():
            print(f"- {key}: {value}")
        print("\nModes:")
        for mode, value in self.config.get('modes', {}).items():
            print(f"- {mode}: {value}")
        print("\nAvailable Models:")
        for dir_name in ['models-idle', 'models-computer', 'models-chatty']:
            if os.path.exists(dir_name):
                models = [f for f in os.listdir(dir_name) if f.endswith('.onnx')]
                print(f"- {dir_name}: {', '.join(models)}")