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

import os
import sys
import tempfile
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager


class TestModelLoading(unittest.TestCase):
    def setUp(self):
        """Setup configuration and model manager for testing."""
        self._model_patch = patch(
            "chatty_commander.app.model_manager._get_patchable_model_class",
            return_value=MagicMock,
        )
        self._model_patch.start()
        self.config = Config()
        self.model_manager = ModelManager(self.config)

    @patch("os.path.exists", return_value=True)
    @patch("os.listdir", return_value=["dummy.onnx"])
    def test_model_load(self, mock_listdir, mock_exists):
        """Test if models are loaded correctly from all directories."""
        self.model_manager.reload_models("idle")
        self.assertGreater(
            len(self.model_manager.models["general"]),
            0,
            "General models should be loaded.",
        )
        self.model_manager.reload_models("computer")
        self.assertGreater(
            len(self.model_manager.models["system"]),
            0,
            "System models should be loaded.",
        )
        self.model_manager.reload_models("chatty")
        self.assertGreater(
            len(self.model_manager.models["chat"]), 0, "Chat models should be loaded."
        )

    @patch("os.path.exists", return_value=True)
    @patch("os.listdir", return_value=["dummy.onnx"])
    def test_model_types(self, mock_listdir, mock_exists):
        """Ensure that models loaded are instances of the expected class."""
        self.model_manager.reload_models("idle")
        self.assertGreater(
            len(self.model_manager.models["general"]),
            0,
            "No general models loaded for type test.",
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
        self.model_manager.reload_models("idle")  # Should log error but not raise
        self.assertEqual(len(self.model_manager.models["general"]), 0)
        self.config.general_models_path = original_path

    def test_load_model_set_error(self):
        """Test error handling in load_model_set."""
        with (
            patch("os.path.exists", return_value=True),
            patch("os.listdir", return_value=["invalid.onnx"]),
            patch(
                "chatty_commander.app.model_manager._get_patchable_model_class",
                side_effect=Exception("Load error"),
            ),
        ):
            models = self.model_manager.load_model_set("dummy_path")
            self.assertEqual(len(models), 0)

    def test_listen_for_commands_detect(self):
        """Test listen_for_commands when a command is detected."""
        self.model_manager.active_models = {"cmd1": "model1", "cmd2": "model2"}
        with (
            patch("random.random", return_value=0.01),
            patch("random.choice", return_value="cmd1"),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            result = self.model_manager.listen_for_commands()
            self.assertEqual(result, "cmd1")

    def test_listen_for_commands_no_detect(self):
        """Test listen_for_commands when no command is detected."""
        self.model_manager.active_models = {"cmd1": "model1"}
        with (
            patch("random.random", return_value=0.1),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            result = self.model_manager.listen_for_commands()
            self.assertIsNone(result)

    def test_get_models(self):
        """Test get_models method."""
        self.model_manager.models["test"] = {"model1": "instance"}
        result = self.model_manager.get_models("test")
        self.assertEqual(result, {"model1": "instance"})
        self.assertEqual(self.model_manager.get_models("nonexistent"), {})

    def tearDown(self):
        self._model_patch.stop()

    def test_repr(self):
        """Test __repr__ method."""
        self.model_manager.models = {
            "general": {"a": 1, "b": 2},
            "system": {},
            "chat": {"c": 3},
        }
        self.assertEqual(
            repr(self.model_manager), "<ModelManager(general=2, system=0, chat=1)>"
        )

    def test_hot_reload(self):
        """Test hot reload functionality by manually reloading models."""
        general = Path(tempfile.mkdtemp())
        system = Path(tempfile.mkdtemp())
        chat = Path(tempfile.mkdtemp())
        self.config.general_models_path = str(general)
        self.config.system_models_path = str(system)
        self.config.chat_models_path = str(chat)
        mm = ModelManager(self.config)

        # Create a new model file and reload
        (general / "new.onnx").write_text("")
        mm.reload_models("idle")
        self.assertIn("new", mm.models["general"])


if __name__ == "__main__":
    unittest.main()
