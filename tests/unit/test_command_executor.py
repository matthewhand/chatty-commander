"""Unit tests for command_executor module."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from chatty_commander.app.command_executor import CommandExecutor


class TestCommandExecutor:
    """Test suite for CommandExecutor functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock()
        config.get = Mock(return_value={"commands": {}})
        config.model_actions = Mock()
        config.model_actions.get = Mock(return_value=None)
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
    def executor(self, mock_config, mock_model_manager, mock_state_manager):
        """Create CommandExecutor with mocked dependencies."""
        return CommandExecutor(mock_config, mock_model_manager, mock_state_manager)

    def test_execute_command_valid(self, executor):
        """Test executing a valid command."""
        # Setup
        executor.config.get.return_value = {
            "commands": {
                "test_cmd": {"action": {"type": "message", "text": "hello"}}
            }
        }

        # Execute
        result = executor.execute_command("test_cmd")

        # Assert
        assert result is True
        assert executor.last_command == "test_cmd"

    def test_execute_command_invalid_name(self, executor):
        """Test executing with invalid command name."""
        with pytest.raises(ValueError):
            executor.execute_command("")

    def test_execute_command_not_found(self, executor):
        """Test executing non-existent command."""
        executor.config.get.return_value = {"commands": {}}

        result = executor.execute_command("nonexistent")

        assert result is False

    def test_validate_command_valid_keypress(self, executor):
        """Test validating keypress command."""
        executor.config.model_actions.get.return_value = {
            "action": "keypress",
            "keys": "ctrl+c"
        }

        result = executor.validate_command("copy")

        assert result is True

    def test_validate_command_valid_shell(self, executor):
        """Test validating shell command."""
        executor.config.model_actions.get.return_value = {
            "action": "shell",
            "cmd": "echo hello"
        }

        result = executor.validate_command("hello")

        assert result is True

    def test_validate_command_invalid_empty(self, executor):
        """Test validating empty command name."""
        result = executor.validate_command("")

        assert result is False

    def test_validate_command_not_found(self, executor):
        """Test validating non-existent command."""
        executor.config.model_actions.get.return_value = None

        result = executor.validate_command("missing")

        assert result is False

    def test_get_command_action_found(self, executor):
        """Test retrieving existing command action."""
        expected_action = {"type": "message", "text": "test"}
        executor.config.get.return_value = {
            "commands": {"test": {"action": expected_action}}
        }

        action = executor._get_command_action("test")

        assert action == expected_action

    def test_get_command_action_not_found(self, executor):
        """Test retrieving non-existent command action."""
        executor.config.get.return_value = {"commands": {}}

        action = executor._get_command_action("missing")

        assert action is None

    def test_validate_new_format_complete(self, executor):
        """Test validating complete new format action."""
        action_config = {"action": "keypress", "keys": "ctrl+v"}

        result = executor._validate_new_format(action_config)

        assert result is True

    def test_validate_new_format_missing_field(self, executor):
        """Test validating new format with missing required field."""
        action_config = {"action": "keypress"}  # missing "keys"

        result = executor._validate_new_format(action_config)

        assert result is False
