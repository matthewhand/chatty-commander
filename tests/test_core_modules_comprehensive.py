"""Comprehensive tests for core modules: ModelManager, StateManager, CommandExecutor."""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager


class TestModelManagerComprehensive:
    """Comprehensive tests for ModelManager class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        config = Mock(spec=Config)
        config.general_models_path = "/tmp/general"
        config.system_models_path = "/tmp/system"
        config.chat_models_path = "/tmp/chat"
        config.model_actions = {"test_command": {"action": "keypress", "keys": "space"}}
        return config

    @pytest.fixture
    def temp_model_dirs(self):
        """Create temporary model directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            general_dir = Path(temp_dir) / "general"
            system_dir = Path(temp_dir) / "system"
            chat_dir = Path(temp_dir) / "chat"

            general_dir.mkdir()
            system_dir.mkdir()
            chat_dir.mkdir()

            # Create some dummy model files
            (general_dir / "model1.onnx").touch()
            (system_dir / "model2.onnx").touch()
            (chat_dir / "model3.onnx").touch()

            yield {"general": str(general_dir), "system": str(system_dir), "chat": str(chat_dir)}

    def test_model_manager_initialization(self, mock_config):
        """Test ModelManager initialization."""
        with patch.object(ModelManager, 'reload_models'):
            manager = ModelManager(mock_config)

        assert manager.config == mock_config
        assert manager.models == {"general": {}, "system": {}, "chat": {}}

    def test_model_manager_initialization_with_real_dirs(self, temp_model_dirs):
        """Test ModelManager initialization with real directories."""
        config = Mock(spec=Config)
        config.general_models_path = temp_model_dirs["general"]
        config.system_models_path = temp_model_dirs["system"]
        config.chat_models_path = temp_model_dirs["chat"]
        config.model_actions = {}

        manager = ModelManager(config)
        assert manager.config == config

    @patch('chatty_commander.app.model_manager.Model')
    def test_reload_models_success(self, mock_model_class, mock_config, temp_model_dirs):
        """Test successful model reloading."""
        mock_config.general_models_path = temp_model_dirs["general"]
        mock_config.system_models_path = temp_model_dirs["system"]
        mock_config.chat_models_path = temp_model_dirs["chat"]

        mock_model = Mock()
        mock_model_class.return_value = mock_model

        manager = ModelManager(mock_config)
        manager.reload_models("general")

        # Should have loaded models from the general directory
        assert "general" in manager.models

    def test_reload_models_nonexistent_state(self, mock_config):
        """Test reloading models for nonexistent state."""
        manager = ModelManager(mock_config)

        # Should not raise an error, just log a warning
        manager.reload_models("nonexistent")
        assert "nonexistent" not in manager.models

    @patch('chatty_commander.app.model_manager.os.path.exists')
    def test_reload_models_missing_directory(self, mock_exists, mock_config):
        """Test reloading models when directory doesn't exist."""
        mock_exists.return_value = False

        manager = ModelManager(mock_config)
        manager.reload_models("general")

        # Should handle missing directory gracefully
        assert manager.models["general"] == {}

    @patch('chatty_commander.app.model_manager.Model')
    def test_reload_models_with_exception(self, mock_model_class, mock_config, temp_model_dirs):
        """Test model reloading when Model creation fails."""
        mock_config.general_models_path = temp_model_dirs["general"]
        mock_model_class.side_effect = Exception("Model loading failed")

        with patch.object(ModelManager, 'reload_models', return_value=None):
            manager = ModelManager(mock_config)

        # Should handle exceptions gracefully
        manager.reload_models("general")
        assert manager.models["general"] == {}

    @patch('chatty_commander.app.model_manager.random.choice')
    @patch('chatty_commander.app.model_manager.random.random')
    def test_listen_for_commands_demo_mode(self, mock_random, mock_choice, mock_config):
        """Test listen_for_commands in demo mode."""
        mock_choice.return_value = "test_command"
        mock_random.return_value = 0.01  # Less than 0.05 to trigger command return

        with patch.object(ModelManager, 'reload_models'):
            manager = ModelManager(mock_config)
        # Set up active_models to have some models
        manager.active_models = {"test_command": Mock()}
        result = manager.listen_for_commands()

        assert result == "test_command"
        mock_choice.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_listen_for_commands_demo_mode(self, mock_config):
        """Test async_listen_for_commands in demo mode."""

        with patch('chatty_commander.app.model_manager.random.choice') as mock_choice:
            with patch('chatty_commander.app.model_manager.random.random') as mock_random:
                mock_choice.return_value = "test_command"
                mock_random.return_value = 0.01  # Less than 0.05 to trigger command return

                with patch.object(ModelManager, 'reload_models'):
                    manager = ModelManager(mock_config)
                # Set up active_models to have some models
                manager.active_models = {"test_command": Mock()}
                result = await manager.async_listen_for_commands()

                assert result == "test_command"

    @pytest.mark.asyncio
    async def test_async_listen_for_commands_with_models(self, mock_config):
        """Test async_listen_for_commands with actual models."""
        mock_model = AsyncMock()
        mock_model.predict.return_value = "detected_command"

        with patch.object(ModelManager, 'reload_models'):
            manager = ModelManager(mock_config)
        manager.models["general"]["test_model"] = mock_model
        manager.active_models = {"test_command": mock_model}

        with patch('chatty_commander.app.model_manager.random.choice', return_value="test_command"):
            with patch('chatty_commander.app.model_manager.random.random', return_value=0.01):
                result = await manager.async_listen_for_commands()

        # Should return the mocked command
        assert result == "test_command"

    def test_get_models(self, mock_config):
        """Test get_models method."""
        manager = ModelManager(mock_config)
        manager.models["test_state"] = {"model1": Mock(), "model2": Mock()}

        result = manager.get_models("test_state")
        assert len(result) == 2
        assert "model1" in result
        assert "model2" in result

    def test_get_models_nonexistent_state(self, mock_config):
        """Test get_models for nonexistent state."""
        manager = ModelManager(mock_config)

        result = manager.get_models("nonexistent")
        assert result == {}

    def test_repr(self, mock_config):
        """Test __repr__ method."""
        manager = ModelManager(mock_config)
        manager.models["general"] = {"model1": Mock()}
        manager.models["system"] = {"model2": Mock(), "model3": Mock()}
        manager.models["chat"] = {}

        repr_str = repr(manager)
        assert "ModelManager" in repr_str
        assert "general=1" in repr_str
        assert "system=2" in repr_str
        assert "chat=0" in repr_str


