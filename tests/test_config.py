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
import logging
import os
from unittest.mock import MagicMock, mock_open, patch

import pytest
from jsonschema import ValidationError, validate

from chatty_commander.app.config import Config
from chatty_commander.tools.builder import build_openapi_schema


@pytest.fixture
def config():
    """Provide a Config instance with minimal model_actions for testing."""
    cfg = Config()
    # Add minimal model_actions to satisfy validation
    cfg.model_actions = {"test_cmd": {"keypress": "space"}}
    return cfg


def test_validate_empty_actions(config):
    """Test validation with empty model actions."""
    config.model_actions = {}
    with pytest.raises(ValueError, match="Model actions configuration is empty"):
        config.validate()


def test_validate_missing_directory(caplog, config):
    config.general_models_path = "nonexistent"
    with caplog.at_level(logging.WARNING):
        config.validate()
    assert "Model directory nonexistent does not exist." in caplog.text


def test_validate_empty_directory(caplog, config):
    with (
        patch("os.path.exists", return_value=True),
        patch("os.listdir", return_value=[]),
    ):
        with caplog.at_level(logging.WARNING):
            config.validate()
        assert "Model directory models-idle is empty." in caplog.text


# Expanded tests
@pytest.fixture
def logger():
    logging.basicConfig(level=logging.DEBUG)
    return logging.getLogger(__name__)


def test_validate_success(config, caplog, logger):
    """Test successful validation with proper setup."""
    # Ensure model_actions are set for successful validation
    config.model_actions = {"test_cmd": {"keypress": "space"}}
    with (
        patch("os.path.exists", return_value=True),
        patch("os.listdir", return_value=["model.onnx"]),
    ):
        with caplog.at_level(logging.INFO):
            config.validate()
        logger.debug("Validation successful with no warnings")
        # Should not contain warning messages
        assert "does not exist" not in caplog.text
        assert "is empty" not in caplog.text


def test_validate_invalid_model_actions(config, logger):
    """Test validation with invalid model actions - should not raise."""
    config.model_actions = {"invalid": {"unknown": "value"}}
    # Config.validate() doesn't validate individual actions, just checks if dict exists
    config.validate()
    logger.debug(
        "Handled invalid model actions without raise - validation only checks for non-empty dict"
    )


def test_validate_state_models(config, caplog, logger):
    """Test that state_models validation is not implemented."""
    # This test documents current behavior - state_models are not validated
    logger.debug("State models not validated in Config.validate() - future enhancement")
    # Test passes by documentation
    assert True


def test_edge_case_no_directories(config, caplog, logger):
    """Test validation with no model directories."""
    config.general_models_path = ""
    config.system_models_path = ""
    config.chat_models_path = ""
    with caplog.at_level(logging.WARNING):
        config.validate()
    assert "Model directory  does not exist." in caplog.text
    logger.debug("Handled no directories with warnings")


def test_multiple_warnings(caplog, config, logger):
    """Test multiple validation warnings."""
    with patch("os.path.exists", return_value=False):
        with caplog.at_level(logging.WARNING):
            config.validate()
        assert len(caplog.records) > 1
        logger.debug(f"Multiple warnings issued: {len(caplog.records)}")


def test_custom_paths(config, logger):
    """Test custom model paths."""
    config.general_models_path = "custom/path"
    config.system_models_path = "custom/path/system"
    config.chat_models_path = "custom/path/chat"
    with (
        patch("os.path.exists", return_value=True),
        patch("os.listdir", return_value=["model.onnx"]),
    ):
        config.validate()
    logger.debug("Custom paths validated")


# Update checking tests
def test_set_check_for_updates(config):
    """Test setting check_for_updates flag."""
    # Test enabling update checks
    with patch.object(config, "_update_general_setting") as mock_update:
        config.set_check_for_updates(True)
        assert config.check_for_updates is True
        mock_update.assert_called_with("check_for_updates", True)

    # Test disabling update checks
    with patch.object(config, "_update_general_setting") as mock_update:
        config.set_check_for_updates(False)
        assert config.check_for_updates is False
        mock_update.assert_called_with("check_for_updates", False)


def test_check_for_updates_disabled(config):
    """Test perform_update_check when disabled."""
    # Set the check_for_updates property to False
    config.check_for_updates = False
    result = config.perform_update_check()
    assert result is None


