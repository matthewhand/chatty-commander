from pathlib import Path
from unittest.mock import MagicMock

import pytest

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.state_manager import StateManager
from conftest import TestDataFactory


class TestErrorHandling:
    """
    Tests for error handling in various modules.
    """

    @pytest.mark.parametrize(
        "invalid_input",
        [
            None,
            123,
            [],
            {},
            True,
        ],
    )
    def test_config_error_handling_invalid_inputs(self, invalid_input):
        """Test Config error handling for invalid inputs."""
        with pytest.raises((TypeError, ValueError)):
            Config(invalid_input)

    def test_config_error_handling_file_permissions(self, temp_dir: Path) -> None:
        """
        Test Config error handling for file permission issues.
        """
        temp_file = temp_dir / "protected_config.json"
        temp_file.write_text('{"default_state": "idle"}')
        temp_file.chmod(0o000)  # Make file unreadable
        try:
            # Config should handle permission error gracefully and return empty config (with defaults applied)
            config = Config(str(temp_file))
            # Verify defaults are present
            assert config.default_state == "idle"
            assert "general" in config.config_data
        finally:
            temp_file.chmod(0o644)  # Restore permissions

        temp_file.write_text("corrupted content")
        config = Config(str(temp_file))
        # Should fallback to defaults
        assert config.default_state == "idle"

    def test_state_manager_error_handling_invalid_transitions(self):
        """Test StateManager error handling for invalid transitions."""
        config = TestDataFactory.create_mock_config()
        sm = StateManager(config)
        with pytest.raises(ValueError):
            sm.change_state("invalid_state")

    def test_command_executor_error_handling_invalid_actions(self):
        """Test CommandExecutor error handling for invalid actions."""
        config = TestDataFactory.create_mock_config(
            {"model_actions": {"invalid": {"action": "unknown"}}}
        )
        ce = CommandExecutor(config, MagicMock(), MagicMock())
        with pytest.raises(ValueError):
            ce.execute_command("invalid")

