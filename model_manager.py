"""
model_manager.py

This module manages the loading and utilization of machine learning models for the ChattyCommander application.
It dynamically loads models based on the application's current state, handles errors robustly, and supports dynamic model reloading.
"""

import os
import logging
import time
import asyncio
import random  # For simulating command detection in demo mode
from typing import Dict, Optional, Any
try:
    from wakewords.model import Model
except ModuleNotFoundError as e:
    logging.warning("Dependency 'wakewords' not found. Using dummy Model. Some functionality may be limited.")
    class Model:
        def __init__(self, path):
            self.path = path

class ModelManager:
    def __init__(self, config: Any) -> None:
        """
        Initializes the ModelManager with configuration settings and an empty model cache.
        """
        logging.basicConfig(level=logging.INFO)  # Setup logging configuration
        self.config: Any = config
        self.models: Dict[str, Dict[str, Model]] = {
            'general': {},
            'system': {},
            'chat': {}
        }
        self.active_models: Dict[str, Model] = {}
        self.reload_models()

    def reload_models(self, state: Optional[str] = None) -> Dict[str, Model]:
        """
        Reloads all models from the specified directories, enabling dynamic updates to model configurations.
        If state is provided, only loads models for that state.
        """
        if state is None:
            self.models['general'] = self.load_model_set(self.config.general_models_path)
            self.models['system'] = self.load_model_set(self.config.system_models_path)
            self.models['chat'] = self.load_model_set(self.config.chat_models_path)
            self.active_models = self.models['general']
            return self.models
        elif state == 'idle':
            self.models['general'] = self.load_model_set(self.config.general_models_path)
            self.active_models = self.models['general']
            return self.models['general']
        elif state == 'computer':
            self.models['system'] = self.load_model_set(self.config.system_models_path)
            self.active_models = self.models['system']
            return self.models['system']
        elif state == 'chatty':
            self.models['chat'] = self.load_model_set(self.config.chat_models_path)
            self.active_models = self.models['chat']
            return self.models['chat']
        return {}

    def load_model_set(self, path: str) -> Dict[str, Model]:
        model_set: Dict[str, Model] = {}
        if not os.path.exists(path):
            logging.error(f"Model directory {path} does not exist.")
            return model_set

        for model_file in os.listdir(path):
            if model_file.endswith('.onnx'):
                model_path = os.path.join(path, model_file)
                model_name = os.path.splitext(model_file)[0]
                if not os.path.exists(model_path):
                    logging.warning(f"Model file '{model_path}' does not exist. Skipping.")
                    continue
                try:
                    model_instance = Model(model_path)
                    model_set[model_name] = model_instance
                    logging.info(f"Successfully loaded model '{model_name}' from '{model_path}'.")
                except Exception as e:
                    logging.error(f"Failed to load model '{model_name}' from '{model_path}'. Error details: {str(e)}. Continuing with other models.")
        return model_set

    async def async_listen_for_commands(self) -> Optional[str]:
        """
        Asynchronous version for listening for voice commands.
        """
        await asyncio.sleep(1)  # Simulate processing time
        if self.active_models and random.random() < 0.05:
            return random.choice(list(self.active_models.keys()))
        return None

    def listen_for_commands(self) -> Optional[str]:
        """
        Synchronous wrapper for async_listen_for_commands.
        """
        return asyncio.run(self.async_listen_for_commands())

    def get_models(self, state: str) -> Dict[str, Model]:
        """
        Retrieves models relevant to the current application state, allowing the system to adapt dynamically to state changes.
        """
        return self.models.get(state, {})

    def __repr__(self) -> str:
        """
        Provides a representation of the ModelManager's state, useful for debugging and logging.
        """
        return f"<ModelManager(general={len(self.models['general'])}, system={len(self.models['system'])}, chat={len(self.models['chat'])})>"



if __name__ == "__main__":
    # Assuming a configuration instance 'config' is available
    # This section would be used for testing or development purposes.
    from config import Config
    config = Config()
    model_manager = ModelManager(config)
    print(model_manager)
def load_model(model_path):
    import onnx
    import logging
    from datetime import datetime
    import traceback

    max_retries = 3
    retries = 0

    while True:
        try:
            model = onnx.load(model_path)
            return model
        except Exception as e:
            retries += 1
            diagnostics = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "model_path": model_path,
                "exception": traceback.format_exc(),
                "retry": retries
            }
            logging.error("Model loading failure: %s", diagnostics)
            if retries > max_retries:
                try:
                    from utils.logger import report_error
                    report_error(e)
                except Exception as report_exc:
                    logging.error("Error reporting failed: %s", report_exc)
                raise Exception("Max retries exceeded") from e