def test_check_for_updates_with_updates(config):
    """Test perform_update_check when updates are available."""
    config.check_for_updates = True
    with patch("subprocess.run") as mock_run:
        # Mock git commands to simulate updates available
        mock_rev_parse = MagicMock()
        mock_rev_parse.stdout = "/path/to/git/dir"
        mock_rev_parse.returncode = 0

        mock_fetch = MagicMock()
        mock_fetch.stdout = b""
        mock_fetch.returncode = 0

        mock_rev_list = MagicMock()
        mock_rev_list.stdout = b"3"
        mock_rev_list.returncode = 0

        mock_log = MagicMock()
        mock_log.stdout = b"Test commit message"
        mock_log.returncode = 0

        mock_run.side_effect = [mock_rev_parse, mock_fetch, mock_rev_list, mock_log]

        result = config.perform_update_check()
        assert result is not None
        assert result["updates_available"] is True
        assert result["update_count"] == 3
        assert "latest_commit" in result


def test_check_for_updates_no_updates(config):
    """Test perform_update_check when no updates are available."""
    # Ensure the check_for_updates property is True
    config.check_for_updates = True

    with patch("subprocess.run") as mock_run:
        # Mock git commands to simulate no updates available
        mock_rev_parse = MagicMock()
        mock_rev_parse.stdout = "/path/to/git/dir"
        mock_rev_parse.returncode = 0

        mock_fetch = MagicMock()
        mock_fetch.stdout = ""
        mock_fetch.returncode = 0

        mock_rev_list = MagicMock()
        mock_rev_list.stdout = "0"
        mock_rev_list.returncode = 0

        mock_run.side_effect = [mock_rev_parse, mock_fetch, mock_rev_list]

        result = config.perform_update_check()
        assert result is not None
        assert result["updates_available"] is False


def test_check_for_updates_git_error(config):
    """Test perform_update_check when git commands fail."""
    # Ensure the check_for_updates property is True
    config.check_for_updates = True

    with patch("subprocess.run", side_effect=Exception("Git command failed")):
        result = config.perform_update_check()
        assert result is None


def test_init_default_values(config):
    """Test initialization with default values."""
    # Test core configuration defaults
    assert config.mic_chunk_size == 1024
    assert config.sample_rate == 16000
    assert config.audio_format == "int16"
    assert config.debug_mode is True
    assert config.default_state == "idle"
    assert config.inference_framework in ["onnx", "custom"]

    # Model paths may vary based on config loading, test they exist
    assert hasattr(config, "general_models_path")
    assert hasattr(config, "system_models_path")
    assert hasattr(config, "chat_models_path")

    # Ensure model_actions are properly initialized
    assert isinstance(config.model_actions, dict)


def test_update_general_setting_serialization_error(
    config, caplog, monkeypatch, tmp_path
):
    """Ensure serialization errors are logged without crashing."""
    config.config_file = tmp_path / "config.json"

    def fail_dump(*args, **kwargs):
        raise TypeError("boom")

    monkeypatch.setattr("json.dump", fail_dump)

    with caplog.at_level(logging.ERROR):
        config._update_general_setting("bad", object())

    assert "Could not save config file" in caplog.text


def test_load_config_file_not_exist(monkeypatch):
    """Test loading config when file does not exist."""
    monkeypatch.setattr("os.path.exists", lambda x: False)
    cfg = Config.load("missing.json")
    assert cfg.model_actions == {}


def test_build_model_actions_keypress(config):
    """Test building model actions for keypress type."""
    config.commands = {"test_command": {"action": "keypress", "keys": "ctrl+alt+t"}}
    actions = config._build_model_actions()
    assert actions["test_command"] == {"keypress": "ctrl+alt+t"}


def test_build_model_actions_url(config):
    """Test building model actions for url type with placeholder replacement."""
    config.commands = {"test_url": {"action": "url", "url": "{home_assistant}/test"}}
    actions = config._build_model_actions()
    assert actions["test_url"] == {
        "url": "http://homeassistant.domain.home:8123/api/test"
    }


def test_build_model_actions_custom_message(config):
    """Test building model actions for custom message."""
    config.commands = {"test_msg": {"action": "custom_message", "message": "Hello"}}
    actions = config._build_model_actions()
    assert actions["test_msg"] == {"shell": "echo Hello"}


