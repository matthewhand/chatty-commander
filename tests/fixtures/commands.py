# fixtures/commands.py
"""Test fixtures for command-related tests."""

from unittest.mock import Mock

import pytest


class CommandFixtures:
    """Factory for command test data."""
    
    # Standard test commands
    VALID_COMMANDS = {
        "open_browser": {
            "type": "url",
            "url": "https://google.com"
        },
        "play_music": {
            "type": "shell",
            "command": "playerctl play"
        },
        "stop_music": {
            "type": "shell",
            "command": "playerctl stop"
        },
        "volume_up": {
            "type": "keypress",
            "keys": ["volume_up"]
        }
    }
    
    @staticmethod
    def create_command_config(name="test_command", action_type="shell", **kwargs):
        """Create a command configuration."""
        config = {"type": action_type}
        config.update(kwargs)
        return {name: config}
    
    @staticmethod
    def get_valid_command(name):
        """Get a pre-defined valid command."""
        return CommandFixtures.VALID_COMMANDS.get(name)
    
    @staticmethod
    def create_mock_command_executor():
        """Create a pre-configured mock command executor."""
        executor = Mock()
        executor.validate_command.return_value = True
        executor.execute_command.return_value = True
        executor.get_available_commands.return_value = list(CommandFixtures.VALID_COMMANDS.keys())
        return executor
    
    @staticmethod
    def create_command_test_cases():
        """Create parameterized test cases for commands."""
        return [
            ("open_browser", True),
            ("play_music", True),
            ("stop_music", True),
            ("nonexistent", False),
        ]


# Pytest fixtures
@pytest.fixture
def valid_commands():
    """Provide all valid command definitions."""
    return CommandFixtures.VALID_COMMANDS


@pytest.fixture
def command_executor():
    """Provide a mock command executor."""
    return CommandFixtures.create_mock_command_executor()


@pytest.fixture
def command_test_cases():
    """Provide parameterized command test cases."""
    return CommandFixtures.create_command_test_cases()


command_fixtures = CommandFixtures
