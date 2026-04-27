"""Unit tests for core module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from chatty_commander.app.core import ChattyCommanderCore, CoreStatus


class TestChattyCommanderCore:
    """Test suite for ChattyCommanderCore functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock()
        config.get.return_value = {
            "app": {"name": "test_app", "version": "1.0.0"},
            "features": {"voice": True, "web": False},
        }
        return config

    @pytest.fixture
    def core(self, mock_config):
        """Create ChattyCommanderCore with mocked config."""
        return ChattyCommanderCore(mock_config)

    def test_core_initialization(self, core):
        """Test Core initializes with config."""
        assert core.config is not None
        assert core.status == CoreStatus.INITIALIZED

    def test_core_status_transitions(self, core):
        """Test core status transitions properly."""
        assert core.status == CoreStatus.INITIALIZED

        core.start()
        assert core.status == CoreStatus.RUNNING

        core.stop()
        assert core.status == CoreStatus.STOPPED

    def test_core_start_failure_handling(self, core):
        """Test core handles start failures gracefully."""
        with patch.object(core, "_initialize_components", side_effect=Exception("Init failed")):
            with pytest.raises(RuntimeError):
                core.start()

            assert core.status == CoreStatus.ERROR

    def test_core_feature_flags(self, core):
        """Test core respects feature flags from config."""
        features = core.get_enabled_features()

        assert "voice" in features
        assert features["voice"] is True
        assert "web" in features
        assert features["web"] is False

    def test_core_get_version(self, core):
        """Test core returns correct version."""
        version = core.get_version()

        assert version == "1.0.0"

    def test_core_health_check_healthy(self, core):
        """Test health check when all components healthy."""
        with patch.object(core, "_check_components", return_value=True):
            health = core.health_check()

            assert health["status"] == "healthy"
            assert health["components"]["all_operational"] is True

    def test_core_health_check_unhealthy(self, core):
        """Test health check when components failing."""
        with patch.object(core, "_check_components", return_value=False):
            health = core.health_check()

            assert health["status"] == "degraded"
            assert health["components"]["all_operational"] is False

    def test_core_restart(self, core):
        """Test core restart functionality."""
        core.start()
        assert core.status == CoreStatus.RUNNING

        core.restart()
        assert core.status == CoreStatus.RUNNING


class TestCoreStatus:
    """Test suite for CoreStatus enum."""

    def test_status_values(self):
        """Test CoreStatus has expected values."""
        assert CoreStatus.INITIALIZED.value == "initialized"
        assert CoreStatus.RUNNING.value == "running"
        assert CoreStatus.STOPPED.value == "stopped"
        assert CoreStatus.ERROR.value == "error"

    def test_status_transitions_valid(self):
        """Test valid status transitions."""
        # Initialized can go to Running
        assert CoreStatus.can_transition(CoreStatus.INITIALIZED, CoreStatus.RUNNING)

        # Running can go to Stopped
        assert CoreStatus.can_transition(CoreStatus.RUNNING, CoreStatus.STOPPED)

        # Stopped can go to Running (restart)
        assert CoreStatus.can_transition(CoreStatus.STOPPED, CoreStatus.RUNNING)

    def test_status_transitions_invalid(self):
        """Test invalid status transitions are rejected."""
        # Cannot go from INITIALIZED directly to STOPPED
        assert not CoreStatus.can_transition(CoreStatus.INITIALIZED, CoreStatus.STOPPED)