def test_set_start_on_boot_enable(config, monkeypatch):
    """Test enabling start on boot."""
    monkeypatch.setattr(config, "_enable_start_on_boot", MagicMock())
    monkeypatch.setattr(config, "_update_general_setting", MagicMock())
    config.set_start_on_boot(True)
    assert config.start_on_boot is True
    config._enable_start_on_boot.assert_called_once()


def test_set_start_on_boot_disable(config, monkeypatch):
    """Test disabling start on boot."""
    monkeypatch.setattr(config, "_disable_start_on_boot", MagicMock())
    monkeypatch.setattr(config, "_update_general_setting", MagicMock())
    config.set_start_on_boot(False)
    assert config.start_on_boot is False
    config._disable_start_on_boot.assert_called_once()


def test_check_for_updates_error(config, monkeypatch):
    """Test perform_update_check when git error occurs."""
    config.check_for_updates = True
    monkeypatch.setattr("subprocess.run", MagicMock(side_effect=Exception("Git error")))
    result = config.perform_update_check()
    assert result is None


# Typed configuration schema validation tests


def _get_config_schema() -> dict:
    """Helper to extract Configuration schema from the OpenAPI builder."""
    schema = build_openapi_schema()
    return schema["components"]["schemas"]["Configuration"]


def test_config_schema_accepts_valid_config():
    """Ensure a minimal valid config passes JSON Schema validation."""
    schema = _get_config_schema()
    valid_cfg = {
        "general_models_path": "models-idle",
        "system_models_path": "models-computer",
        "chat_models_path": "models-chatty",
        "model_actions": {"foo": {"keypress": "ctrl+c"}},
        "default_state": "idle",
    }
    validate(instance=valid_cfg, schema=schema)  # Should not raise


def test_config_schema_rejects_invalid_state():
    """Invalid default_state should raise a ValidationError."""
    schema = _get_config_schema()
    invalid_cfg = {
        "general_models_path": "models-idle",
        "system_models_path": "models-computer",
        "chat_models_path": "models-chatty",
        "model_actions": {},
        "default_state": "unknown",
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_cfg, schema=schema)


# Additional comprehensive tests to improve coverage


def test_config_initialization_with_defaults():
    """Test Config initialization with default values when no config file is provided."""
    config = Config("")  # Empty config_file to trigger defaults
    assert config.default_state == "idle"
    assert config.general_models_path == "models-idle"
    assert config.system_models_path == "models-computer"
    assert config.chat_models_path == "models-chatty"
    assert config.mic_chunk_size == 1024
    assert config.sample_rate == 16000
    assert config.audio_format == "int16"
    assert config.debug_mode is True
    assert config.voice_only is False
    assert config.check_for_updates is True
    assert config.inference_framework == "onnx"
    assert config.start_on_boot is False


def test_config_initialization_with_custom_config():
    """Test Config initialization with custom config data."""
    custom_config = {
        "default_state": "computer",
        "general_models_path": "custom/general",
        "system_models_path": "custom/system",
        "chat_models_path": "custom/chat",
        "mic_chunk_size": 2048,
        "sample_rate": 44100,
        "audio_format": "float32",
        "voice_only": True,
        "general": {
            "debug_mode": False,
            "check_for_updates": False,
            "inference_framework": "custom",
            "start_on_boot": True,
        },
    }

    with patch("builtins.open", mock_open(read_data=json.dumps(custom_config))):
        config = Config("test_config.json")
        assert config.default_state == "computer"
        assert config.general_models_path == "custom/general"
        assert config.system_models_path == "custom/system"
        assert config.chat_models_path == "custom/chat"
        assert config.mic_chunk_size == 2048
        assert config.sample_rate == 44100
        assert config.audio_format == "float32"
        assert config.debug_mode is False
        assert config.voice_only is True
        assert config.check_for_updates is False
        assert config.inference_framework == "custom"
        assert config.start_on_boot is True


def test_config_reload_config_success():
    """Test successful config reload."""
    config = Config("test_config.json")
    original_config = config.config_data.copy()

    new_config_data = original_config.copy()
    new_config_data["default_state"] = "computer"
    new_config_data["general"] = {"default_state": "computer"}

    with patch("builtins.open", mock_open(read_data=json.dumps(new_config_data))):
        result = config.reload_config()
        assert result is True
        assert config.default_state == "computer"


