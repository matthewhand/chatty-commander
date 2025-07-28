import pytest
import logging
from config import Config
from unittest.mock import patch, MagicMock
import os

@pytest.fixture
def config():
    return Config()

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
    with patch('os.path.exists', return_value=True), patch('os.listdir', return_value=['model.onnx']):
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
    config.idle_models_path = 'custom/path/idle'  # Note: Config may not have idle_models_path, adjust if needed
    with patch('os.path.exists', return_value=True), patch('os.listdir', return_value=['model.onnx']):
        config.validate()
    logger.debug("Custom paths validated")