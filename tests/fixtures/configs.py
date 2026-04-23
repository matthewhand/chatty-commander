# fixtures/configs.py
"""Test fixtures for configuration-related tests."""

from unittest.mock import Mock

import pytest


class ConfigFixtures:
    """Factory for configuration test data."""
    
    DEFAULT_CONFIG = {
        "wake_words": ["hey computer", "ok chatty"],
        "default_state": "idle",
        "confidence_threshold": 0.7,
        "audio": {
            "sample_rate": 16000,
            "chunk_size": 1024
        },
        "web_server": {
            "host": "0.0.0.0",
            "port": 8000,
            "auth_enabled": False
        }
    }
    
    MINIMAL_CONFIG = {
        "wake_words": ["test"],
        "default_state": "idle"
    }
    
    FULL_CONFIG = {
        "wake_words": ["hey computer", "ok chatty", "yo assistant"],
        "default_state": "idle",
        "confidence_threshold": 0.8,
        "audio": {
            "sample_rate": 16000,
            "chunk_size": 1024,
            "device_index": 0
        },
        "web_server": {
            "host": "127.0.0.1",
            "port": 8080,
            "auth_enabled": True,
            "cors_origins": ["http://localhost:3000"]
        },
        "model_actions": {
            "open_browser": {"type": "url", "url": "https://google.com"},
            "play_music": {"type": "shell", "command": "playerctl play"}
        },
        "llm": {
            "backend": "openai",
            "model": "gpt-4",
            "temperature": 0.7
        }
    }
    
    @staticmethod
    def create_minimal_config():
        """Create minimal working configuration."""
        return ConfigFixtures.MINIMAL_CONFIG.copy()
    
    @staticmethod
    def create_default_config():
        """Create default test configuration."""
        return ConfigFixtures.DEFAULT_CONFIG.copy()
    
    @staticmethod
    def create_full_config():
        """Create full configuration with all options."""
        return ConfigFixtures.FULL_CONFIG.copy()
    
    @staticmethod
    def create_mock_config(overrides=None):
        """Create a mock config object."""
        config = Mock()
        data = ConfigFixtures.DEFAULT_CONFIG.copy()
        if overrides:
            data.update(overrides)
        
        for key, value in data.items():
            setattr(config, key, value)
        
        config.save_config = Mock(return_value=True)
        config.reload_config = Mock(return_value=True)
        config.validate = Mock(return_value=True)
        return config


# Pytest fixtures
@pytest.fixture
def minimal_config():
    """Provide minimal configuration."""
    return ConfigFixtures.create_minimal_config()


@pytest.fixture
def default_config():
    """Provide default configuration."""
    return ConfigFixtures.create_default_config()


@pytest.fixture
def full_config():
    """Provide full configuration."""
    return ConfigFixtures.create_full_config()


@pytest.fixture
def mock_config():
    """Provide mock configuration object."""
    return ConfigFixtures.create_mock_config()


config_fixtures = ConfigFixtures