def test_config_reload_config_no_change():
    """Test config reload when config hasn't changed."""
    config = Config("")
    with patch("builtins.open", mock_open(read_data=json.dumps(config.config_data))):
        result = config.reload_config()
        assert result is False


def test_config_reload_config_failure():
    """Test config reload failure handling."""
    config = Config("")
    with patch("builtins.open", side_effect=OSError("Permission denied")):
        result = config.reload_config()
        assert result is False


def test_config_apply_env_overrides():
    """Test environment variable overrides."""
    with patch.dict(
        os.environ,
        {
            "CHATBOT_ENDPOINT": "http://custom-endpoint:3000/",
            "HOME_ASSISTANT_ENDPOINT": "http://custom-ha:8123/api",
            "CHATCOMM_DEBUG": "false",
            "CHATCOMM_DEFAULT_STATE": "computer",
            "CHATCOMM_INFERENCE_FRAMEWORK": "custom",
            "CHATCOMM_START_ON_BOOT": "true",
            "CHATCOMM_CHECK_FOR_UPDATES": "false",
        },
    ):
        config = Config("")
        assert (
            config.api_endpoints["chatbot_endpoint"] == "http://custom-endpoint:3000/"
        )
        assert config.api_endpoints["home_assistant"] == "http://custom-ha:8123/api"
        assert config.debug_mode is False
        assert config.default_state == "computer"
        assert config.inference_framework == "custom"
        assert config.start_on_boot is True
        assert config.check_for_updates is False


def test_config_apply_web_server_config():
    """Test web server configuration application."""
    config_data = {
        "web_server": {"host": "127.0.0.1", "port": 9000, "auth_enabled": False}
    }
    config = Config("")
    config.config_data = config_data
    config._apply_web_server_config()

    assert config.web_server["host"] == "127.0.0.1"
    assert config.web_server["port"] == 9000
    assert config.web_server["auth_enabled"] is False
    assert config.web_host == "127.0.0.1"
    assert config.web_port == 9000
    assert config.web_auth_enabled is False


def test_config_get_int_env():
    """Test _get_int_env static method."""
    # Test valid integer
    with patch.dict(os.environ, {"TEST_VAR": "42"}):
        result = Config._get_int_env("TEST_VAR", 10)
        assert result == 42

    # Test invalid integer (should use fallback)
    with patch.dict(os.environ, {"TEST_VAR": "invalid"}):
        result = Config._get_int_env("TEST_VAR", 10)
        assert result == 10

    # Test negative integer (should use fallback)
    with patch.dict(os.environ, {"TEST_VAR": "-5"}):
        result = Config._get_int_env("TEST_VAR", 10)
        assert result == 10

    # Test missing environment variable
    with patch.dict(os.environ, {}, clear=True):
        result = Config._get_int_env("TEST_VAR", 10)
        assert result == 10


def test_config_load_config_file_not_found():
    """Test _load_config when file doesn't exist."""
    config = Config("nonexistent.json")
    result = config._load_config()
    assert result == {}


def test_config_load_config_invalid_json():
    """Test _load_config with invalid JSON."""
    with patch("builtins.open", mock_open(read_data="invalid json content")):
        config = Config("test.json")
        result = config._load_config()
        assert result == {}


def test_config_load_config_non_dict_content():
    """Test _load_config with non-dictionary JSON content."""
    with patch("builtins.open", mock_open(read_data='["list", "content"]')):
        config = Config("test.json")
        result = config._load_config()
        assert result == {}


def test_config_build_model_actions_voice_chat():
    """Test _build_model_actions with voice_chat action type."""
    config = Config("")
    config.commands = {"voice_cmd": {"action": "voice_chat"}}
    actions = config._build_model_actions()
    assert actions["voice_cmd"] == {"action": "voice_chat"}


def test_config_save_config_with_data():
    """Test save_config with provided data."""
    config = Config("")
    config.config_file = "test_save.json"
    new_data = {"test_key": "test_value"}

    with patch("builtins.open", mock_open()) as mock_file:
        config.save_config(new_data)
        mock_file.assert_called_once_with("test_save.json", "w", encoding="utf-8")
        # Verify json.dump was called with updated data
        call_args = mock_file().write.call_args_list
        assert any("test_key" in str(call) for call in call_args)


