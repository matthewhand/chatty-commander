import json
import os
import unittest
from unittest.mock import MagicMock, patch
from chatty_commander.app.config import Config

class TestConfigReloadCallbacks(unittest.TestCase):
    def setUp(self):
        self.config_file = "test_config_reload.json"
        self.initial_data = {"general": {"debug_mode": True}, "commands": {}}
        with open(self.config_file, "w") as f:
            json.dump(self.initial_data, f)
        self.config = Config(self.config_file)

    def tearDown(self):
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    def test_reload_callback_triggered(self):
        callback = MagicMock()
        self.config.add_reload_callback(callback)

        # Modify file
        new_data = self.initial_data.copy()
        new_data["general"]["debug_mode"] = False
        with open(self.config_file, "w") as f:
            json.dump(new_data, f)

        self.config.reload_config()
        callback.assert_called_once()

        # Config properties might be cached or require property access to update
        # Check raw config data first
        self.assertFalse(self.config.config_data["general"]["debug_mode"])
        # Check property wrapper
        self.assertFalse(self.config.debug_mode)

    def test_remove_reload_callback(self):
        callback = MagicMock()
        self.config.add_reload_callback(callback)
        self.config.remove_reload_callback(callback)

        # Modify file
        new_data = self.initial_data.copy()
        new_data["general"]["debug_mode"] = False
        with open(self.config_file, "w") as f:
            json.dump(new_data, f)

        self.config.reload_config()
        callback.assert_not_called()

    def test_callback_exception_handled(self):
        bad_callback = MagicMock(side_effect=Exception("Boom"))
        good_callback = MagicMock()

        self.config.add_reload_callback(bad_callback)
        self.config.add_reload_callback(good_callback)

        # Modify file
        new_data = self.initial_data.copy()
        new_data["general"]["debug_mode"] = False
        with open(self.config_file, "w") as f:
            json.dump(new_data, f)

        # Should not raise
        self.config.reload_config()

        bad_callback.assert_called_once()
        good_callback.assert_called_once()
