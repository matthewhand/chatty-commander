# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
model_manager.py

This module manages the loading and utilization of machine learning models for the ChattyCommander application.
It dynamically loads models based on the application's current state, handles errors robustly, and supports dynamic model reloading.
"""

import os
import logging
import time
import random  # For simulating command detection in demo mode
from openwakeword.model import Model


class ModelManager:
    def __init__(self, config):
        """
        Initializes the ModelManager with configuration settings and an empty model cache.
        """
        logging.basicConfig(level=logging.INFO)  # Setup logging configuration
        self.config = config
        self.models = {"general": {}, "system": {}, "chat": {}}
        self.active_models = {}
        self.reload_models()

    def reload_models(self, state=None):
        """
        Reloads all models from the specified directories, enabling dynamic updates to model configurations.
        If state is provided, only loads models for that state.
        """
        if state is None or state == "idle":
            self.models["general"] = self.load_model_set(
                self.config.general_models_path
            )
            self.active_models = self.models["general"]
        elif state == "computer":
            self.models["system"] = self.load_model_set(self.config.system_models_path)
            self.active_models = self.models["system"]
        elif state == "chatty":
            self.models["chat"] = self.load_model_set(self.config.chat_models_path)
            self.active_models = self.models["chat"]

    def load_model_set(self, path):
        model_set = {}
        if not os.path.exists(path):
            logging.error(f"Model directory {path} does not exist.")
            return model_set

        for model_file in os.listdir(path):
            if model_file.endswith(".onnx"):
                model_path = os.path.join(path, model_file)
                model_name = os.path.splitext(model_file)[0]
                try:
                    model_instance = Model(wakeword_model_paths=[model_path])
                    model_set[model_name] = model_instance
                    logging.info(f"Loaded model '{model_name}' from '{model_path}'.")
                except Exception as e:
                    logging.error(
                        f"Error loading model '{model_name}' from '{model_path}': {e}"
                    )
        return model_set

    def listen_for_commands(self):
        """
        Simulates listening for voice commands using the loaded models.
        In a real implementation, this would process audio input and detect wake words.

        Returns:
            str or None: The detected command name if a command is recognized, None otherwise.
        """
        # This is a simplified simulation for demonstration purposes
        # In a real implementation, this would process audio and use the models to detect commands
        time.sleep(1)  # Simulate processing time

        # Demo mode: randomly return a command from active models occasionally
        if (
            self.active_models and random.random() < 0.05
        ):  # 5% chance of detecting a command
            return random.choice(list(self.active_models.keys()))
        return None

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
    from config import Config

    config = Config()
    model_manager = ModelManager(config)
    print(model_manager)