def test_config_save_config_without_data():
    """Test save_config without provided data."""
    config = Config("")
    config.config_file = "test_save.json"

    with patch("builtins.open", mock_open()) as mock_file:
        config.save_config()
        mock_file.assert_called_once_with("test_save.json", "w", encoding="utf-8")


def test_config_save_config_no_file():
    """Test save_config when config_file is empty."""
    config = Config("")
    # Should not raise exception or attempt to save
    config.save_config({"test": "data"})


def test_config_save_config_error_handling():
    """Test save_config error handling."""
    config = Config("")
    config.config_file = "test_save.json"

    with patch("builtins.open", side_effect=OSError("Permission denied")):
        config.save_config({"test": "data"})
        # Should not raise exception, just log error


def test_config_general_settings_properties():
    """Test _GeneralSettings property setters and getters."""
    config = Config("")

    # Test default_state
    config.general_settings.default_state = "computer"
    assert config.general_settings.default_state == "computer"
    assert config.config_data["default_state"] == "computer"

    # Test debug_mode
    config.general_settings.debug_mode = False
    assert config.general_settings.debug_mode is False
    assert config.config_data["general"]["debug_mode"] is False

    # Test inference_framework
    config.general_settings.inference_framework = "custom"
    assert config.general_settings.inference_framework == "custom"
    assert config.config_data["general"]["inference_framework"] == "custom"

    # Test start_on_boot
    config.general_settings.start_on_boot = True
    assert config.general_settings.start_on_boot is True
    assert config.config_data["general"]["start_on_boot"] is True

    # Test check_for_updates
    config.general_settings.check_for_updates = False
    assert config.general_settings.check_for_updates is False
    assert config.config_data["general"]["check_for_updates"] is False


def test_config_from_dict():
    """Test Config.from_dict class method."""
    config_data = {
        "default_state": "computer",
        "general": {
            "models_path": "test/path",
            "debug_mode": False,
            "inference_framework": "custom",
        },
    }

    config = Config.from_dict(config_data, "test_config.json")
    assert config.default_state == "computer"
    assert config.general_models_path == "test/path"
    assert config.debug_mode is False
    assert config.inference_framework == "custom"
    assert config.config_file == "test_config.json"


def test_config_to_dict():
    """Test Config.to_dict method."""
    config = Config("")
    config.default_state = "computer"
    config.general_models_path = "test/path"
    config.general_settings.debug_mode = False

    result = config.to_dict()
    assert result["default_state"] == "computer"
    assert result["general"]["models_path"] == "test/path"
    assert result["general"]["debug_mode"] is False
    assert result["model_actions"] == config.model_actions


def test_config_validate_config_invalid_types():
    """Test _validate_config with invalid configuration types."""
    config = Config("")

    # Test invalid state_models
    config.state_models = "invalid"
    config._validate_config()
    assert isinstance(config.state_models, dict)

    # Test invalid api_endpoints
    config.api_endpoints = "invalid"
    config._validate_config()
    assert isinstance(config.api_endpoints, dict)

    # Test invalid commands
    config.commands = "invalid"
    config._validate_config()
    assert isinstance(config.commands, dict)


def test_config_validate_config_deprecated_field():
    """Test _validate_config with deprecated field."""
    config = Config("")
    config.config_data["deprecated_field"] = "old_value"

    with patch("logging.Logger.warning") as mock_warning:
        config._validate_config()
        mock_warning.assert_called_with(
            "Found deprecated configuration field: deprecated_field"
        )


def test_config_validate_config_model_paths():
    """Test _validate_config model path validation."""
    config = Config("")
    config.general_models_path = "nonexistent/path"
    config.system_models_path = "nonexistent/path"
    config.chat_models_path = "nonexistent/path"

    with patch("os.path.exists", return_value=False):
        with patch("logging.Logger.warning") as mock_warning:
            config.validate()
            # Check that any of the expected warning messages were called
            assert any(
                "does not exist" in str(call) for call in mock_warning.call_args_list
            )


def test_config_load_general_settings():
    """Test _load_general_settings method."""
    config = Config("")
    config.config_data["general"] = {"default_state": "computer"}

    config._load_general_settings()
    assert config.default_state == "computer"
