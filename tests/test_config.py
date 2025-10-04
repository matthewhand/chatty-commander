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

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from test_assertions import TestAssertions
from test_data_factories import TestDataFactory

from chatty_commander.app.config import Config


class TestConfig:
    """
    Comprehensive tests for the Config module.
    """

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Provide a temporary directory for tests that need file system access."""
        temp_path = Path(tempfile.mkdtemp(prefix="chatty_test_"))
        yield temp_path
        # Cleanup

        shutil.rmtree(temp_path)  # Remove directory and all contents

    @pytest.fixture
    def temp_file(self, temp_dir: Path) -> Path:
        """Provide a temporary file for tests."""
        temp_file = temp_dir / "test_config.json"
        yield temp_file
        # File is cleaned up by temp_dir fixture

    @pytest.fixture
    def mock_config(self) -> Mock:
        """Provide a properly configured mock Config object."""
        return TestDataFactory.create_mock_config()

    @pytest.mark.config
    @pytest.mark.parametrize("config_file", ["", "test.json", "config/test.json"])
    def test_config_initialization_variations(
        self, config_file: str, temp_dir: Path
    ) -> None:
        """
        Test Config initialization with various file paths.

        Ensures Config can handle different file path scenarios including
        empty paths, relative paths, and nested directory paths.
        """
        if config_file and not config_file.startswith("/"):
            config_file = str(temp_dir / config_file)

        config = Config(config_file)
        assert hasattr(
            config, "config_data"
        ), "Config should have config_data attribute"
        assert hasattr(config, "config"), "Config should have config attribute"
        assert isinstance(
            config.config_data, dict
        ), "config_data should be a dictionary"

    @pytest.mark.config
    @pytest.mark.error_handling
    @pytest.mark.parametrize(
        "invalid_json,expected_error",
        [
            ("{invalid json", "JSONDecodeError"),
            ('{"incomplete": json}', "JSONDecodeError"),
            ("null", "JSONDecodeError"),
            ("undefined", "JSONDecodeError"),
            ('{"key": value}', "JSONDecodeError"),
        ],
    )
    def test_config_invalid_json_handling(
        self, invalid_json: str, expected_error: str, temp_file: Path
    ) -> None:
        """
        Test Config handles invalid JSON gracefully.

        Verifies that Config can recover from corrupted JSON files
        and provides sensible defaults.
        """
        # Write invalid JSON to temp file
        temp_file.write_text(invalid_json)

        # Config should handle invalid JSON gracefully by using empty dict as fallback
        config = Config(str(temp_file))

        # Use custom assertion helper
        TestAssertions.assert_config_valid(config)
        assert config.config_data == {}, f"Should handle {expected_error} gracefully"

    @pytest.mark.parametrize(
        "missing_keys,expected_default",
        [
            ("default_state", "idle"),
            ("general_models_path", "models-idle"),
            ("system_models_path", "models-computer"),
            ("chat_models_path", "models-chatty"),
            ("state_models", {}),
            (
                "api_endpoints",
                lambda: {
                    "home_assistant": "http://homeassistant.domain.home:8123/api",
                    "chatbot_endpoint": "http://localhost:3100/",
                },
            ),
            ("wakeword_state_map", {}),
            ("state_transitions", {}),
            ("commands", {}),
            (
                "advisors",
                lambda: {
                    "enabled": False,
                    "llm_api_mode": "completion",
                    "model": "gpt-oss20b",
                },
            ),
            ("voice_only", False),
        ],
    )
    def test_config_missing_keys_defaults(
        self, missing_keys: str, expected_default: Any, temp_file: Path
    ) -> None:
        """
        Test Config provides sensible defaults for missing configuration keys.

        Ensures that Config gracefully handles missing configuration keys
        by providing appropriate default values.
        """
        # Create a complete config data
        config_data = TestDataFactory.create_valid_config_data()

        # Remove only the specific key we're testing
        if missing_keys in config_data:
            del config_data[missing_keys]

        temp_file.write_text(json.dumps(config_data))

        config = Config(str(temp_file))

        # Check that defaults are applied by accessing the instance attributes
        if callable(expected_default):
            expected_value = expected_default()
            assert (
                getattr(config, missing_keys) == expected_value
            ), f"Should provide default {expected_value} for missing key {missing_keys}"
        else:
            assert (
                getattr(config, missing_keys) == expected_default
            ), f"Should provide default {expected_default} for missing key {missing_keys}"

    @pytest.mark.parametrize("state", ["idle", "computer", "chatty", "invalid"])
    def test_config_state_validation(self, state):
        """Test Config state validation."""
        config = Config()
        config.default_state = state
        # Should not raise exception for valid states
        if state in ["idle", "computer", "chatty"]:
            assert config.default_state == state
        else:
            # Invalid state should be handled gracefully
            assert config.default_state == state  # Config doesn't validate

    @pytest.mark.parametrize(
        "model_path",
        [
            "/valid/path",
            "relative/path",
            "",
            None,
            "~/user/path",
            "/path/with spaces",
            "/path/with/special-chars!@#",
        ],
    )
    def test_config_model_path_handling(self, model_path):
        """Test Config handles various model path formats."""
        config = Config()
        config.general_models_path = model_path
        assert config.general_models_path == model_path

    @pytest.mark.parametrize(
        "endpoint_config",
        [
            {"home_assistant": "http://localhost:8123"},
            {"chatbot_endpoint": "http://localhost:3100"},
            {"custom_endpoint": "https://api.example.com"},
            {},
            {"multiple": "endpoints", "here": "too"},
        ],
    )
    def test_config_api_endpoints_variations(self, endpoint_config):
        """Test Config handles various API endpoint configurations."""
        config = Config()
        config.api_endpoints = endpoint_config
        assert config.api_endpoints == endpoint_config

    @pytest.mark.parametrize(
        "command_config",
        [
            {"hello": {"action": "custom_message", "message": "Hi!"}},
            {"screenshot": {"action": "keypress", "keys": "f12"}},
            {"invalid": {"action": "unknown", "param": "value"}},
            {},
            {"multiple": {"action": "shell", "cmd": "echo test"}},
        ],
    )
    def test_config_command_configurations(self, command_config):
        """Test Config handles various command configurations."""
        config = Config()
        config.commands = command_config
        assert config.commands == command_config

    @pytest.mark.parametrize(
        "advisor_config",
        [
            {"enabled": True, "llm_api_mode": "completion"},
            {"enabled": False, "llm_api_mode": "responses"},
            {"enabled": True, "model": "gpt-4"},
            {},
            {"custom": "config", "values": "here"},
        ],
    )
    def test_config_advisor_configurations(self, advisor_config):
        """Test Config handles various advisor configurations."""
        config = Config()
        config.advisors = advisor_config
        assert config.advisors == advisor_config

    @pytest.mark.parametrize(
        "voice_setting", [True, False, None, "true", "false", 1, 0]
    )
    def test_config_voice_only_settings(self, voice_setting):
        """Test Config handles various voice_only settings."""
        config = Config()
        config.voice_only = voice_setting
        assert config.voice_only == bool(voice_setting)

    def test_config_save_with_empty_file(self):
        """Test Config.save_config with empty config file."""
        config = Config("")
        config.config_data = {"test": "data"}
        config.save_config()  # Should not raise exception

    def test_config_reload_functionality(self):
        """Test Config.reload_config functionality."""
        config = Config()
        _original_data = config.config_data.copy()
        result = config.reload_config()
        assert isinstance(result, bool)

    def test_config_to_dict_conversion(self):
        """Test Config.to_dict conversion."""
        config = Config()
        result = config.to_dict()
        assert isinstance(result, dict)
        assert "model_actions" in result

    @pytest.mark.parametrize(
        "env_var,value",
        [
            ("CHATCOMM_CHECK_FOR_UPDATES", "true"),
            # Add more env var tests as needed from original
        ],
    )
    def test_config_env_overrides(self, env_var, value, monkeypatch):
        """Test Config environment variable overrides."""
        monkeypatch.setenv(env_var, value)
        config = Config()
        # Check that the environment variable was properly applied
        if env_var == "CHATCOMM_CHECK_FOR_UPDATES":
            assert hasattr(config, "check_for_updates")
            assert config.check_for_updates is True
        else:
            # For other env vars, check if they were applied to config_data
            assert config.config_data.get(env_var.lower()) == value
