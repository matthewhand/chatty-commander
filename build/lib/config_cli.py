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
            keybinding = action.get('keypress', 'N/A')
            print(f"- {model}: Action={action}, Keybinding={keybinding}")
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
