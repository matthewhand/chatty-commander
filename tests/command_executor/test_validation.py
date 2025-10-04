"""
Command validation tests for CommandExecutor.
"""

import pytest
from unittest.mock import Mock
from src.chatty_commander.app.command_executor import CommandExecutor


class TestCommandExecutorValidation:
    """Test command validation functionality."""

    def test_validate_existing_command(self, command_executor):
        """Test validation of existing command."""
        assert command_executor.validate_command("test_shell") is True
        assert command_executor.validate_command("test_keypress") is True
        assert command_executor.validate_command("test_url") is True
        assert command_executor.validate_command("test_message") is True

    def test_validate_nonexistent_command(self, command_executor):
        """Test validation of nonexistent command."""
        assert command_executor.validate_command("nonexistent") is False

    def test_validate_empty_string(self, command_executor):
        """Test validation of empty string."""
        assert command_executor.validate_command("") is False

    def test_validate_none(self, command_executor):
        """Test validation of None."""
        assert command_executor.validate_command(None) is False

    def test_validate_non_string_types(self, command_executor):
        """Test validation of non-string types."""
        assert command_executor.validate_command(123) is False
        assert command_executor.validate_command([]) is False
        assert command_executor.validate_command({}) is False
        assert command_executor.validate_command(True) is False

    def test_validate_whitespace_only(self, command_executor):
        """Test validation of whitespace-only string."""
        assert command_executor.validate_command("   ") is False
        assert command_executor.validate_command("\t") is False
        assert command_executor.validate_command("\n") is False

    def test_validate_case_sensitivity(self, command_executor):
        """Test case sensitivity in command validation."""
        assert command_executor.validate_command("TEST_SHELL") is False
        assert command_executor.validate_command("Test_Shell") is False
        assert command_executor.validate_command("test_shell") is True

    def test_validate_partial_match(self, command_executor):
        """Test partial command matching."""
        assert command_executor.validate_command("test") is False
        assert command_executor.validate_command("shell") is False
        assert command_executor.validate_command("test_shel") is False

    def test_validate_with_empty_model_actions(self, command_executor, mock_config):
        """Test validation with empty model actions."""
        mock_config.model_actions = {}

        assert command_executor.validate_command("any_command") is False

    def test_validate_with_none_model_actions(self, command_executor, mock_config):
        """Test validation with None model actions."""
        mock_config.model_actions = None

        assert command_executor.validate_command("any_command") is False

    def test_validate_command_with_special_characters(
        self, command_executor, mock_config
    ):
        """Test validation of command with special characters."""
        mock_config.model_actions = {
            "special-cmd": {"action": "shell", "cmd": "echo test"},
            "cmd_with_underscore": {"action": "shell", "cmd": "echo test"},
            "cmd.with.dots": {"action": "shell", "cmd": "echo test"},
        }

        assert command_executor.validate_command("special-cmd") is True
        assert command_executor.validate_command("cmd_with_underscore") is True
        assert command_executor.validate_command("cmd.with.dots") is True

    def test_validate_command_with_numbers(self, command_executor, mock_config):
        """Test validation of command with numbers."""
        mock_config.model_actions = {
            "cmd123": {"action": "shell", "cmd": "echo test"},
            "123cmd": {"action": "shell", "cmd": "echo test"},
            "cmd_123_test": {"action": "shell", "cmd": "echo test"},
        }

        assert command_executor.validate_command("cmd123") is True
        assert command_executor.validate_command("123cmd") is True
        assert command_executor.validate_command("cmd_123_test") is True

    def test_validate_command_structure(self, command_executor, mock_config):
        """Test validation with different command structures."""
        mock_config.model_actions = {
            "valid_cmd": {"action": "shell", "cmd": "echo test"},
            "no_action": {"cmd": "echo test"},
            "empty_action": {"action": "", "cmd": "echo test"},
            "none_action": {"action": None, "cmd": "echo test"},
        }

        assert command_executor.validate_command("valid_cmd") is True
        assert (
            command_executor.validate_command("no_action") is True
        )  # May still be valid
        assert command_executor.validate_command("empty_action") is True
        assert command_executor.validate_command("none_action") is True

    def test_validate_after_config_change(self, command_executor, mock_config):
        """Test validation after config change."""
        # Initially valid
        assert command_executor.validate_command("test_shell") is True

        # Change config
        mock_config.model_actions = {"new_cmd": {"action": "shell", "cmd": "echo new"}}

        # Old command should be invalid, new should be valid
        assert command_executor.validate_command("test_shell") is False
        assert command_executor.validate_command("new_cmd") is True
