"""
model_manager.py

This module manages the loading and utilization of machine learning models for the ChattyCommander application.
It dynamically loads models based on the application's current state, handles errors robustly, and supports dynamic model reloading.
"""

import os
import logging
from openwakeword.model import Model

class ModelManager:
    def __init__(self, config):
        """
        Initializes the ModelManager with configuration settings and an empty model cache.
        """
        logging.basicConfig(level=logging.INFO)  # Setup logging configuration
        self.config = config
        self.models = {
            'general': {},
            'system': {},
            'chat': {}
        }
        self.reload_models()

    def reload_models(self):
        """
        Reloads all models from the specified directories, enabling dynamic updates to model configurations.
        """
        self.models['general'] = self.load_model_set(self.config.general_models_path)
        self.models['system'] = self.load_model_set(self.config.system_models_path)
        self.models['chat'] = self.load_model_set(self.config.chat_models_path)

    def load_model_set(self, path):
        model_set = {}
        if not os.path.exists(path):
            logging.error(f"Model directory {path} does not exist.")
            return model_set

        for model_file in os.listdir(path):
            if model_file.endswith('.onnx'):
                model_path = os.path.join(path, model_file)
                model_name = os.path.splitext(model_file)[0]
                try:
                    model_instance = Model(wakeword_model_paths=[model_path])
                    model_set[model_name] = model_instance
                    logging.info(f"Loaded model '{model_name}' from '{model_path}'.")
                except Exception as e:
                    logging.error(f"Error loading model '{model_name}' from '{model_path}': {e}")
        return model_set

    def get_models(self, state):
        """
        Retrieves models relevant to the current application state, allowing the system to adapt dynamically to state changes.
        """
        return self.models.get(state, {})

    def __repr__(self):
        """
        Provides a representation of the ModelManager's state, useful for debugging and logging.
        """
        return f"<ModelManager(general={len(self.models['general'])}, system={len(self.models['system'])}, chat={len(self.models['chat'])})>"

if __name__ == "__main__":
    # Assuming a configuration instance 'config' is available
    # This section would be used for testing or development purposes.
    model_manager = ModelManager(config)
    print(model_manager)
