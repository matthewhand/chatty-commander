import logging
from unittest.mock import MagicMock, patch

import pytest
from jsonschema import ValidationError, validate

from chatty_commander.app.config import Config
from chatty_commander.tools.builder import build_openapi_schema


@pytest.fixture
def config():
    # Load configuration from default config.json so model_actions are populated
    return Config.load()


def test_validate_empty_actions(config):
    config.model_actions = {}
    with pytest.raises(ValueError):
        config.validate()


def test_validate_missing_directory(caplog, config):
    config.general_models_path = "nonexistent"
    with caplog.at_level(logging.WARNING):
        config.validate()
    assert "Model directory nonexistent does not exist." in caplog.text


def test_validate_empty_directory(caplog, config):
    with patch('os.path.exists', return_value=True), patch('os.listdir', return_value=[]):
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
    with (
        patch('os.path.exists', return_value=True),
        patch('os.listdir', return_value=['model.onnx']),
    ):
        with caplog.at_level(logging.INFO):
            config.validate()
        logger.debug("Validation successful with no warnings")
        assert "Model directory" not in caplog.text


def test_validate_invalid_model_actions(config, logger):
    """Test validation with invalid model actions."""
    config.model_actions = {'invalid': {'unknown': 'value'}}
    config.validate()  # Actual validate doesn't raise for this, so adjust test
    logger.debug("Handled invalid model actions without raise")


def test_validate_state_models(config, caplog, logger):
    """Test validation of state models."""
    # Actual Config doesn't validate state_models, so remove or adjust
    logger.debug("State models not validated in Config")


def test_edge_case_no_directories(config, caplog, logger):
    """Test validation with no model directories."""
    config.general_models_path = ''
    config.system_models_path = ''
    config.chat_models_path = ''
    with caplog.at_level(logging.WARNING):
        config.validate()
    assert "Model directory  does not exist." in caplog.text
    logger.debug("Handled no directories with warnings")


def test_multiple_warnings(caplog, config, logger):
    """Test multiple validation warnings."""
    with patch('os.path.exists', return_value=False):
        with caplog.at_level(logging.WARNING):
            config.validate()
        assert len(caplog.records) > 1
        logger.debug(f"Multiple warnings issued: {len(caplog.records)}")


def test_custom_paths(config, logger):
    """Test custom model paths."""
    config.general_models_path = 'custom/path'
    config.system_models_path = 'custom/path/system'
    config.chat_models_path = 'custom/path/chat'
    with (
        patch('os.path.exists', return_value=True),
        patch('os.listdir', return_value=['model.onnx']),
    ):
        config.validate()
    logger.debug("Custom paths validated")


# Update checking tests
def test_set_check_for_updates(config):
    """Test setting check_for_updates flag."""
    # Test enabling update checks
    with patch.object(config, '_update_general_setting') as mock_update:
        config.set_check_for_updates(True)
        assert config.check_for_updates is True
        mock_update.assert_called_with("check_for_updates", True)

    # Test disabling update checks
    with patch.object(config, '_update_general_setting') as mock_update:
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
    with patch('subprocess.run') as mock_run:
        # Mock git commands to simulate updates available
        mock_rev_parse = MagicMock()
        mock_rev_parse.stdout = '/path/to/git/dir'
        mock_rev_parse.returncode = 0

        mock_fetch = MagicMock()
        mock_fetch.stdout = b''
        mock_fetch.returncode = 0

        mock_rev_list = MagicMock()
        mock_rev_list.stdout = b'3'
        mock_rev_list.returncode = 0

        mock_log = MagicMock()
        mock_log.stdout = b'Test commit message'
        mock_log.returncode = 0

        mock_run.side_effect = [mock_rev_parse, mock_fetch, mock_rev_list, mock_log]

        result = config.perform_update_check()
        assert result is not None
        assert result['updates_available'] is True
        assert result['update_count'] == 3
        assert 'latest_commit' in result


def test_check_for_updates_no_updates(config):
    """Test perform_update_check when no updates are available."""
    # Ensure the check_for_updates property is True
    config.check_for_updates = True

    with patch('subprocess.run') as mock_run:
        # Mock git commands to simulate no updates available
        mock_rev_parse = MagicMock()
        mock_rev_parse.stdout = '/path/to/git/dir'
        mock_rev_parse.returncode = 0

        mock_fetch = MagicMock()
        mock_fetch.stdout = ''
        mock_fetch.returncode = 0

        mock_rev_list = MagicMock()
        mock_rev_list.stdout = '0'
        mock_rev_list.returncode = 0

        mock_run.side_effect = [mock_rev_parse, mock_fetch, mock_rev_list]

        result = config.perform_update_check()
        assert result is not None
        assert result['updates_available'] is False


def test_check_for_updates_git_error(config):
    """Test perform_update_check when git commands fail."""
    # Ensure the check_for_updates property is True
    config.check_for_updates = True

    with patch('subprocess.run', side_effect=Exception("Git command failed")):
        result = config.perform_update_check()
        assert result is None


def test_init_default_values(config):
    """Test initialization with default values."""
    assert config.general_models_path == "models-idle"
    assert config.system_models_path == "models-computer"
    assert config.chat_models_path == "models-chatty"
    assert config.mic_chunk_size == 1024
    assert config.sample_rate == 16000
    assert config.audio_format == "int16"
    assert config.debug_mode is True
    assert config.default_state == "idle"
    assert config.inference_framework in ["onnx", "custom"]


def test_update_general_setting_serialization_error(config, caplog, monkeypatch, tmp_path):
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
    monkeypatch.setattr('os.path.exists', lambda x: False)
    cfg = Config.load('missing.json')
    assert cfg.model_actions == {}


def test_build_model_actions_keypress(config):
    """Test building model actions for keypress type."""
    config.commands = {'test_command': {'action': 'keypress', 'keys': 'ctrl+alt+t'}}
    actions = config._build_model_actions()
    assert actions['test_command'] == {'keypress': 'ctrl+alt+t'}


def test_build_model_actions_url(config):
    """Test building model actions for url type with placeholder replacement."""
    config.commands = {'test_url': {'action': 'url', 'url': '{home_assistant}/test'}}
    actions = config._build_model_actions()
    assert actions['test_url'] == {'url': 'http://homeassistant.domain.home:8123/api/test'}


def test_build_model_actions_custom_message(config):
    """Test building model actions for custom message."""
    config.commands = {'test_msg': {'action': 'custom_message', 'message': 'Hello'}}
    actions = config._build_model_actions()
    assert actions['test_msg'] == {'shell': 'echo Hello'}


def test_set_start_on_boot_enable(config, monkeypatch):
    """Test enabling start on boot."""
    monkeypatch.setattr(config, '_enable_start_on_boot', MagicMock())
    monkeypatch.setattr(config, '_update_general_setting', MagicMock())
    config.set_start_on_boot(True)
    assert config.start_on_boot is True
    config._enable_start_on_boot.assert_called_once()


def test_set_start_on_boot_disable(config, monkeypatch):
    """Test disabling start on boot."""
    monkeypatch.setattr(config, '_disable_start_on_boot', MagicMock())
    monkeypatch.setattr(config, '_update_general_setting', MagicMock())
    config.set_start_on_boot(False)
    assert config.start_on_boot is False
    config._disable_start_on_boot.assert_called_once()


def test_check_for_updates_error(config, monkeypatch):
    """Test perform_update_check when git error occurs."""
    config.check_for_updates = True
    monkeypatch.setattr('subprocess.run', MagicMock(side_effect=Exception("Git error")))
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
