import json
import os
from unittest.mock import patch

import pytest

from chatty_commander.app.config import Config


class TestConfigStabilization:
    """
    Focused test suite to stabilize fragile configuration logic,
    specifically defaults, state transitions, and legacy support.
    """

    @pytest.fixture
    def mock_config_file(self, tmp_path):
        """Create a temporary config file."""
        config_file = tmp_path / "config.json"
        return str(config_file)

    @pytest.fixture
    def empty_config_file(self, mock_config_file):
        """Create an empty config file to test defaults."""
        with open(mock_config_file, "w") as f:
            json.dump({}, f)
        return mock_config_file

    def test_defaults_load_correctly(self, empty_config_file):
        """Test that essential defaults are loaded when config is empty."""
        config = Config(empty_config_file)

        assert config.default_state == "idle"
        assert config.general_models_path == "models-idle"
        assert len(config.commands) > 0
        assert "hello" in config.commands
        assert config.voice_only is False

    def test_state_transitions_logic(self, mock_config_file):
        """Test the logic for parsing and validating state transitions."""
        data = {
            "state_transitions": {
                "idle": {"wakeword_1": "active"},
                "active": {"wakeword_2": "idle"}
            }
        }
        with open(mock_config_file, "w") as f:
            json.dump(data, f)

        config = Config(mock_config_file)
        assert config.state_transitions["idle"]["wakeword_1"] == "active"
        assert config.state_transitions["active"]["wakeword_2"] == "idle"

    def test_fragile_validate_config(self, mock_config_file):
        """Test _validate_config resilience to bad types."""
        data = {
            "state_models": "not_a_dict",  # Should warn and reset to {}
            "api_endpoints": ["not", "a", "dict"],  # Should warn and reset to {}
            "commands": 123  # Should warn and reset to {}
        }
        with open(mock_config_file, "w") as f:
            json.dump(data, f)

        config = Config(mock_config_file)

        # Logic in _validate_config should handle these gracefully
        assert isinstance(config.state_models, dict)
        assert isinstance(config.api_endpoints, dict)
        assert isinstance(config.commands, dict)
        assert config.state_models == {}

    def test_env_overrides(self, mock_config_file):
        """Test environment variable overrides."""
        with open(mock_config_file, "w") as f:
            json.dump({"default_state": "idle"}, f)

        with patch.dict(os.environ, {"CHATCOMM_DEFAULT_STATE": "super_active"}):
            config = Config(mock_config_file)
            assert config.default_state == "super_active"

    def test_build_model_actions(self, mock_config_file):
        """Test transformation of commands to model actions."""
        data = {
            "commands": {
                "cmd1": {"action": "keypress", "keys": "ctrl+c"},
                "cmd2": {"action": "custom_message", "message": "hi"}
            },
            "keybindings": {
                "ctrl+c": "mapped_ctrl_c"
            }
        }
        with open(mock_config_file, "w") as f:
            json.dump(data, f)

        config = Config(mock_config_file)
        actions = config.model_actions

        assert "cmd1" in actions
        assert actions["cmd1"]["keypress"] == "mapped_ctrl_c"
        assert "cmd2" in actions
        assert actions["cmd2"]["shell"] == "echo hi"

    def test_reload_config_resilience(self, mock_config_file):
        """Test reload mechanism."""
        with open(mock_config_file, "w") as f:
            json.dump({"default_state": "idle"}, f)

        config = Config(mock_config_file)
        assert config.default_state == "idle"

        # Update file
        with open(mock_config_file, "w") as f:
            json.dump({"default_state": "reloaded"}, f)

        assert config.reload_config() is True
        assert config.default_state == "reloaded"

    def test_missing_config_file_uses_defaults(self, tmp_path):
        """Test behavior when file does not exist."""
        missing_file = str(tmp_path / "nonexistent.json")
        config = Config(missing_file)

        # Should start with defaults and not crash
        assert config.commands is not None
        assert len(config.commands) > 0
        # defaults might inject general settings, so config_data is not empty
        assert isinstance(config.config_data, dict)
