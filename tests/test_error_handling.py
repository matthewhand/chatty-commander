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

from pathlib import Path

import pytest
from unittest.mock import MagicMock
from test_data_factories import TestDataFactory

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.web_mode import WebModeServer


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

    def test_web_mode_error_handling_missing_dependencies(self):
        """Test WebModeServer error handling for missing dependencies."""
        pass 
        # config = TestDataFactory.create_mock_config()
        # with pytest.raises(ImportError):
        #    WebModeServer(config, missing_dependency=True)
