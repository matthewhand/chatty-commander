"""Unit tests for backends module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from chatty_commander.app.backends import (
    BackendBase,
    BackendRegistry,
    BackendManager,
    BackendStatus,
)


class TestBackendBase:
    """Test suite for BackendBase functionality."""

    @pytest.fixture
    def mock_backend(self):
        """Create a mock backend instance."""
        backend = Mock(spec=BackendBase)
        backend.name = "test_backend"
        backend.is_available.return_value = True
        backend.get_status.return_value = BackendStatus.AVAILABLE
        return backend

    def test_backend_base_initialization(self, mock_backend):
        """Test BackendBase initializes correctly."""
        assert mock_backend.name == "test_backend"
        assert mock_backend.is_available() is True

    def test_backend_status_available(self, mock_backend):
        """Test backend returns correct status when available."""
        status = mock_backend.get_status()
        assert status == BackendStatus.AVAILABLE

    def test_backend_status_unavailable(self):
        """Test backend returns UNAVAILABLE status."""
        backend = Mock(spec=BackendBase)
        backend.is_available.return_value = False
        backend.get_status.return_value = BackendStatus.UNAVAILABLE

        status = backend.get_status()
        assert status == BackendStatus.UNAVAILABLE


class TestBackendRegistry:
    """Test suite for BackendRegistry functionality."""

    @pytest.fixture
    def registry(self):
        """Create a fresh BackendRegistry instance."""
        return BackendRegistry()

    def test_register_backend(self, registry):
        """Test registering a backend."""
        mock_backend = Mock(spec=BackendBase)
        mock_backend.name = "test_backend"

        registry.register(mock_backend)

        assert "test_backend" in registry.backends
        assert registry.backends["test_backend"] == mock_backend

    def test_unregister_backend(self, registry):
        """Test unregistering a backend."""
        mock_backend = Mock(spec=BackendBase)
        mock_backend.name = "test_backend"

        registry.register(mock_backend)
        registry.unregister("test_backend")

        assert "test_backend" not in registry.backends

    def test_get_backend_exists(self, registry):
        """Test getting a registered backend."""
        mock_backend = Mock(spec=BackendBase)
        mock_backend.name = "test_backend"

        registry.register(mock_backend)
        result = registry.get("test_backend")

        assert result == mock_backend

    def test_get_backend_not_exists(self, registry):
        """Test getting a non-existent backend returns None."""
        result = registry.get("nonexistent")

        assert result is None

    def test_list_backends(self, registry):
        """Test listing all registered backends."""
        backend1 = Mock(spec=BackendBase)
        backend1.name = "backend1"
        backend2 = Mock(spec=BackendBase)
        backend2.name = "backend2"

        registry.register(backend1)
        registry.register(backend2)

        backends = registry.list()

        assert len(backends) == 2
        assert "backend1" in backends
        assert "backend2" in backends


class TestBackendManager:
    """Test suite for BackendManager functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock()
        config.get.return_value = {
            "backends": {
                "ollama": {"enabled": True, "url": "http://localhost:11434"},
                "openai": {"enabled": False, "api_key": None},
            }
        }
        return config

    @pytest.fixture
    def manager(self, mock_config):
        """Create BackendManager with mocked config."""
        return BackendManager(mock_config)

    def test_manager_initialization(self, manager):
        """Test BackendManager initializes with config."""
        assert manager.config is not None

    def test_get_enabled_backends(self, manager):
        """Test getting list of enabled backends."""
        enabled = manager.get_enabled_backends()

        assert "ollama" in enabled
        assert "openai" not in enabled

    def test_is_backend_enabled_true(self, manager):
        """Test checking if enabled backend is enabled."""
        result = manager.is_backend_enabled("ollama")

        assert result is True

    def test_is_backend_enabled_false(self, manager):
        """Test checking if disabled backend is enabled."""
        result = manager.is_backend_enabled("openai")

        assert result is False

    def test_is_backend_enabled_nonexistent(self, manager):
        """Test checking if non-existent backend is enabled."""
        result = manager.is_backend_enabled("nonexistent")

        assert result is False
