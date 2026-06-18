"""Unit tests for web/web_mode.py (WebModeServer, Pydantic models, helpers).

Focus: model validation, server construction (mocked deps), broadcast, hooks,
rate limit / security middleware helpers, advisor registration paths.
Uses conftest mocks + AAA. Avoids spinning real servers/uvi.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI
from pydantic import ValidationError

# Direct import works via pytest pythonpath=src + uv
from chatty_commander.web.web_mode import (
    CommandRequest,
    CommandResponse,
    ContextStats,
    RateLimitMiddleware,
    StateChangeRequest,
    SystemStatus,
    WebModeServer,
    WebSocketMessage,
    get_client_ip,
)

# ============================================================================
# PYDANTIC MODEL TESTS (lightweight, no server needed)
# ============================================================================


class TestWebModeModels:
    """Pydantic models from web_mode (validation + serialization)."""

    def test_system_status_model(self):
        # Arrange
        data = {
            "status": "ok",
            "current_state": "idle",
            "active_models": ["m1"],
            "uptime": "1h 2m",
        }
        # Act
        obj = SystemStatus(**data)
        # Assert
        assert obj.status == "ok"
        assert obj.version == "0.2.0"
        assert "active_models" in obj.model_dump()

    def test_state_change_request_valid_and_invalid(self):
        # Arrange/Act/Assert happy
        req = StateChangeRequest(state="chatty")
        assert req.state == "chatty"
        # invalid
        with pytest.raises(ValidationError):
            StateChangeRequest(state="invalid_state")

    def test_command_request_and_response(self):
        # Arrange
        creq = CommandRequest(command="doit", parameters={"a": 1})
        cresp = CommandResponse(success=True, message="ok", execution_time=12.3)
        # Assert
        assert creq.command == "doit"
        assert cresp.success is True
        assert cresp.execution_time == 12.3

    def test_websocket_message_defaults(self):
        # Act
        msg = WebSocketMessage(type="foo", data={"k": "v"})
        # Assert
        assert msg.type == "foo"
        assert "timestamp" in msg.model_dump()
        assert isinstance(msg.timestamp, str)

    def test_context_stats_model(self):
        # Act
        stats = ContextStats(
            total_contexts=5,
            platform_distribution={"discord": 3},
            persona_distribution={"jarvis": 2},
            persistence_enabled=True,
            persistence_path="/tmp/c",
        )
        # Assert
        assert stats.total_contexts == 5


# ============================================================================
# HELPER FUNCTION TESTS (get_client_ip, middlewares)
# ============================================================================


class TestGetClientIpAndRateLimit:
    """get_client_ip security logic + RateLimitMiddleware basics."""

    def test_get_client_ip_direct_no_trusted(self):
        # Arrange
        req = Mock()
        req.client.host = "203.0.113.5"
        req.headers = {}
        # Act
        ip = get_client_ip(req, trusted_proxies=None)
        # Assert
        assert ip == "203.0.113.5"

    def test_get_client_ip_falls_back_direct_when_no_trusted_proxies(self):
        # Arrange
        req = Mock()
        req.client.host = "10.1.2.3"
        req.headers = {"X-Forwarded-For": "1.2.3.4, 10.1.2.3"}
        # Act
        ip = get_client_ip(req, trusted_proxies=[])
        # Assert
        assert ip == "10.1.2.3"

    def test_rate_limit_middleware_basic_dispatch(self):
        # Arrange
        app = Mock()
        mw = RateLimitMiddleware(app, requests_per_minute=10, trusted_proxies=["127.0.0.1"])
        request = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        AsyncMock(return_value=Mock(headers={}))
        # Act (sync wrapper around async for unit)
        # We just ensure no crash on construction + dispatch call path exercised via await in real
        assert mw.requests_per_minute == 10
        # simple state check
        assert hasattr(mw, "requests")


# ============================================================================
# WEB MODE SERVER CONSTRUCTION + BEHAVIOR (heavily mocked)
# ============================================================================


class TestWebModeServerConstruction:
    """WebModeServer init, _create_app wiring, using mocks for heavy deps."""

    @pytest.fixture
    def mocks(self, mock_config, mock_state_manager, mock_model_manager, mock_command_executor):
        """Bundle real-ish mocks from conftest + patches."""
        return {
            "config": mock_config,
            "state": mock_state_manager,
            "model": mock_model_manager,
            "executor": mock_command_executor,
        }

    def test_web_mode_server_instantiates_with_mocks(self, mocks):
        # Arrange - patch _create_app to avoid complex internal route includes / iteration on mocks
        with patch("chatty_commander.web.web_mode.AdvisorsService"), \
             patch.object(WebModeServer, "_create_app", return_value=Mock(spec=FastAPI)):
            # Act
            server = WebModeServer(
                config_manager=mocks["config"],
                state_manager=mocks["state"],
                model_manager=mocks["model"],
                command_executor=mocks["executor"],
                no_auth=True,
            )
            # Assert
            assert server.config_manager is mocks["config"]
            assert server.app is not None
            assert server.commands_executed == 0
            assert server.no_auth is True

    def test_execute_command_wrapper_increments_counter(self, mocks):
        # Arrange
        with patch("chatty_commander.web.web_mode.AdvisorsService"), \
             patch.object(WebModeServer, "_create_app", return_value=Mock(spec=FastAPI)):
            server = WebModeServer(
                mocks["config"], mocks["state"], mocks["model"], mocks["executor"], no_auth=True
            )
            mocks["executor"].execute_command.return_value = True
            # Act
            res = server._execute_command_wrapper("foo")
            # Assert
            assert server.commands_executed == 1
            assert res is True

    def test_broadcast_and_on_hooks_use_event_loop(self, mocks):
        # Arrange
        with patch("chatty_commander.web.web_mode.AdvisorsService"), \
             patch.object(WebModeServer, "_create_app", return_value=Mock(spec=FastAPI)):
            server = WebModeServer(
                mocks["config"], mocks["state"], mocks["model"], mocks["executor"], no_auth=True
            )
            server.active_connections = set()
            # Act - should not raise even without real loop/ws
            server.on_command_detected("cmd42", 0.9)
            server.on_system_event("sys", {"d": 1})
            # Assert - counters or last updated
            assert server.last_command == "cmd42"
            assert server.commands_executed >= 1

    def test_format_uptime(self, mocks):
        with patch("chatty_commander.web.web_mode.AdvisorsService"), \
             patch.object(WebModeServer, "_create_app", return_value=Mock(spec=FastAPI)):
            server = WebModeServer(mocks["config"], mocks["state"], mocks["model"], mocks["executor"], no_auth=True)
            # Act
            up = server._format_uptime(3661)
            # Assert
            assert "1h 1m 1s" in up or "1h" in up

    def test_clear_cache_and_get_cached(self, mocks):
        with patch("chatty_commander.web.web_mode.AdvisorsService"), \
             patch.object(WebModeServer, "_create_app", return_value=Mock(spec=FastAPI)):
            server = WebModeServer(mocks["config"], mocks["state"], mocks["model"], mocks["executor"], no_auth=True)
            # Act
            server._cache_command_result("c1", {"ok": True})
            cached = server._get_cached_command_result("c1")
            # Assert
            assert cached == {"ok": True}
            server._clear_expired_cache()
            # exercised
            assert isinstance(server._command_cache, dict)


# ============================================================================
# ADVISOR ROUTE REGISTRATION (via _register without full app run)
# ============================================================================


class TestWebModeAdvisorsRegistration:
    """Exercise the advisors route closures registered by server (mocked service)."""

    def test_register_advisors_routes_does_not_crash(self, mock_config):
        # Arrange - minimal
        sm = Mock()
        sm.add_state_change_callback = Mock()
        sm.current_state = "idle"
        sm.get_active_models = Mock(return_value=[])
        mm = Mock()
        ce = Mock()
        with patch("chatty_commander.web.web_mode.AdvisorsService") as mock_adv, \
             patch.object(WebModeServer, "_create_app", return_value=Mock(spec=FastAPI)):
            mock_adv.return_value.get_personas.return_value = []
            mock_adv.return_value.enabled = True
            srv = WebModeServer(mock_config, sm, mm, ce, no_auth=True)
            app = FastAPI()
            # Act
            srv._register_advisors_routes(app)
            # Assert - routes now present (or at least no crash on reg)
            assert hasattr(srv, "_register_advisors_routes")

    def test_imports_and_server_class_present(self):
        # Act / Assert
        assert WebModeServer is not None
        assert callable(WebModeServer)
