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

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager


class TestModelManager:
    def test_init(self):
        config = Config()
        mm = ModelManager(config)
        assert hasattr(mm, "config")
        assert hasattr(mm, "models")

    def test_reload_models(self):
        config = Config()
        mm = ModelManager(config)
        with patch(
            "chatty_commander.app.model_manager.Model", return_value=MagicMock()
        ):
            models = mm.reload_models("idle")
            assert isinstance(models, dict)

    def test_reload_models_invalid_state(self):
        config = Config()
        mm = ModelManager(config)
        with patch(
            "chatty_commander.app.model_manager.Model", return_value=MagicMock()
        ):
            models = mm.reload_models("invalid")
            assert models == {}

    def test_listen_for_commands(self):
        config = Config()
        mm = ModelManager(config)
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = mm.listen_for_commands()
        assert result is None or isinstance(result, str)

        # Should not raise, but returns None or str
        result = asyncio.run(mm.async_listen_for_commands())
        assert result is None or isinstance(result, str)

    def test_hot_reload_detects_new_model(self, tmp_path):
        cfg = Config()
        model_dir = tmp_path / "models"
        model_dir.mkdir()
        cfg.general_models_path = str(model_dir)
        (model_dir / "first.onnx").write_text("dummy")
        mm = ModelManager(cfg)
        assert "first" in mm.models["general"]
        (model_dir / "second.onnx").write_text("dummy2")

        async def _run():
            await asyncio.gather(
                mm.async_listen_for_commands(),
                asyncio.to_thread(mm.reload_models, "idle"),
            )

        asyncio.run(_run())
        assert "second" in mm.models["general"]

    def test_repr(self):
        """Test __repr__ method"""
        config = Config()
        mm = ModelManager(config)

        # Mock some models
        mm.models = {
            "general": {"model1": MagicMock(), "model2": MagicMock()},
            "system": {"model3": MagicMock()},
            "chat": {},
        }

        repr_str = repr(mm)
        assert "ModelManager" in repr_str
        assert "general=2" in repr_str
        assert "system=1" in repr_str
        assert "chat=0" in repr_str

    # Additional comprehensive tests to improve coverage to 80%+

    def test_model_manager_reload_models_all_states(self):
        """Test reload_models for all states when no specific state is provided."""
        config = Config()
        config.general_models_path = "test_general"
        config.system_models_path = "test_system"
        config.chat_models_path = "test_chat"

        mm = ModelManager(config)

        with patch.object(mm, "load_model_set") as mock_load:
            mock_load.return_value = {"test_model": MagicMock()}

            result = mm.reload_models()

            # Should have called load_model_set for all three model types
            assert mock_load.call_count == 3
            mock_load.assert_any_call("test_general")
            mock_load.assert_any_call("test_system")
            mock_load.assert_any_call("test_chat")

            # Should return all models
            assert "general" in result
            assert "system" in result
            assert "chat" in result

            # active_models should be set to general models
            assert mm.active_models == result["general"]

    def test_model_manager_reload_models_idle_state(self):
        """Test reload_models for idle state specifically."""
        config = Config()
        config.general_models_path = "test_general"

        mm = ModelManager(config)

        mock_model = MagicMock()
        with patch.object(mm, "load_model_set") as mock_load:
            mock_load.return_value = {"test_model": mock_model}

            result = mm.reload_models("idle")

            # Should have called load_model_set only for general models
            mock_load.assert_called_once_with("test_general")

            # Should return general models
            assert result == {"test_model": mock_model}

            # active_models should be set to general models
            assert mm.active_models == result

    def test_model_manager_reload_models_computer_state(self):
        """Test reload_models for computer state specifically."""
        config = Config()
        config.system_models_path = "test_system"

        mm = ModelManager(config)

        mock_model = MagicMock()
        with patch.object(mm, "load_model_set") as mock_load:
            mock_load.return_value = {"test_model": mock_model}

            result = mm.reload_models("computer")

            # Should have called load_model_set only for system models
            mock_load.assert_called_once_with("test_system")

            # Should return system models
            assert result == {"test_model": mock_model}

            # active_models should be set to system models
            assert mm.active_models == result

    def test_model_manager_reload_models_chatty_state(self):
        """Test reload_models for chatty state specifically."""
        config = Config()
        config.chat_models_path = "test_chat"

        mm = ModelManager(config)

        mock_model = MagicMock()
        with patch.object(mm, "load_model_set") as mock_load:
            mock_load.return_value = {"test_model": mock_model}

            result = mm.reload_models("chatty")

            # Should have called load_model_set only for chat models
            mock_load.assert_called_once_with("test_chat")

            # Should return chat models
            assert result == {"test_model": mock_model}

            # active_models should be set to chat models
            assert mm.active_models == result

    def test_model_manager_reload_models_invalid_state(self):
        """Test reload_models with invalid state."""
        config = Config()
        mm = ModelManager(config)

        result = mm.reload_models("invalid_state")
        assert result == {}

    def test_model_manager_load_model_set_directory_not_exist(self):
        """Test load_model_set when directory doesn't exist."""
        config = Config()
        mm = ModelManager(config)

        with patch("os.path.exists", return_value=False):
            with patch("logging.error") as mock_error:
                result = mm.load_model_set("/nonexistent/path")
                assert result == {}
                mock_error.assert_called_once_with(
                    "Model directory /nonexistent/path does not exist."
                )

    def test_model_manager_load_model_set_directory_list_error(self):
        """Test load_model_set when directory listing fails."""
        config = Config()
        mm = ModelManager(config)

        with patch("os.path.exists", return_value=True):
            with patch("os.listdir", side_effect=OSError("Permission denied")):
                with patch("logging.error") as mock_error:
                    result = mm.load_model_set("/test/path")
                    assert result == {}
                    mock_error.assert_called_once()

    def test_model_manager_load_model_set_no_onnx_files(self):
        """Test load_model_set when directory has no .onnx files."""
        config = Config()
        mm = ModelManager(config)

        with patch("os.path.exists", return_value=True):
            with patch("os.listdir", return_value=["file1.txt", "file2.jpg"]):
                result = mm.load_model_set("/test/path")
                assert result == {}

    def test_model_manager_load_model_set_model_file_not_exist(self):
        """Test load_model_set when model file doesn't exist."""
        config = Config()
        mm = ModelManager(config)

        def mock_exists(path):
            # Directory exists, but model file doesn't
            if path == "/test/path":
                return True
            elif path == "/test/path/model1.onnx":
                return False
            return False

        with patch("os.path.exists", side_effect=mock_exists):
            with patch("os.listdir", return_value=["model1.onnx"]):
                with patch("logging.warning") as mock_warning:
                    result = mm.load_model_set("/test/path")
                    assert result == {}
                    mock_warning.assert_called_once()

    def test_model_manager_load_model_set_model_loading_failure(self):
        """Test load_model_set when model loading fails."""
        config = Config()
        mm = ModelManager(config)

        # Mock pyautogui import to avoid X11 display issues
        with patch.dict("sys.modules", {"pyautogui": MagicMock()}):
            # Create a failing model class that raises an exception
            class FailingModel:
                def __init__(self, path):
                    raise Exception("Load failed")

            # We need to mock the global model_manager module to patch the Model class
            mock_module = MagicMock()
            mock_module.Model = FailingModel

            with patch("os.path.exists", return_value=True):
                with patch("os.listdir", return_value=["model1.onnx"]):
                    with patch("sys.modules", {"model_manager": mock_module}):
                        # Use caplog fixture to capture logging
                        with patch("logging.getLogger") as mock_get_logger:
                            mock_logger = MagicMock()
                            mock_get_logger.return_value = mock_logger
                            result = mm.load_model_set("/test/path")
                            assert result == {}
                            mock_logger.error.assert_called_once()

    def test_model_manager_load_model_set_successful_load(self):
        """Test load_model_set successful model loading."""
        config = Config()
        mm = ModelManager(config)

        mock_model = MagicMock()

        # Mock pyautogui import to avoid X11 display issues
        with patch.dict("sys.modules", {"pyautogui": MagicMock()}):
            with patch("os.path.exists", return_value=True):
                with patch("os.listdir", return_value=["model1.onnx", "model2.onnx"]):
                    with patch("os.path.exists", return_value=True):
                        with patch(
                            "src.chatty_commander.app.model_manager._get_patchable_model_class",
                            return_value=lambda path: mock_model,
                        ):
                            with patch("logging.info") as mock_info:
                                result = mm.load_model_set("/test/path")
                                assert len(result) == 2
                                assert "model1" in result
                                assert "model2" in result
                                assert mock_info.call_count == 2

    def test_get_patchable_model_class_sys_modules(self):
        """Test _get_patchable_model_class with sys.modules priority."""
        # Mock pyautogui import to avoid X11 display issues
        with patch.dict("sys.modules", {"pyautogui": MagicMock()}):
            from src.chatty_commander.app.model_manager import (
                _get_patchable_model_class,
            )

            mock_model_class = MagicMock()
            mock_module = MagicMock()
            mock_module.Model = mock_model_class

            with patch("sys.modules", {"model_manager": mock_module}):
                result = _get_patchable_model_class()
                assert result == mock_model_class

    def test_get_patchable_model_class_importlib(self):
        """Test _get_patchable_model_class with importlib fallback."""
        # Mock pyautogui import to avoid X11 display issues
        with patch.dict("sys.modules", {"pyautogui": MagicMock()}):
            from src.chatty_commander.app.model_manager import (
                _get_patchable_model_class,
            )

            # Create a concrete class instead of MagicMock instance
            class MockModelClass:
                pass

            mock_module = MagicMock()
            mock_module.Model = MockModelClass

            # Clear PYTEST_CURRENT_TEST to avoid pytest fallback and mock os.environ
            with patch("os.environ", {}):
                with patch("sys.modules", {}):
                    with patch("importlib.import_module", return_value=mock_module):
                        result = _get_patchable_model_class()
                        # Check that we get the Model class from the mock module
                        assert result is MockModelClass

    def test_get_patchable_model_class_pytest(self):
        """Test _get_patchable_model_class with pytest MagicMock."""
        # Import MagicMock first to avoid scope issues
        from unittest.mock import MagicMock

        # Mock pyautogui import to avoid X11 display issues
        with patch.dict("sys.modules", {"pyautogui": MagicMock()}):
            from src.chatty_commander.app.model_manager import (
                _get_patchable_model_class,
            )

            with patch("sys.modules", {}):
                with patch(
                    "importlib.import_module", side_effect=Exception("Import failed")
                ):
                    with patch.dict(
                        os.environ, {"PYTEST_CURRENT_TEST": "test_running"}
                    ):
                        # This should return the MagicMock class itself
                        result = _get_patchable_model_class()
                        assert result == MagicMock

    def test_get_patchable_model_class_fallback(self):
        """Test _get_patchable_model_class with local fallback."""
        # Mock pyautogui import to avoid X11 display issues
        with patch.dict("sys.modules", {"pyautogui": MagicMock()}):
            from src.chatty_commander.app.model_manager import (
                Model,
                _get_patchable_model_class,
            )

            # Ensure we get the local Model class
            with patch("sys.modules", {}):
                with patch(
                    "importlib.import_module", side_effect=Exception("Import failed")
                ):
                    with patch.dict(os.environ, {}, clear=True):
                        result = _get_patchable_model_class()
                        assert result == Model

    def test_model_manager_async_listen_for_commands_no_models(self):
        """Test async_listen_for_commands when no active models."""
        config = Config()
        mm = ModelManager(config)
        mm.active_models = {}

        result = asyncio.run(mm.async_listen_for_commands())
        assert result is None

    def test_model_manager_async_listen_for_commands_with_models_no_detection(self):
        """Test async_listen_for_commands with models but no detection (random >= 0.05)."""
        config = Config()
        mm = ModelManager(config)
        mm.active_models = {"model1": MagicMock(), "model2": MagicMock()}

        with patch("random.random", return_value=0.1):  # Above threshold
            result = asyncio.run(mm.async_listen_for_commands())
            assert result is None

    def test_model_manager_async_listen_for_commands_with_detection(self):
        """Test async_listen_for_commands with successful detection."""
        config = Config()
        mm = ModelManager(config)
        mm.active_models = {"model1": MagicMock(), "model2": MagicMock()}

        with patch("random.random", return_value=0.01):  # Below threshold
            with patch("random.choice", return_value="model1"):
                result = asyncio.run(mm.async_listen_for_commands())
                assert result == "model1"

    def test_model_manager_get_models(self):
        """Test get_models method."""
        config = Config()
        mm = ModelManager(config)

        mock_model = MagicMock()
        mm.models = {
            "general": {"model1": mock_model},
            "system": {"model2": mock_model},
            "chat": {},
        }

        result = mm.get_models("general")
        assert result == {"model1": mock_model}

        result = mm.get_models("system")
        assert result == {"model2": mock_model}

        result = mm.get_models("chat")
        assert result == {}

        result = mm.get_models("nonexistent")
        assert result == {}
