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
Additional comprehensive tests for core modules: compat.py, command_executor.py, model_manager.py.

Extends existing test coverage with edge cases, error scenarios, and integration tests.
"""

import asyncio
import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.model_manager import ModelManager, _get_patchable_model_class
from chatty_commander.compat import ALIASES, expose
from chatty_commander.exceptions import DependencyError, ExecutionError, ValidationError


class TestCompatibilityLayer:
    """Test the compatibility layer functionality."""

    def test_aliases_mapping(self):
        """Test that ALIASES contains correct mappings."""
        expected_aliases = {
            "config": "chatty_commander.app.config",
            "model_manager": "chatty_commander.app.model_manager",
            "web_mode": "chatty_commander.web.web_mode",
        }
        assert ALIASES == expected_aliases

    def test_expose_function_with_aliases(self):
        """Test expose function with known aliases."""
        # Test config alias
        config_module = expose("config")
        assert hasattr(config_module, "Config")

        # Test model_manager alias
        model_manager_module = expose("model_manager")
        assert hasattr(model_manager_module, "ModelManager")

        # Test web_mode alias
        web_mode_module = expose("web_mode")
        assert web_mode_module is not None

    def test_expose_function_passthrough(self):
        """Test expose function with direct module names."""
        # Test with direct module name (should pass through)
        sys_module = expose("sys")
        import sys
        assert sys_module is sys

        # Test with non-existent module
        with pytest.raises(ModuleNotFoundError):
            expose("nonexistent_module_xyz123")

    def test_expose_function_with_importlib_behavior(self):
        """Test expose function uses importlib correctly."""
        with patch("chatty_commander.compat.importlib") as mock_importlib:
            mock_importlib.import_module.return_value = "mocked_module"

            result = expose("some_module")

            mock_importlib.import_module.assert_called_once_with("some_module")
            assert result == "mocked_module"

    def test_expose_function_error_handling(self):
        """Test expose function handles import errors gracefully."""
        with patch("chatty_commander.compat.importlib") as mock_importlib:
            mock_importlib.import_module.side_effect = ImportError("Module not found")

            # Should try alias first, then direct import
            result = expose("config")  # This should work despite the mock

            # In real usage, the alias should resolve first
            assert result is not None

    def test_expose_function_with_nested_modules(self):
        """Test expose function with nested module paths."""
        # Test with a nested module path
        json_module = expose("json")
        import json
        assert json_module is json

    def test_aliases_are_comprehensive(self):
        """Test that aliases cover all major modules."""
        # Check that all aliases point to existing modules
        for alias_name, target_path in ALIASES.items():
            try:
                expose(alias_name)
            except ImportError as e:
                pytest.fail(f"Alias '{alias_name}' -> '{target_path}' failed to import: {e}")


class TestCommandExecutorExtended:
    """Extended tests for CommandExecutor functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing."""
        config = Mock()
        config.model_actions = {
            "test_keypress": {"action": "keypress", "keys": "ctrl+c"},
            "test_url": {"action": "url", "url": "https://example.com"},
            "test_shell": {"action": "shell", "cmd": "echo 'hello'"},
            "test_custom": {"action": "custom_message", "message": "Custom message"},
            "old_format_keypress": {"keypress": "ctrl+v"},
            "old_format_url": {"url": "https://test.com"},
            "old_format_shell": {"shell": "ls -la"},
            "invalid_action": {"action": "invalid_action_type"},
            "missing_keys": {"action": "keypress"},
            "missing_url": {"action": "url"},
            "missing_cmd": {"action": "shell"},
            "missing_message": {"action": "custom_message"},
        }
        return config

    @pytest.fixture
    def mock_model_manager(self):
        """Create mock model manager."""
        return Mock()

    @pytest.fixture
    def mock_state_manager(self):
        """Create mock state manager."""
        return Mock()

    @pytest.fixture
    def command_executor(self, mock_config, mock_model_manager, mock_state_manager):
        """Create CommandExecutor instance."""
        return CommandExecutor(mock_config, mock_model_manager, mock_state_manager)

    def test_command_executor_initialization(self, command_executor, mock_config, mock_model_manager, mock_state_manager):
        """Test CommandExecutor initialization."""
        assert command_executor.config == mock_config
        assert command_executor.model_manager == mock_model_manager
        assert command_executor.state_manager == mock_state_manager
        assert command_executor.last_command is None

    def test_execute_command_invalid_name(self, command_executor):
        """Test executing command with invalid name."""
        # Test None command name
        result = command_executor.execute_command(None)
        assert result is False

        # Test empty command name
        result = command_executor.execute_command("")
        assert result is False

        # Test whitespace only
        result = command_executor.execute_command("   ")
        assert result is False

    def test_validate_command_success(self, command_executor):
        """Test command validation with valid commands."""
        # Test new format commands
        assert command_executor.validate_command("test_keypress") is True
        assert command_executor.validate_command("test_url") is True
        assert command_executor.validate_command("test_shell") is True
        assert command_executor.validate_command("test_custom") is True

        # Test old format commands
        assert command_executor.validate_command("old_format_keypress") is True
        assert command_executor.validate_command("old_format_url") is True
        assert command_executor.validate_command("old_format_shell") is True

    def test_validate_command_invalid_action_type(self, command_executor):
        """Test command validation with invalid action type."""
        with pytest.raises(ValidationError) as exc_info:
            command_executor.validate_command("invalid_action")

        assert "invalid action type" in str(exc_info.value)

    def test_validate_command_missing_required_fields(self, command_executor):
        """Test command validation with missing required fields."""
        # Should return False for missing fields (not raise ValidationError)
        assert command_executor.validate_command("missing_keys") is False
        assert command_executor.validate_command("missing_url") is False
        assert command_executor.validate_command("missing_cmd") is False
        assert command_executor.validate_command("missing_message") is False

    def test_validate_command_nonexistent(self, command_executor):
        """Test command validation with non-existent command."""
        assert command_executor.validate_command("nonexistent_command") is False

    def test_pre_execute_hook(self, command_executor):
        """Test pre-execute hook functionality."""
        command_executor.pre_execute_hook("test_command")
        assert command_executor.last_command == "test_command"

    def test_post_execute_hook(self, command_executor):
        """Test post-execute hook functionality."""
        # Should not raise any exceptions
        command_executor.post_execute_hook("test_command")

    def test_execute_keybinding_success(self, command_executor):
        """Test successful keybinding execution."""
        with patch("chatty_commander.app.command_executor.pyautogui") as mock_pyautogui:
            mock_pyautogui.hotkey = Mock()

            command_executor._execute_keybinding("test_cmd", "ctrl+c")

            mock_pyautogui.hotkey.assert_called_once_with("ctrl", "c")

    def test_execute_keybinding_with_plus_syntax(self, command_executor):
        """Test keybinding execution with plus-separated syntax."""
        with patch("chatty_commander.app.command_executor.pyautogui") as mock_pyautogui:
            mock_pyautogui.hotkey = Mock()

            command_executor._execute_keybinding("test_cmd", "ctrl+shift+t")

            mock_pyautogui.hotkey.assert_called_once_with("ctrl", "shift", "t")

    def test_execute_keybinding_single_key(self, command_executor):
        """Test keybinding execution with single key."""
        with patch("chatty_commander.app.command_executor.pyautogui") as mock_pyautogui:
            mock_pyautogui.press = Mock()

            command_executor._execute_keybinding("test_cmd", "enter")

            mock_pyautogui.press.assert_called_once_with("enter")

    def test_execute_keybinding_list_keys(self, command_executor):
        """Test keybinding execution with list of keys."""
        with patch("chatty_commander.app.command_executor.pyautogui") as mock_pyautogui:
            mock_pyautogui.hotkey = Mock()

            command_executor._execute_keybinding("test_cmd", ["ctrl", "c"])

            mock_pyautogui.hotkey.assert_called_once_with("ctrl", "c")

    def test_execute_keybinding_pyautogui_unavailable(self, command_executor):
        """Test keybinding execution when pyautogui is unavailable."""
        with patch("chatty_commander.app.command_executor.pyautogui", None):
            with pytest.raises(DependencyError) as exc_info:
                command_executor._execute_keybinding("test_cmd", "ctrl+c")

            assert "pyautogui is not installed" in str(exc_info.value)

    def test_execute_keybinding_pyautogui_error(self, command_executor):
        """Test keybinding execution with pyautogui error."""
        with patch("chatty_commander.app.command_executor.pyautogui") as mock_pyautogui:
            mock_pyautogui.hotkey.side_effect = Exception("Hotkey failed")

            with pytest.raises(ExecutionError) as exc_info:
                command_executor._execute_keybinding("test_cmd", "ctrl+c")

            assert "Failed to execute keybinding" in str(exc_info.value)

    def test_execute_url_success(self, command_executor):
        """Test successful URL execution."""
        with patch("chatty_commander.app.command_executor.requests") as mock_requests:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_requests.get.return_value = mock_response

            command_executor._execute_url("test_cmd", "https://example.com")

            mock_requests.get.assert_called_once_with("https://example.com")

    def test_execute_url_missing_url(self, command_executor):
        """Test URL execution with missing URL."""
        with patch("chatty_commander.app.command_executor.requests") as mock_requests:
            command_executor._execute_url("test_cmd", "")

            # Should not call requests.get with empty URL
            mock_requests.get.assert_not_called()

    def test_execute_url_requests_unavailable(self, command_executor):
        """Test URL execution when requests is unavailable."""
        with patch("chatty_commander.app.command_executor.requests", None):
            with pytest.raises(DependencyError) as exc_info:
                command_executor._execute_url("test_cmd", "https://example.com")

            assert "requests not available" in str(exc_info.value)

    def test_execute_url_http_error(self, command_executor):
        """Test URL execution with HTTP error."""
        with patch("chatty_commander.app.command_executor.requests") as mock_requests:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_requests.get.return_value = mock_response

            command_executor._execute_url("test_cmd", "https://example.com")

            # Should not raise exception for HTTP errors, just log them

    def test_execute_url_requests_error(self, command_executor):
        """Test URL execution with requests error."""
        with patch("chatty_commander.app.command_executor.requests") as mock_requests:
            mock_requests.get.side_effect = Exception("Network error")

            with pytest.raises(ExecutionError) as exc_info:
                command_executor._execute_url("test_cmd", "https://example.com")

            assert "Failed to execute URL" in str(exc_info.value)

    def test_execute_shell_success(self, command_executor):
        """Test successful shell command execution."""
        with patch("chatty_commander.app.command_executor.subprocess") as mock_subprocess:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "command output"
            mock_result.stderr = ""
            mock_subprocess.run.return_value = mock_result

            result = command_executor._execute_shell("test_cmd", "echo hello")

            assert result is True
            mock_subprocess.run.assert_called_once()

    def test_execute_shell_missing_command(self, command_executor):
        """Test shell execution with missing command."""
        result = command_executor._execute_shell("test_cmd", "")
        assert result is False

    def test_execute_shell_failure(self, command_executor):
        """Test shell command execution failure."""
        with patch("chatty_commander.app.command_executor.subprocess") as mock_subprocess:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "command failed"
            mock_subprocess.run.return_value = mock_result

            result = command_executor._execute_shell("test_cmd", "false")

            assert result is False

    def test_execute_shell_timeout(self, command_executor):
        """Test shell command timeout."""
        with patch("chatty_commander.app.command_executor.subprocess") as mock_subprocess:
            mock_subprocess.run.side_effect = TimeoutError("Command timed out")

            result = command_executor._execute_shell("test_cmd", "sleep 30")

            assert result is False

    def test_execute_shell_execution_error(self, command_executor):
        """Test shell command execution error."""
        with patch("chatty_commander.app.command_executor.subprocess") as mock_subprocess:
            mock_subprocess.run.side_effect = Exception("Shell execution failed")

            with pytest.raises(ExecutionError) as exc_info:
                command_executor._execute_shell("test_cmd", "invalid_command")

            assert "Shell execution failed" in str(exc_info.value)

    def test_execute_custom_message_success(self, command_executor):
        """Test custom message execution."""
        command_executor._execute_custom_message("test_cmd", "Custom message")

        # Should complete without error

    def test_execute_custom_message_missing(self, command_executor):
        """Test custom message execution with missing message."""
        command_executor._execute_custom_message("test_cmd", "")

        # Should complete without error

    def test_report_error_functionality(self, command_executor):
        """Test error reporting functionality."""
        with patch("chatty_commander.app.command_executor.logging") as mock_logging:
            command_executor.report_error("test_cmd", "Test error message")

            mock_logging.critical.assert_called_once_with("Error in test_cmd: Test error message")

    def test_report_error_with_utils_logger(self, command_executor):
        """Test error reporting with utils logger."""
        with patch("chatty_commander.app.command_executor.logging") as mock_logging:
            with patch("chatty_commander.utils.logger.report_error") as mock_utils_report:
                command_executor.report_error("test_cmd", "Test error message")

                mock_logging.critical.assert_called_once()
                mock_utils_report.assert_called_once_with("Test error message", context="test_cmd")

    def test_report_error_utils_logger_import_error(self, command_executor):
        """Test error reporting when utils logger import fails."""
        with patch("chatty_commander.app.command_executor.logging") as mock_logging:
            with patch("chatty_commander.utils.logger.report_error", side_effect=ImportError):
                # Should not raise exception
                command_executor.report_error("test_cmd", "Test error message")

                mock_logging.critical.assert_called_once()

    def test_full_command_execution_cycle(self, command_executor):
        """Test full command execution cycle."""
        # Mock all dependencies
        with patch("chatty_commander.app.command_executor.pyautogui"):
            with patch("chatty_commander.app.command_executor.requests"):
                with patch("chatty_commander.app.command_executor.subprocess"):
                    # Execute keypress command
                    result = command_executor.execute_command("test_keypress")
                    assert result is True
                    assert command_executor.last_command == "test_keypress"

                    # Execute URL command
                    result = command_executor.execute_command("test_url")
                    assert result is True

                    # Execute shell command
                    result = command_executor.execute_command("test_shell")
                    assert result is True

                    # Execute custom message command
                    result = command_executor.execute_command("test_custom")
                    assert result is True

    def test_error_handling_during_execution(self, command_executor):
        """Test error handling during command execution."""
        with patch.object(command_executor, '_execute_keybinding') as mock_keybinding:
            mock_keybinding.side_effect = Exception("Keybinding failed")

            with patch("chatty_commander.app.command_executor.logging") as mock_logging:
                result = command_executor.execute_command("test_keypress")

                assert result is False
                mock_logging.error.assert_called()

    def test_display_environment_handling(self, command_executor):
        """Test DISPLAY environment variable handling."""
        # Test when DISPLAY is not set
        if "DISPLAY" in os.environ:
            del os.environ["DISPLAY"]

        with patch.dict(os.environ, {}, clear=True):
            # Should set DISPLAY to :0
            command_executor.execute_command("test_keypress")
            assert os.environ.get("DISPLAY") == ":0"

    def test_command_execution_with_old_format(self, command_executor):
        """Test command execution with old configuration format."""
        with patch("chatty_commander.app.command_executor.pyautogui"):
            result = command_executor.execute_command("old_format_keypress")
            assert result is True

    def test_invalid_command_action_type(self, command_executor):
        """Test command execution with invalid action type."""
        with patch("chatty_commander.app.command_executor.logging") as mock_logging:
            result = command_executor.execute_command("invalid_action")

            assert result is False
            mock_logging.error.assert_called()

    def test_exception_propagation(self, command_executor):
        """Test that certain exceptions are propagated."""
        with patch.object(command_executor, 'validate_command') as mock_validate:
            mock_validate.side_effect = TypeError("Validation failed")

            with pytest.raises(TypeError):
                command_executor.execute_command("test_command")


class TestModelManagerExtended:
    """Extended tests for ModelManager functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for ModelManager."""
        config = Mock()
        config.general_models_path = "/tmp/general_models"
        config.system_models_path = "/tmp/system_models"
        config.chat_models_path = "/tmp/chat_models"
        return config

    @pytest.fixture
    def model_manager(self, mock_config):
        """Create ModelManager instance."""
        return ModelManager(mock_config)

    def test_model_manager_initialization(self, model_manager, mock_config):
        """Test ModelManager initialization."""
        assert model_manager.config == mock_config
        assert model_manager.models["general"] == {}
        assert model_manager.models["system"] == {}
        assert model_manager.models["chat"] == {}
        assert model_manager.active_models == {}

    def test_get_patchable_model_class_priority_1(self):
        """Test _get_patchable_model_class priority 1: sys.modules."""
        with patch("chatty_commander.app.model_manager._sys") as mock_sys:
            mock_module = Mock()
            mock_model_class = Mock()
            mock_module.Model = mock_model_class
            mock_sys.modules.get.return_value = mock_module

            result = _get_patchable_model_class()
            assert result == mock_model_class

    def test_get_patchable_model_class_priority_2(self):
        """Test _get_patchable_model_class priority 2: importlib."""
        with patch("chatty_commander.app.model_manager._sys") as mock_sys:
            mock_sys.modules.get.return_value = None

            with patch("chatty_commander.app.model_manager.importlib") as mock_importlib:
                mock_module = Mock()
                mock_model_class = Mock()
                mock_module.Model = mock_model_class
                mock_importlib.import_module.return_value = mock_module

                result = _get_patchable_model_class()
                assert result == mock_model_class

    def test_get_patchable_model_class_priority_3(self):
        """Test _get_patchable_model_class priority 3: pytest MagicMock."""
        with patch("chatty_commander.app.model_manager._sys") as mock_sys:
            mock_sys.modules.get.return_value = None

        with patch("chatty_commander.app.model_manager.importlib") as mock_importlib:
            mock_importlib.import_module.side_effect = ImportError

        with patch("chatty_commander.app.model_manager._os") as mock_os:
            mock_os.environ.get.return_value = "pytest_test"

            with patch("chatty_commander.app.model_manager._MagicMock") as mock_magic_mock:
                result = _get_patchable_model_class()
                assert result == mock_magic_mock

    def test_get_patchable_model_class_priority_4(self):
        """Test _get_patchable_model_class priority 4: fallback Model."""
        with patch("chatty_commander.app.model_manager._sys") as mock_sys:
            mock_sys.modules.get.return_value = None

        with patch("chatty_commander.app.model_manager.importlib") as mock_importlib:
            mock_importlib.import_module.side_effect = ImportError

        with patch("chatty_commander.app.model_manager._os") as mock_os:
            mock_os.environ.get.return_value = None

        result = _get_patchable_model_class()
        assert result.__name__ == "Model"

    def test_reload_models_all_states(self, model_manager, mock_config):
        """Test reloading all model states."""
        with patch.object(model_manager, 'load_model_set') as mock_load:
            mock_load.return_value = {"model1": "mock_model"}

            result = model_manager.reload_models()

            assert len(mock_load.call_args_list) == 3  # general, system, chat
            assert model_manager.active_models == {"model1": "mock_model"}

    def test_reload_models_specific_state(self, model_manager, mock_config):
        """Test reloading specific model state."""
        with patch.object(model_manager, 'load_model_set') as mock_load:
            mock_load.return_value = {"idle_model": "mock_model"}

            result = model_manager.reload_models(state="idle")

            mock_load.assert_called_once_with(mock_config.general_models_path)
            assert model_manager.active_models == {"idle_model": "mock_model"}

    def test_reload_models_invalid_state(self, model_manager):
        """Test reloading invalid state."""
        result = model_manager.reload_models(state="invalid_state")
        assert result == {}

    def test_load_model_set_nonexistent_path(self, model_manager):
        """Test loading models from non-existent path."""
        with patch("os.path.exists", return_value=False):
            with patch("chatty_commander.app.model_manager.logging") as mock_logging:
                result = model_manager.load_model_set("/nonexistent/path")

                assert result == {}
                mock_logging.error.assert_called()

    def test_load_model_set_directory_error(self, model_manager):
        """Test loading models with directory listing error."""
        with patch("os.path.exists", return_value=True):
            with patch("os.listdir", side_effect=Exception("Directory error")):
                with patch("chatty_commander.app.model_manager.logging") as mock_logging:
                    result = model_manager.load_model_set("/some/path")

                    assert result == {}
                    mock_logging.error.assert_called()

    def test_load_model_set_with_mixed_files(self, model_manager):
        """Test loading models with mixed file types."""
        with patch("os.path.exists", return_value=True):
            with patch("os.listdir", return_value=["model1.onnx", "model2.onnx", "readme.txt", "script.py"]):
                with patch("os.path.join", side_effect=lambda *args: "/".join(args)):
                    with patch("os.path.exists", return_value=True):
                        with patch.object(model_manager, '_get_patchable_model_class') as mock_get_class:
                            mock_model_class = Mock()
                            mock_get_class.return_value = mock_model_class

                            result = model_manager.load_model_set("/models")

                            # Should only load .onnx files
                            assert len(result) == 2
                            assert "model1" in result
                            assert "model2" in result

    def test_load_model_set_model_instantiation_failure(self, model_manager):
        """Test loading models with model instantiation failure."""
        with patch("os.path.exists", return_value=True):
            with patch("os.listdir", return_value=["good_model.onnx", "bad_model.onnx"]):
                with patch("os.path.join", side_effect=lambda *args: "/".join(args)):
                    with patch("os.path.exists", return_value=True):
                        with patch.object(model_manager, '_get_patchable_model_class') as mock_get_class:
                            mock_model_class = Mock()
                            mock_model_class.side_effect = [Mock(), Exception("Model load failed")]
                            mock_get_class.return_value = mock_model_class

                            with patch("chatty_commander.app.model_manager.logging") as mock_logging:
                                result = model_manager.load_model_set("/models")

                                # Should only have good model
                                assert len(result) == 1
                                assert "good_model" in result
                                mock_logging.error.assert_called()

    def test_async_listen_for_commands(self, model_manager):
        """Test async command listening."""
        with patch("random.random", return_value=0.01):  # Force command detection
            with patch("random.choice", return_value="detected_command"):
                result = asyncio.run(model_manager.async_listen_for_commands())
                assert result == "detected_command"

    def test_async_listen_for_commands_no_detection(self, model_manager):
        """Test async command listening with no detection."""
        with patch("random.random", return_value=0.1):  # No command detection
            result = asyncio.run(model_manager.async_listen_for_commands())
            assert result is None

    def test_listen_for_commands_sync_wrapper(self, model_manager):
        """Test synchronous wrapper for async listening."""
        with patch.object(model_manager, 'async_listen_for_commands', return_value="sync_command"):
            result = model_manager.listen_for_commands()
            assert result == "sync_command"

    def test_get_models(self, model_manager):
        """Test getting models for specific state."""
        model_manager.models = {
            "general": {"model1": "general_model"},
            "system": {"model2": "system_model"},
            "chat": {"model3": "chat_model"}
        }

        general_models = model_manager.get_models("general")
        assert general_models == {"model1": "general_model"}

        system_models = model_manager.get_models("system")
        assert system_models == {"model2": "system_model"}

        chat_models = model_manager.get_models("chat")
        assert chat_models == {"model3": "chat_model"}

        nonexistent_models = model_manager.get_models("nonexistent")
        assert nonexistent_models == {}

    def test_model_manager_repr(self, model_manager):
        """Test ModelManager string representation."""
        model_manager.models = {
            "general": {"m1": "model1", "m2": "model2"},
            "system": {"m3": "model3"},
            "chat": {}
        }

        repr_str = repr(model_manager)
        assert "general=2" in repr_str
        assert "system=1" in repr_str
        assert "chat=0" in repr_str

    def test_model_manager_with_real_files(self, mock_config):
        """Test ModelManager with real model files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock .onnx files
            model_dir = os.path.join(temp_dir, "models")
            os.makedirs(model_dir)

            # Create some mock model files
            for model_name in ["model1.onnx", "model2.onnx", "text.txt"]:
                with open(os.path.join(model_dir, model_name), "w") as f:
                    f.write("mock model content")

            mock_config.general_models_path = model_dir

            model_manager = ModelManager(mock_config)

            # Should load only .onnx files
            assert len(model_manager.models["general"]) == 2
            assert "model1" in model_manager.models["general"]
            assert "model2" in model_manager.models["general"]

    def test_model_manager_file_not_found_handling(self, mock_config):
        """Test ModelManager handling of missing model files."""
        with patch("os.path.exists", return_value=False):
            with patch("chatty_commander.app.model_manager.logging") as mock_logging:
                model_manager = ModelManager(mock_config)

                # Should handle missing files gracefully
                assert len(model_manager.models["general"]) == 0
                mock_logging.error.assert_called()

    def test_model_manager_pytest_integration(self):
        """Test ModelManager pytest integration."""
        with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "true"}):
            with patch("chatty_commander.app.model_manager._MagicMock") as mock_magic_mock:
                result = _get_patchable_model_class()
                assert result == mock_magic_mock

    def test_model_manager_error_recovery(self, mock_config):
        """Test ModelManager error recovery during model loading."""
        with patch("os.path.exists", return_value=True):
            with patch("os.listdir", return_value=["model.onnx"]):
                with patch("os.path.join", return_value="/path/model.onnx"):
                    with patch("os.path.exists", return_value=True):
                        with patch.object(ModelManager, '_get_patchable_model_class') as mock_get_class:
                            # Make model instantiation fail
                            mock_get_class.return_value = Mock(side_effect=Exception("Model error"))

                            with patch("chatty_commander.app.model_manager.logging") as mock_logging:
                                model_manager = ModelManager(mock_config)

                                # Should handle error gracefully
                                assert len(model_manager.models["general"]) == 0
                                mock_logging.error.assert_called()

    def test_model_manager_concurrent_loading(self, mock_config):
        """Test ModelManager concurrent model loading simulation."""
        with patch("os.path.exists", return_value=True):
            with patch("os.listdir", return_value=[f"model{i}.onnx" for i in range(10)]):
                with patch("os.path.join", side_effect=lambda *args: "/".join(args)):
                    with patch("os.path.exists", return_value=True):
                        with patch.object(ModelManager, '_get_patchable_model_class') as mock_get_class:
                            mock_model_class = Mock()
                            mock_get_class.return_value = mock_model_class

                            model_manager = ModelManager(mock_config)

                            # Should load all models successfully
                            assert len(model_manager.models["general"]) == 10
                            assert mock_model_class.call_count == 10

    def test_model_manager_state_isolation(self, model_manager):
        """Test that different model states are isolated."""
        model_manager.models = {
            "general": {"general_model": "general_instance"},
            "system": {"system_model": "system_instance"},
            "chat": {"chat_model": "chat_instance"}
        }

        # Test state isolation
        general_models = model_manager.get_models("general")
        system_models = model_manager.get_models("system")
        chat_models = model_manager.get_models("chat")

        assert len(general_models) == 1
        assert len(system_models) == 1
        assert len(chat_models) == 1

        # Verify they're different instances
        assert general_models["general_model"] == "general_instance"
        assert system_models["system_model"] == "system_instance"
        assert chat_models["chat_model"] == "chat_instance"
