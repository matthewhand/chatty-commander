import pytest
import logging
from config import Config
from unittest.mock import patch

def test_validate_empty_actions():
    config = Config()
    config.model_actions = {}
    with pytest.raises(ValueError):
        config.validate()

def test_validate_missing_directory(caplog):
    config = Config()
    config.general_models_path = "nonexistent"
    with caplog.at_level(logging.WARNING):
        config.validate()
    assert "Model directory nonexistent does not exist." in caplog.text

def test_validate_empty_directory(caplog):
    config = Config()
    with patch('os.path.exists', return_value=True), patch('os.listdir', return_value=[]):
        with caplog.at_level(logging.WARNING):
            config.validate()
        assert "Model directory models-idle is empty." in caplog.text