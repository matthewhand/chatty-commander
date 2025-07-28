import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from model_manager import ModelManager
from config import Config
from openwakeword.model import Model

class TestModelLoading(unittest.TestCase):
    def setUp(self):
        """Setup configuration and model manager for testing."""
        self.config = Config()
        self.model_manager = ModelManager(self.config)

    def test_model_load(self):
        """Test if models are loaded correctly from all directories."""
        self.model_manager.reload_models('idle')
        self.assertGreater(len(self.model_manager.models['general']), 0, "General models should be loaded.")
        self.model_manager.reload_models('computer')
        self.assertGreater(len(self.model_manager.models['system']), 0, "System models should be loaded.")
        self.model_manager.reload_models('chatty')
        self.assertGreater(len(self.model_manager.models['chat']), 0, "Chat models should be loaded.")

    def test_model_types(self):
        """Ensure that models loaded are instances of the expected class."""
        for model_category in self.model_manager.models.values():
            for model in model_category.values():
                self.assertIsInstance(model, Model, "Loaded models must be instances of Model.")

    def test_invalid_model_path(self):
        """Test loading models from an invalid path should handle errors gracefully."""
        original_path = self.config.general_models_path
        self.config.general_models_path = "invalid/path/to/models"
        with self.assertRaises(Exception):
            self.model_manager.load_models()
            self.fail("Loading models from an invalid path should raise an exception.")
        # Restore the original path after the test
        self.config.general_models_path = original_path

if __name__ == '__main__':
    unittest.main()
