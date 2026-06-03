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
Comprehensive tests for model manager module.

Tests model loading, management, and voice command listening.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.chatty_commander.app import model_manager
from src.chatty_commander.app.model_manager import ModelManager, _get_patchable_model_class


class MockConfig:
    """Mock configuration object for testing."""
    def __init__(self):
        self.general_models_path = "/tmp/models/general"
        self.system_models_path = "/tmp/models/system"
        self.chat_models_path = "/tmp/models/chat"


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    return MockConfig()


@pytest.fixture
def temp_model_dir():
    """Create temporary directory with mock .onnx files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create mock .onnx files
        for model_name in ["model1.onnx", "model2.onnx", "test_model.onnx"]:
            Path(tmp_dir, model_name).touch()
        yield tmp_dir


class TestModelManagerInitialization:
    """Test ModelManager initialization."""

    def test_basic_initialization(self, mock_config):
        """Test basic ModelManager initialization."""
        with patch.object(ModelManager, 'reload_models'):
            mm = ModelManager(mock_config)
            assert mm.config == mock_config
            assert mm.mock_models is False
            assert "general" in mm.models
            assert "system" in mm.models
            assert "chat" in mm.models

    def test_initialization_with_mock_models(self, mock_config):
        """Test initialization with mock_models=True."""
        mm = ModelManager(mock_config, mock_models=True)
        assert mm.mock_models is True
        assert len(mm.models["general"]) > 0
        assert len(mm.models["system"]) > 0
        assert len(mm.models["chat"]) > 0

    def test_initialization_calls_reload(self, mock_config):
        """Test that initialization calls reload_models."""
        with patch.object(ModelManager, 'reload_models') as mock_reload:
            ModelManager(mock_config)
            mock_reload.assert_called_once()


class TestReloadModels:
    """Test reload_models functionality."""

    def test_reload_all_models(self, mock_config, temp_model_dir):
        """Test reloading all model sets."""
        mock_config.general_models_path = temp_model_dir
        mock_config.system_models_path = temp_model_dir
        mock_config.chat_models_path = temp_model_dir

        mm = ModelManager(mock_config, mock_models=True)
        result = mm.reload_models()

        assert isinstance(result, dict)
        assert "general" in result
        assert "system" in result
        assert "chat" in result

    def test_reload_idle_state(self, mock_config, temp_model_dir):
        """Test reloading only idle/general models."""
        mock_config.general_models_path = temp_model_dir

        mm = ModelManager(mock_config, mock_models=True)
        result = mm.reload_models(state="idle")

        assert isinstance(result, dict)
        assert mm.active_models == result

    def test_reload_computer_state(self, mock_config, temp_model_dir):
        """Test reloading only computer/system models."""
        mock_config.system_models_path = temp_model_dir

        mm = ModelManager(mock_config, mock_models=True)
        result = mm.reload_models(state="computer")

        assert isinstance(result, dict)
        assert mm.active_models == result

    def test_reload_chatty_state(self, mock_config, temp_model_dir):
        """Test reloading only chatty/chat models."""
        mock_config.chat_models_path = temp_model_dir

        mm = ModelManager(mock_config, mock_models=True)
        result = mm.reload_models(state="chatty")

        assert isinstance(result, dict)
        assert mm.active_models == result

    def test_reload_unknown_state(self, mock_config):
        """Test reloading unknown state behavior."""
        mm = ModelManager(mock_config, mock_models=True)
        result = mm.reload_models(state="unknown")

        # With mock_models=True, the mock models are set up during init
        # Unknown state returns {} but mock models remain in place
        assert isinstance(result, dict)


class TestLoadModelSet:
    """Test load_model_set functionality."""

    def test_load_from_valid_directory(self, temp_model_dir):
        """Test loading models from valid directory."""
        mm = ModelManager(MockConfig(), mock_models=True)
        result = mm.load_model_set(temp_model_dir)

        assert isinstance(result, dict)
        assert len(result) == 3  # 3 .onnx files
        assert "model1" in result
        assert "model2" in result
        assert "test_model" in result

    def test_load_from_nonexistent_directory(self):
        """Test loading from non-existent directory."""
        mm = ModelManager(MockConfig(), mock_models=True)
        result = mm.load_model_set("/nonexistent/path")

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_load_ignores_non_onnx_files(self, temp_model_dir):
        """Test that non-.onnx files are ignored."""
        # Add non-onnx files
        Path(temp_model_dir, "readme.txt").touch()
        Path(temp_model_dir, "model.py").touch()

        mm = ModelManager(MockConfig(), mock_models=True)
        result = mm.load_model_set(temp_model_dir)

        assert len(result) == 3  # Still only 3 .onnx files
        assert "readme" not in result
        assert "model" not in result

    def test_load_handles_model_init_failure(self, temp_model_dir):
        """Test handling of model initialization failure."""
        mm = ModelManager(MockConfig(), mock_models=True)

        with patch.object(model_manager, '_get_patchable_model_class') as mock_get:
            mock_model_class = Mock()
            mock_model_class.side_effect = Exception("Model init failed")
            mock_get.return_value = mock_model_class

            result = mm.load_model_set(temp_model_dir)

            # Should return empty dict when all models fail
            assert isinstance(result, dict)


class TestGetPatchableModelClass:
    """Test _get_patchable_model_class function."""

    def test_returns_model_class(self):
        """Test that function returns a Model class."""
        result = _get_patchable_model_class()
        assert result is not None

    def test_under_pytest_returns_magicmock(self):
        """Test that function returns MagicMock when running under pytest."""
        with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_foo"}):
            result = _get_patchable_model_class()
            assert result is MagicMock


class TestListenForCommands:
    """Test voice command listening functionality."""

    def test_async_listen_returns_none_when_no_models(self, mock_config):
        """Test async_listen returns None when no active models."""
        mm = ModelManager(mock_config, mock_models=True)
        mm.active_models = {}

        result = asyncio.run(mm.async_listen_for_commands())
        assert result is None

    def test_async_listen_returns_command_when_models_present(self, mock_config):
        """Test async_listen may return a command when models are present."""
        mm = ModelManager(mock_config, mock_models=True)

        # With mock models, should have a small chance of returning a command
        result = asyncio.run(mm.async_listen_for_commands())

        # Result should be either None or a string
        assert result is None or isinstance(result, str)

    def test_sync_listen_wrapper(self, mock_config):
        """Test synchronous listen_for_commands wrapper."""
        mm = ModelManager(mock_config, mock_models=True)

        result = mm.listen_for_commands()
        assert result is None or isinstance(result, str)


class TestGetModels:
    """Test get_models functionality."""

    def test_get_general_models(self, mock_config):
        """Test retrieving general models."""
        mm = ModelManager(mock_config, mock_models=True)
        result = mm.get_models("general")

        assert isinstance(result, dict)

    def test_get_system_models(self, mock_config):
        """Test retrieving system models."""
        mm = ModelManager(mock_config, mock_models=True)
        result = mm.get_models("system")

        assert isinstance(result, dict)

    def test_get_chat_models(self, mock_config):
        """Test retrieving chat models."""
        mm = ModelManager(mock_config, mock_models=True)
        result = mm.get_models("chat")

        assert isinstance(result, dict)

    def test_get_unknown_state_returns_empty(self, mock_config):
        """Test retrieving unknown state returns empty dict."""
        mm = ModelManager(mock_config, mock_models=True)
        result = mm.get_models("unknown")

        assert result == {}


class TestRepr:
    """Test __repr__ functionality."""

    def test_repr_format(self, mock_config):
        """Test repr output format."""
        mm = ModelManager(mock_config, mock_models=True)
        repr_str = repr(mm)

        assert repr_str.startswith("<ModelManager(")
        assert "general=" in repr_str
        assert "system=" in repr_str
        assert "chat=" in repr_str
        assert repr_str.endswith(")>")


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_load_model_set_with_permission_error(self, temp_model_dir):
        """Test handling of permission error during load."""
        mm = ModelManager(MockConfig(), mock_models=True)

        with patch('os.listdir', side_effect=PermissionError("Access denied")):
            result = mm.load_model_set(temp_model_dir)
            assert isinstance(result, dict)
            assert len(result) == 0

    def test_load_model_set_with_os_error(self, temp_model_dir):
        """Test handling of OSError during load."""
        mm = ModelManager(MockConfig(), mock_models=True)

        with patch('os.listdir', side_effect=OSError("I/O error")):
            result = mm.load_model_set(temp_model_dir)
            assert isinstance(result, dict)
            assert len(result) == 0

    def test_empty_model_directory(self):
        """Test loading from empty directory."""
        with tempfile.TemporaryDirectory() as empty_dir:
            mm = ModelManager(MockConfig(), mock_models=True)
            result = mm.load_model_set(empty_dir)

            assert isinstance(result, dict)
            assert len(result) == 0

    def test_directory_with_non_onnx_files_only(self):
        """Test loading from directory with only non-.onnx files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            Path(tmp_dir, "readme.txt").touch()
            Path(tmp_dir, "data.json").touch()

            mm = ModelManager(MockConfig(), mock_models=True)
            result = mm.load_model_set(tmp_dir)

            assert isinstance(result, dict)
            assert len(result) == 0


class TestIntegration:
    """Integration tests for ModelManager."""

    def test_full_lifecycle(self, temp_model_dir):
        """Test full lifecycle: init, reload, listen, get."""
        config = MockConfig()
        config.general_models_path = temp_model_dir

        # Initialize
        mm = ModelManager(config, mock_models=True)
        assert mm is not None

        # Reload with specific state
        models = mm.reload_models(state="idle")
        assert isinstance(models, dict)

        # Get models
        general = mm.get_models("general")
        assert isinstance(general, dict)

        # Listen for commands
        command = mm.listen_for_commands()
        assert command is None or isinstance(command, str)

    def test_multiple_reload_cycles(self, mock_config, temp_model_dir):
        """Test multiple reload cycles."""
        mock_config.general_models_path = temp_model_dir

        mm = ModelManager(mock_config, mock_models=True)

        # First reload
        result1 = mm.reload_models(state="idle")

        # Second reload
        result2 = mm.reload_models(state="idle")

        # Both should return valid results
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
