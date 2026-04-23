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
Comprehensive tests for config validation tool.

Tests config.json validation and state_models consistency.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.tools.validate_config import main, CFG


class TestConfigValidation:
    """Tests for config validation main function."""

    def test_config_not_found(self):
        """Test when config.json does not exist."""
        with tempfile.TemporaryDirectory() as tmp:
            with patch("src.chatty_commander.tools.validate_config.CFG", Path(tmp) / "config.json"):
                result = main()
                assert result == 2

    def test_valid_config(self):
        """Test with valid config."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.json"
            config_data = {
                "commands": {
                    "open_browser": {"action": "shell", "command": "firefox"},
                    "launch_app": {"action": "shell", "command": "code"},
                },
                "state_models": {
                    "idle": ["open_browser"],
                    "chatty": ["launch_app"],
                },
            }
            config_file.write_text(json.dumps(config_data))
            
            with patch("src.chatty_commander.tools.validate_config.CFG", config_file):
                result = main()
                assert result == 0

    def test_missing_command_in_state_models(self):
        """Test when state_models references missing command."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.json"
            config_data = {
                "commands": {
                    "open_browser": {"action": "shell", "command": "firefox"},
                },
                "state_models": {
                    "idle": ["open_browser"],
                    "chatty": ["missing_command"],  # This command doesn't exist
                },
            }
            config_file.write_text(json.dumps(config_data))
            
            with patch("src.chatty_commander.tools.validate_config.CFG", config_file):
                result = main()
                assert result == 1

    def test_multiple_missing_commands(self):
        """Test with multiple missing commands."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.json"
            config_data = {
                "commands": {},
                "state_models": {
                    "idle": ["cmd1", "cmd2"],
                    "chatty": ["cmd3"],
                },
            }
            config_file.write_text(json.dumps(config_data))
            
            with patch("src.chatty_commander.tools.validate_config.CFG", config_file):
                result = main()
                assert result == 1

    def test_empty_commands(self):
        """Test with empty commands section."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.json"
            config_data = {
                "commands": {},
                "state_models": {},
            }
            config_file.write_text(json.dumps(config_data))
            
            with patch("src.chatty_commander.tools.validate_config.CFG", config_file):
                result = main()
                assert result == 0

    def test_empty_state_models(self):
        """Test with empty state_models section."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.json"
            config_data = {
                "commands": {
                    "cmd1": {"action": "shell", "command": "test"},
                },
                "state_models": {},
            }
            config_file.write_text(json.dumps(config_data))
            
            with patch("src.chatty_commander.tools.validate_config.CFG", config_file):
                result = main()
                assert result == 0

    def test_missing_commands_section(self):
        """Test when commands section is missing."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.json"
            config_data = {
                "state_models": {
                    "idle": ["some_command"],
                },
            }
            config_file.write_text(json.dumps(config_data))
            
            with patch("src.chatty_commander.tools.validate_config.CFG", config_file):
                result = main()
                assert result == 1

    def test_missing_state_models_section(self):
        """Test when state_models section is missing."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.json"
            config_data = {
                "commands": {
                    "cmd1": {"action": "shell", "command": "test"},
                },
            }
            config_file.write_text(json.dumps(config_data))
            
            with patch("src.chatty_commander.tools.validate_config.CFG", config_file):
                result = main()
                assert result == 0


class TestConfigValidationEdgeCases:
    """Edge case tests for config validation."""

    def test_null_commands(self):
        """Test when commands is null."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.json"
            config_data = {
                "commands": None,
                "state_models": {
                    "idle": ["cmd1"],
                },
            }
            config_file.write_text(json.dumps(config_data))
            
            with patch("src.chatty_commander.tools.validate_config.CFG", config_file):
                result = main()
                assert result == 1

    def test_null_state_models(self):
        """Test when state_models is null."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.json"
            config_data = {
                "commands": {
                    "cmd1": {"action": "shell", "command": "test"},
                },
                "state_models": None,
            }
            config_file.write_text(json.dumps(config_data))
            
            with patch("src.chatty_commander.tools.validate_config.CFG", config_file):
                result = main()
                assert result == 0

    def test_null_values_in_state_models(self):
        """Test with null values in state_models."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.json"
            config_data = {
                "commands": {
                    "cmd1": {"action": "shell", "command": "test"},
                },
                "state_models": {
                    "idle": None,
                    "chatty": ["cmd1"],
                },
            }
            config_file.write_text(json.dumps(config_data))
            
            with patch("src.chatty_commander.tools.validate_config.CFG", config_file):
                result = main()
                assert result == 0

    def test_invalid_json(self):
        """Test with invalid JSON."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.json"
            config_file.write_text("not valid json")
            
            with patch("src.chatty_commander.tools.validate_config.CFG", config_file):
                with pytest.raises(json.JSONDecodeError):
                    main()


class TestConfigValidationIntegration:
    """Integration tests for config validation."""

    def test_complex_valid_config(self):
        """Test with complex valid configuration."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.json"
            config_data = {
                "commands": {
                    "open_browser": {"action": "shell", "command": "firefox"},
                    "launch_editor": {"action": "shell", "command": "code"},
                    "play_music": {"action": "shell", "command": "spotify"},
                    "show_time": {"action": "python", "code": "print('time')"},
                },
                "state_models": {
                    "idle": ["open_browser", "show_time"],
                    "chatty": ["play_music"],
                    "computer": ["launch_editor", "open_browser"],
                },
                "other_settings": {
                    "debug": True,
                    "timeout": 30,
                },
            }
            config_file.write_text(json.dumps(config_data))
            
            with patch("src.chatty_commander.tools.validate_config.CFG", config_file):
                result = main()
                assert result == 0

    def test_partial_missing_commands(self):
        """Test when some commands are missing."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.json"
            config_data = {
                "commands": {
                    "open_browser": {"action": "shell", "command": "firefox"},
                    "launch_editor": {"action": "shell", "command": "code"},
                },
                "state_models": {
                    "idle": ["open_browser"],  # Valid
                    "chatty": ["missing_cmd"],  # Invalid
                    "computer": ["launch_editor"],  # Valid
                },
            }
            config_file.write_text(json.dumps(config_data))
            
            with patch("src.chatty_commander.tools.validate_config.CFG", config_file):
                result = main()
                assert result == 1


class TestConfigPath:
    """Tests for config path handling."""

    def test_default_config_path(self):
        """Test that default config path is set correctly."""
        from src.chatty_commander.tools import validate_config
        assert validate_config.CFG == Path("config.json")

    def test_config_path_is_pathlib(self):
        """Test that config path is a Path object."""
        from src.chatty_commander.tools import validate_config
        assert isinstance(validate_config.CFG, Path)
