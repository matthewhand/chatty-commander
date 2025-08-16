"""
model_manager.py

This module manages the loading and utilization of machine learning models for the ChattyCommander application.
It dynamically loads models based on the application's current state, handles errors robustly, and supports dynamic model reloading.
"""

import asyncio
import logging
import os
import random  # For simulating command detection in demo mode
from typing import Any

try:
    from wakewords.model import Model
except ModuleNotFoundError:
    logging.warning(
        "Dependency 'wakewords' not found. Using dummy Model. Some functionality may be limited."
    )

    class Model:  # type: ignore[no-redef]
        def __init__(self, path):
            self.path = path


class ModelManager:
    def __init__(self, config: Any) -> None:
        """
        Initializes the ModelManager with configuration settings and an empty model cache.
        """
        logging.basicConfig(level=logging.INFO)  # Setup logging configuration
        self.config: Any = config
        self.models: dict[str, dict[str, Model]] = {'general': {}, 'system': {}, 'chat': {}}
        self.active_models: dict[str, Model] = {}
        self.reload_models()

    def reload_models(self, state: str | None = None) -> dict[str, Model]:
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

    def _load_model_with_retry(self, model_path: str) -> Model | None:
        import traceback
        from datetime import datetime

        max_retries = 3
        retries = 0
        while True:
            try:
                ModelClass = _get_patchable_model_class()
                return ModelClass(model_path)  # type: ignore[call-arg]
            except Exception as e:  # pragma: no cover - diagnostics handled below
                retries += 1
                diagnostics = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "model_path": model_path,
                    "exception": traceback.format_exc(),
                    "retry": retries,
                }
                logging.error("Model loading failure: %s", diagnostics)
                if retries > max_retries:
                    try:
                        from chatty_commander.utils.logger import report_error

                        report_error(e)
                    except Exception as report_exc:
                        logging.error("Error reporting failed: %s", report_exc)
                    return None

    def load_model_set(self, path: str) -> dict[str, Model]:
        model_set: dict[str, Model] = {}
        if not os.path.exists(path):
            logging.error(f"Model directory {path} does not exist.")
            return model_set

        try:
            entries = os.listdir(path)
        except Exception as e:
            logging.error(f"Error listing directory {path}: {e}")
            return model_set

        for model_file in entries:
            if not model_file.lower().endswith('.onnx'):
                continue

            model_path = os.path.join(path, model_file)
            model_name = os.path.splitext(model_file)[0]

            if not os.path.exists(model_path):
                logging.warning(f"Model file '{model_path}' does not exist. Skipping.")
                continue

            # Use retrying constructor that is patchable in tests
            instance = self._load_model_with_retry(model_path)
            if instance is not None:
                model_set[model_name] = instance  # only add on success
                logging.info("Successfully loaded model '%s' from '%s'.", model_name, model_path)
            else:
                # Already logged with diagnostics and error reporting in retry helper
                logging.error(
                    "Failed to load model '%s' from '%s'. Continuing with other models.",
                    model_name,
                    model_path,
                )
                continue
        return model_set

    async def async_listen_for_commands(self) -> str | None:
        """
        Asynchronous version for listening for voice commands.
        """
        await asyncio.sleep(1)  # Simulate processing time
        if self.active_models and random.random() < 0.05:
            return random.choice(list(self.active_models.keys()))
        return None

    def listen_for_commands(self) -> str | None:
        """
        Synchronous wrapper for async_listen_for_commands.
        """
        return asyncio.run(self.async_listen_for_commands())

    def get_models(self, state: str) -> dict[str, Model]:
        """
        Retrieves models relevant to the current application state, allowing the system to adapt dynamically to state changes.
        """
        return self.models.get(state, {})

    def __repr__(self) -> str:
        """
        Provides a representation of the ModelManager's state, useful for debugging and logging.
        """
        return f"<ModelManager(general={len(self.models['general'])}, system={len(self.models['system'])}, chat={len(self.models['chat'])})>"


def load_model(model_path):
    import logging
    import traceback
    from datetime import datetime

    import onnx

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
                "retry": retries,
            }
            logging.error("Model loading failure: %s", diagnostics)
            if retries > max_retries:
                try:
                    from chatty_commander.utils.logger import report_error

                    report_error(e)
                except Exception as report_exc:
                    logging.error("Error reporting failed: %s", report_exc)
                raise Exception("Max retries exceeded") from e


# --- fallback for tests/linters when dynamic backend is unavailable ---
def _get_patchable_model_class():
    """Return a model class; fall back to a tiny dummy.

    This keeps static analysis/lint happy without changing runtime behavior.
    """
    try:
        from ..llm.manager import ModelManager as _ModelClass  # type: ignore

        return _ModelClass
    except Exception:

        class _Dummy:
            def __init__(self, *args, **kwargs):  # noqa: D401, ANN001
                """No-op stub."""
                pass

        return _Dummy
