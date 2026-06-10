# MIT License
#
# Tests for CORS restriction in --no-auth mode (security backlog, ex PR #624).
#
# no_auth=True disables authentication entirely, so the CORS allowlist must
# NOT be a wildcard: with allow_origins=["*"] any website the user visits
# could drive the unauthenticated API from their browser and read responses
# (drive-by attack). The fix pins no-auth CORS to localhost origins by
# default, overridable via CHATTY_CORS_ORIGINS.

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.web_mode import WebModeServer


def _build_server(no_auth: bool) -> WebModeServer:
    config = Config()
    state_manager = StateManager(config)
    model_manager = ModelManager(config)
    command_executor = CommandExecutor(config, model_manager, state_manager)
    return WebModeServer(
        config, state_manager, model_manager, command_executor, no_auth=no_auth
    )


def _cors_kwargs(app) -> dict:
    middleware = next(m for m in app.user_middleware if m.cls is CORSMiddleware)
    return middleware.kwargs


class TestNoAuthCorsRestriction:
    def test_no_auth_does_not_use_wildcard_origin(self, monkeypatch):
        """The vulnerability shape: no_auth must never yield allow_origins=['*']."""
        monkeypatch.delenv("CHATTY_CORS_ORIGINS", raising=False)
        server = _build_server(no_auth=True)
        kwargs = _cors_kwargs(server.app)
        assert "*" not in kwargs["allow_origins"]

    def test_no_auth_defaults_to_localhost_origins_only(self, monkeypatch):
        monkeypatch.delenv("CHATTY_CORS_ORIGINS", raising=False)
        server = _build_server(no_auth=True)
        kwargs = _cors_kwargs(server.app)
        assert kwargs["allow_origins"], "expected a non-empty localhost allowlist"
        for origin in kwargs["allow_origins"]:
            assert origin.startswith(("http://localhost", "http://127.0.0.1")), origin

    def test_auth_mode_keeps_default_localhost_3000(self, monkeypatch):
        """No behavior change for the authenticated factory path."""
        monkeypatch.delenv("CHATTY_CORS_ORIGINS", raising=False)
        server = _build_server(no_auth=False)
        kwargs = _cors_kwargs(server.app)
        assert kwargs["allow_origins"] == ["http://localhost:3000"]

    def test_env_override_is_honored_in_no_auth_mode(self, monkeypatch):
        monkeypatch.setenv(
            "CHATTY_CORS_ORIGINS",
            "https://chatty.example.com, http://localhost:9999",
        )
        server = _build_server(no_auth=True)
        kwargs = _cors_kwargs(server.app)
        assert kwargs["allow_origins"] == [
            "https://chatty.example.com",
            "http://localhost:9999",
        ]

    def test_env_override_is_honored_in_auth_mode(self, monkeypatch):
        monkeypatch.setenv("CHATTY_CORS_ORIGINS", "https://ui.internal.example")
        server = _build_server(no_auth=False)
        kwargs = _cors_kwargs(server.app)
        assert kwargs["allow_origins"] == ["https://ui.internal.example"]

    def test_env_wildcard_override_disables_credentials(self, monkeypatch):
        """If someone opts back into '*' via env, credentials must stay off (RFC 6454)."""
        monkeypatch.setenv("CHATTY_CORS_ORIGINS", "*")
        server = _build_server(no_auth=True)
        kwargs = _cors_kwargs(server.app)
        assert kwargs["allow_origins"] == ["*"]
        assert kwargs["allow_credentials"] is False


class TestNoAuthCorsBehavior:
    """End-to-end: the browser-visible CORS headers in no_auth mode."""

    def test_evil_origin_is_not_allowed(self, monkeypatch):
        monkeypatch.delenv("CHATTY_CORS_ORIGINS", raising=False)
        server = _build_server(no_auth=True)
        client = TestClient(server.app)
        resp = client.options(
            "/api/v1/status",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") != "https://evil.example"
        assert resp.headers.get("access-control-allow-origin") != "*"

    def test_localhost_origin_is_allowed(self, monkeypatch):
        monkeypatch.delenv("CHATTY_CORS_ORIGINS", raising=False)
        server = _build_server(no_auth=True)
        client = TestClient(server.app)
        resp = client.options(
            "/api/v1/status",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        assert (
            resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
        )


class TestCreateAppCors:
    """server.create_app adds no CORS middleware: same-origin browser default."""

    def test_create_app_has_no_cors_middleware(self):
        from chatty_commander.web.server import create_app

        app = create_app(no_auth=True)
        assert not any(m.cls is CORSMiddleware for m in app.user_middleware)

    def test_create_app_emits_no_cors_headers_for_cross_origin(self):
        from chatty_commander.web.server import create_app

        app = create_app(no_auth=True)
        client = TestClient(app)
        resp = client.get("/api/v1/status", headers={"Origin": "https://evil.example"})
        assert "access-control-allow-origin" not in resp.headers
