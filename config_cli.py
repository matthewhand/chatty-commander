import json
import os

class ConfigCLI:
    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
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