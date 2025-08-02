import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from unittest.mock import MagicMock, patch

from config import Config
from model_manager import ModelManager


class TestModelLoading(unittest.TestCase):
    def setUp(self):
        """Setup configuration and model manager for testing."""
        self.config = Config()
        self.model_manager = ModelManager(self.config)

    def test_model_load(self):
        """Test if models are loaded correctly from all directories."""
        self.model_manager.reload_models('idle')
        self.assertGreater(
            len(self.model_manager.models['general']), 0, "General models should be loaded."
        )
        self.model_manager.reload_models('computer')
        self.assertGreater(
            len(self.model_manager.models['system']), 0, "System models should be loaded."
        )
        self.model_manager.reload_models('chatty')
        self.assertGreater(
            len(self.model_manager.models['chat']), 0, "Chat models should be loaded."
        )

    def test_model_types(self):
        """Ensure that models loaded are instances of the expected class."""
        self.model_manager.reload_models('idle')
        self.assertGreater(
            len(self.model_manager.models['general']), 0, "No general models loaded for type test."
        )
        for model_category in self.model_manager.models.values():
            for model in model_category.values():
                self.assertIsInstance(
                    model, MagicMock, "Loaded models must be instances of MagicMock."
                )

    def test_invalid_model_path(self):
        """Test loading models from an invalid path should handle errors gracefully."""
        original_path = self.config.general_models_path
        self.config.general_models_path = "invalid/path/to/models"
        self.model_manager.reload_models('idle')  # Should log error but not raise
        self.assertEqual(len(self.model_manager.models['general']), 0)
        self.config.general_models_path = original_path

    def test_load_model_set_error(self):
        """Test error handling in load_model_set."""
        with (
            patch('os.path.exists', return_value=True),
            patch('os.listdir', return_value=['invalid.onnx']),
            patch('model_manager.Model', side_effect=Exception('Load error')),
        ):
            models = self.model_manager.load_model_set('dummy_path')
            self.assertEqual(len(models), 0)

    def test_listen_for_commands_detect(self):
        """Test listen_for_commands when a command is detected."""
        self.model_manager.active_models = {'cmd1': 'model1', 'cmd2': 'model2'}
        with (
            patch('random.random', return_value=0.01),
            patch('random.choice', return_value='cmd1'),
            patch('time.sleep'),
        ):
            result = self.model_manager.listen_for_commands()
            self.assertEqual(result, 'cmd1')

    def test_listen_for_commands_no_detect(self):
        """Test listen_for_commands when no command is detected."""
        self.model_manager.active_models = {'cmd1': 'model1'}
        with patch('random.random', return_value=0.1), patch('time.sleep'):
            result = self.model_manager.listen_for_commands()
            self.assertIsNone(result)

    def test_get_models(self):
        """Test get_models method."""
        self.model_manager.models['test'] = {'model1': 'instance'}
        result = self.model_manager.get_models('test')
        self.assertEqual(result, {'model1': 'instance'})
        self.assertEqual(self.model_manager.get_models('nonexistent'), {})

    def test_repr(self):
        """Test __repr__ method."""
        self.model_manager.models = {'general': {'a': 1, 'b': 2}, 'system': {}, 'chat': {'c': 3}}
        self.assertEqual(repr(self.model_manager), '<ModelManager(general=2, system=0, chat=1)>')


if __name__ == '__main__':
    unittest.main()