class TestStateManagerComprehensive:
    """Comprehensive tests for StateManager class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        config = Mock(spec=Config)
        config.default_state = "idle"
        config.state_models = {
            "idle": ["idle_model1", "idle_model2"],
            "computer": ["computer_model1"],
            "chatty": ["chatty_model1", "chatty_model2", "chatty_model3"],
        }
        config.state_transitions = {
            "idle": {"hey_khum_puter": "computer", "hey_chat_tee": "chatty"},
            "computer": {"okay_stop": "idle"},
            "chatty": {"thanks_chat_tee": "idle"},
        }
        config.wakeword_state_map = {
            "hey_khum_puter": "computer",
            "hey_chat_tee": "chatty",
            "okay_stop": "idle",
            "thanks_chat_tee": "idle",
        }
        return config

    def test_state_manager_initialization(self, mock_config):
        """Test StateManager initialization."""
        manager = StateManager(mock_config)

        assert manager.config == mock_config
        assert manager.current_state == "idle"
        assert manager.active_models == ["idle_model1", "idle_model2"]
        assert manager.callbacks == []

    def test_state_manager_initialization_no_config(self):
        """Test StateManager initialization without config."""
        with patch('chatty_commander.app.state_manager.Config') as mock_config_class:
            mock_config = Mock()
            mock_config.default_state = "idle"
            mock_config.state_models = {"idle": []}
            mock_config_class.return_value = mock_config

            manager = StateManager()
            assert manager.config == mock_config

    def test_update_state_valid_transition(self, mock_config):
        """Test valid state transition."""
        manager = StateManager(mock_config)

        result = manager.update_state("hey_khum_puter")

        assert result == "computer"
        assert manager.current_state == "computer"
        assert manager.active_models == ["computer_model1"]

    def test_update_state_invalid_command(self, mock_config):
        """Test update_state with invalid command."""
        manager = StateManager(mock_config)

        result = manager.update_state("invalid_command")

        assert result is None
        assert manager.current_state == "idle"  # Should remain unchanged

    def test_update_state_no_transition_config(self, mock_config):
        """Test update_state without state_transitions config."""
        mock_config.state_transitions = None
        manager = StateManager(mock_config)

        # Should fall back to hardcoded logic
        result = manager.update_state("hey_chat_tee")
        assert result == "chatty"

    def test_update_state_wakeword_mapping(self):
        """Test state transitions using wakeword_state_map."""
        # Create a config with wakeword_state_map
        config = Mock()
        config.default_state = "idle"
        config.state_models = {
            "idle": ["idle_model1"],
            "computer": ["computer_model1"],
            "chatty": ["chatty_model1"],
        }
        config.wakeword_state_map = {
            "hey_chat_tee": "chatty",
            "hey_khum_puter": "computer",
            "okay_stop": "idle",
            "thanks_chat_tee": "idle",
            "that_ill_do": "idle",
        }

        manager = StateManager(config)

        # Test transition from idle to chatty (should work since states are different)
        assert manager.current_state == "idle"
        result = manager.update_state("hey_chat_tee")
        assert result == "chatty"
        assert manager.current_state == "chatty"

        # Test transition from chatty to computer
        result = manager.update_state("hey_khum_puter")
        assert result == "computer"
        assert manager.current_state == "computer"

        # Test transition from computer to idle
        result = manager.update_state("okay_stop")
        assert result == "idle"
        assert manager.current_state == "idle"

    def test_update_state_toggle_mode(self, mock_config):
        """Test toggle_mode command."""
        delattr(mock_config, 'state_transitions')
        manager = StateManager(mock_config)

        # Start in idle, toggle should go to computer
        result = manager.update_state("toggle_mode")
        assert result == "computer"

        # From computer, toggle should go to chatty
        result = manager.update_state("toggle_mode")
        assert result == "chatty"

        # From chatty, toggle should go back to idle
        result = manager.update_state("toggle_mode")
        assert result == "idle"

    def test_add_state_change_callback(self, mock_config):
        """Test adding state change callbacks."""
        manager = StateManager(mock_config)
        callback = Mock()

        manager.add_state_change_callback(callback)

        assert callback in manager.callbacks

    def test_change_state_valid(self, mock_config):
        """Test changing to a valid state."""
        manager = StateManager(mock_config)
        callback = Mock()
        manager.add_state_change_callback(callback)

        manager.change_state("computer")

        assert manager.current_state == "computer"
        assert manager.active_models == ["computer_model1"]
        callback.assert_called_once_with("idle", "computer")

    def test_change_state_with_callback(self, mock_config):
        """Test changing state with additional callback."""
        manager = StateManager(mock_config)
        additional_callback = Mock()

        manager.change_state("computer", additional_callback)

        additional_callback.assert_called_once_with("computer")

    def test_change_state_invalid(self, mock_config):
        """Test changing to an invalid state."""
        manager = StateManager(mock_config)

        with pytest.raises(ValueError, match="Invalid state: invalid_state"):
            manager.change_state("invalid_state")

    def test_get_active_models(self, mock_config):
        """Test get_active_models method."""
        manager = StateManager(mock_config)

        result = manager.get_active_models()
        assert result == ["idle_model1", "idle_model2"]

    def test_post_state_change_hook(self, mock_config):
        """Test post_state_change_hook method."""
        manager = StateManager(mock_config)

        # Should not raise any errors
        manager.post_state_change_hook("computer")

    def test_repr(self, mock_config):
        """Test __repr__ method."""
        manager = StateManager(mock_config)

        repr_str = repr(manager)
        assert "StateManager" in repr_str
        assert "current_state=idle" in repr_str
        assert "active_models=2" in repr_str


class TestCommandExecutorComprehensive:
    """Comprehensive tests for CommandExecutor class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        config = Mock(spec=Config)
        config.model_actions = {
            "keypress_command": {"keypress": "space"},
            "url_command": {"url": "https://example.com"},
            "shell_command": {"shell": "echo hello"},
            "structured_keypress": {"action": "keypress", "keys": "ctrl+c"},
            "structured_url": {"action": "url", "url": "https://test.com"},
            "custom_message": {"action": "custom_message", "message": "Test message"},
            "voice_chat": {"action": "voice_chat", "llm_provider": "test"},
        }
        return config

    @pytest.fixture
    def mock_managers(self, mock_config):
        """Create mock managers for testing."""
        model_manager = Mock()
        state_manager = Mock()
        return mock_config, model_manager, state_manager

    def test_command_executor_initialization(self, mock_managers):
        """Test CommandExecutor initialization."""
        config, model_manager, state_manager = mock_managers

        executor = CommandExecutor(config, model_manager, state_manager)

        assert executor.config == config
        assert executor.model_manager == model_manager
        assert executor.state_manager == state_manager

    def test_command_executor_initialization_simple_config(self):
        """Test CommandExecutor initialization with simple config."""
        config = Mock()
        config.model_actions = {"simple": "value"}
        model_manager = Mock()
        state_manager = Mock()

        executor = CommandExecutor(config, model_manager, state_manager)

        assert executor.config == config

    def test_validate_command_valid(self, mock_managers):
        """Test validate_command with valid command."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        assert executor.validate_command("keypress_command") is True

    def test_validate_command_invalid(self, mock_managers):
        """Test validate_command with invalid command."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        assert executor.validate_command("invalid_command") is False

    def test_execute_command_invalid_type(self, mock_managers):
        """Test execute_command with invalid command type."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        # In tolerant mode, should return False
        assert executor.execute_command(None) is False
        assert executor.execute_command(123) is False

    def test_execute_command_invalid_type_strict(self):
        """Test execute_command with invalid type in strict mode."""
        config = Mock()
        config.model_actions = {"simple": "value"}
        executor = CommandExecutor(config, Mock(), Mock())

        with pytest.raises(TypeError):
            executor.execute_command(None)

    @patch('chatty_commander.app.command_executor.pyautogui')
    def test_execute_keypress_command(self, mock_pyautogui, mock_managers):
        """Test executing keypress command."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        with patch.object(executor, '_execute_keybinding') as mock_keybinding:
            result = executor.execute_command("keypress_command")

            assert result is True
            mock_keybinding.assert_called_once_with("keypress_command", "space")

    @patch('chatty_commander.app.command_executor.requests.get')
    def test_execute_url_command(self, mock_get, mock_managers):
        """Test executing URL command."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)
        mock_get.return_value.status_code = 200

        with patch.object(executor, '_execute_url', return_value=True) as mock_url:
            result = executor.execute_command("url_command")

            assert result is True
            mock_url.assert_called_once_with("url_command", "https://example.com")

    def test_execute_custom_message_command(self, mock_managers):
        """Test executing custom message command."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        # Custom message commands are not supported by current implementation
        with pytest.raises(TypeError, match="Command 'custom_message' has an invalid type"):
            executor.execute_command("custom_message")

    def test_execute_command_nonexistent(self, mock_managers):
        """Test executing nonexistent command."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        # Should raise ValueError for nonexistent command
        with pytest.raises(ValueError, match="Invalid command: nonexistent"):
            executor.execute_command("nonexistent")

    def test_pre_execute_hook(self, mock_managers):
        """Test pre_execute_hook method."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        # Should not raise any errors
        executor.pre_execute_hook("test_command")

    def test_post_execute_hook(self, mock_managers):
        """Test post_execute_hook method."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        # Should not raise any errors
        executor.post_execute_hook("test_command")

    @patch('chatty_commander.app.command_executor.pyautogui')
    def test_execute_keypress_string_keys(self, mock_pyautogui, mock_managers):
        """Test _execute_keypress with string keys."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        executor._execute_keybinding("test_command", "space")
        mock_pyautogui.press.assert_called_once_with("space")

    @patch('chatty_commander.app.command_executor.pyautogui')
    def test_execute_keypress_hotkey(self, mock_pyautogui, mock_managers):
        """Test _execute_keypress with hotkey combination."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        executor._execute_keybinding("test_command", ["ctrl", "c"])
        mock_pyautogui.hotkey.assert_called_once_with("ctrl", "c")

    @patch('chatty_commander.app.command_executor.pyautogui')
    def test_execute_keypress_list_keys(self, mock_pyautogui, mock_managers):
        """Test _execute_keypress with list of keys."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        executor._execute_keybinding("test_command", ["ctrl", "shift", "n"])
        mock_pyautogui.hotkey.assert_called_once_with("ctrl", "shift", "n")

    def test_execute_keypress_no_pyautogui(self, mock_managers):
        """Test _execute_keypress when pyautogui is not available."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        with patch('chatty_commander.app.command_executor.pyautogui', None):
            # Should not raise, just report error
            executor._execute_keybinding("test_command", "space")

    def test_execute_keypress_invalid_keys(self, mock_managers):
        """Test _execute_keypress with invalid keys."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        # The current implementation doesn't validate key types, it just passes them to pyautogui
        # This test should be removed or modified to test actual error conditions
        with patch('chatty_commander.app.command_executor.pyautogui') as mock_pyautogui:
            mock_pyautogui.press.side_effect = Exception("Invalid key")
            executor._execute_keybinding("test_command", 123)  # Should not raise, just report error

    def test_report_error(self, mock_managers):
        """Test report_error method."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        with patch('logging.critical') as mock_log_critical:
            executor.report_error("test_command", "Test error message")

            mock_log_critical.assert_called_once_with("Error in test_command: Test error message")

    @patch('chatty_commander.app.command_executor.requests.get')
    def test_execute_url_success(self, mock_get, mock_managers):
        """Test _execute_url with successful request."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        executor._execute_url("test_command", "https://example.com")

        mock_get.assert_called_once_with("https://example.com")

    @patch('chatty_commander.app.command_executor.requests.get')
    def test_execute_url_failure(self, mock_get, mock_managers):
        """Test _execute_url with failed request."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        mock_get.side_effect = Exception("Network error")

        executor._execute_url("test_command", "https://example.com")
        # Should handle exception gracefully by reporting error

    @patch('chatty_commander.app.command_executor.subprocess.run')
    def test_execute_shell_success(self, mock_run, mock_managers):
        """Test _execute_shell with successful command."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = executor._execute_shell("test_command", "echo hello")

        assert result is True
        mock_run.assert_called_once()

    @patch('chatty_commander.app.command_executor.subprocess.run')
    def test_execute_shell_failure(self, mock_run, mock_managers):
        """Test _execute_shell with failed command."""
        config, model_manager, state_manager = mock_managers
        executor = CommandExecutor(config, model_manager, state_manager)

        mock_run.side_effect = Exception("Command failed")

        result = executor._execute_shell("test_command", "invalid_command")

        assert result is False
        mock_run.assert_called_once()
