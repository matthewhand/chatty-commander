
import pytest
from unittest.mock import MagicMock
import os
import sys
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.web.web_mode import create_app

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = MagicMock(spec=Config)
    config.web_server = {"host": "0.0.0.0", "port": 8100, "auth_enabled": False}
    return config

@pytest.fixture
def mock_model_manager(mock_config):
    """Mock ModelManager for testing."""
    mm = ModelManager(mock_config, mock_models=True)
    return mm

@pytest.fixture
def test_app(mock_config, mock_model_manager):
    """Create a test FastAPI app with mocked dependencies."""
    app = create_app(
        config=mock_config,
        model_manager=mock_model_manager,
        no_auth=True
    )
    return app
