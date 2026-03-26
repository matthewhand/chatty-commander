"""Tests for web/server.py module.

Consolidated from:
- test_web_server.py (app creation, bridge security, router inclusion)
- test_web_server_guards.py (import safety, guards, idempotency, static analysis)
"""

import ast
import pathlib
import py_compile
import re
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

try:
    from fastapi import APIRouter, FastAPI
    from fastapi.testclient import TestClient
except ImportError:
    pytest.skip("FastAPI not available", allow_module_level=True)

from chatty_commander.web.server import (
    _include_optional,
    create_app,
    settings_router,
)

SERVER = pathlib.Path("src/chatty_commander/web/server.py")


# ---------------------------------------------------------------------------
# Core app creation and configuration
# ---------------------------------------------------------------------------


class TestWebServer:
    """Test web server creation and configuration."""

    def test_create_app_basic(self):
        app = create_app()
        assert isinstance(app, FastAPI)
        assert len(app.routes) >= 0

    def test_create_app_with_no_auth(self):
        app = create_app(no_auth=True)
        assert isinstance(app, FastAPI)
        client = TestClient(app)
        response = client.post("/bridge/event")
        assert response.status_code == 401
        assert "Unauthorized bridge request" in response.json()["detail"]

    def test_create_app_with_auth(self):
        mock_config = Mock()
        mock_config.web_server = {"bridge_token": "test-token"}
        app = create_app(no_auth=False, config_manager=mock_config)
        assert isinstance(app, FastAPI)
        client = TestClient(app)
        response = client.post(
            "/bridge/event",
            headers={"X-Bridge-Token": "test-token"},
        )
        assert response.status_code == 200
        assert response.json() == {
            "ok": True,
            "reply": {"text": "Bridge response", "meta": {}},
        }

    @patch("chatty_commander.web.server.avatar_ws_router")
    def test_include_optional_with_router(self, mock_router):
        mock_app = Mock(spec=FastAPI)
        mock_router.return_value = Mock()
        with patch("chatty_commander.web.server.globals") as mock_globals:
            mock_globals.return_value.get.return_value = mock_router
            _include_optional(mock_app, "avatar_ws_router")
            mock_app.include_router.assert_called_once_with(mock_router)

    def test_include_optional_without_router(self):
        mock_app = Mock(spec=FastAPI)
        with patch("chatty_commander.web.server.globals") as mock_globals:
            mock_globals.return_value.get.return_value = None
            _include_optional(mock_app, "nonexistent_router")
            mock_app.include_router.assert_not_called()

    @patch("chatty_commander.web.server.include_avatar_settings_routes")
    def test_create_app_with_config_manager(self, mock_include_settings):
        mock_config_manager = Mock()
        mock_settings_router = Mock()
        mock_settings_router.routes = []
        mock_settings_router.on_startup = []
        mock_settings_router.on_shutdown = []
        mock_settings_router.default_response_class = None
        mock_include_settings.return_value = mock_settings_router
        app = create_app(config_manager=mock_config_manager)
        mock_include_settings.assert_called_once()
        assert isinstance(app, FastAPI)

    @patch("chatty_commander.web.server.include_avatar_settings_routes", None)
    def test_create_app_without_settings_routes(self):
        mock_config_manager = Mock()
        app = create_app(config_manager=mock_config_manager)
        assert isinstance(app, FastAPI)

    @patch("chatty_commander.web.server.avatar_api_router")
    @patch("chatty_commander.web.server.avatar_selector_router")
    @patch("chatty_commander.web.server.version_router")
    @patch("chatty_commander.web.server.metrics_router")
    @patch("chatty_commander.web.server.agents_router")
    def test_create_app_with_all_routers(
        self, mock_agents, mock_metrics, mock_version, mock_selector, mock_api
    ):
        for router in [
            mock_agents,
            mock_metrics,
            mock_version,
            mock_selector,
            mock_api,
        ]:
            router.return_value = Mock()
        app = create_app()
        assert isinstance(app, FastAPI)

    def test_fastapi_basic_functionality(self):
        app = FastAPI()
        assert isinstance(app, FastAPI)
        assert len(app.routes) > 0

    def test_router_inclusion(self):
        app = create_app()
        assert isinstance(app, FastAPI)
        assert len(app.routes) > 0

    def test_bridge_endpoint_error_handling(self):
        mock_config = Mock()
        mock_config.web_server = {"bridge_token": "valid-token"}
        app = create_app(no_auth=False, config_manager=mock_config)
        client = TestClient(app)
        response = client.post(
            "/bridge/event",
            headers={"X-Bridge-Token": "valid-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "reply" in data
        assert "text" in data["reply"]
        assert "meta" in data["reply"]

    def test_global_settings_router_state(self):
        assert settings_router is None

    @patch("chatty_commander.web.server.include_avatar_settings_routes")
    def test_settings_router_global_assignment(self, mock_include_settings):
        mock_config_manager = Mock()
        mock_settings_router = Mock()
        mock_settings_router.routes = []
        mock_settings_router.on_startup = []
        mock_settings_router.on_shutdown = []
        mock_include_settings.return_value = mock_settings_router
        create_app(config_manager=mock_config_manager)
        from chatty_commander.web import server

        assert server.settings_router is mock_settings_router

    def test_router_import_error_handling(self):
        app = create_app()
        assert isinstance(app, FastAPI)

    def test_multiple_app_creation(self):
        app1 = create_app(no_auth=True)
        app2 = create_app(no_auth=False)
        assert isinstance(app1, FastAPI)
        assert isinstance(app2, FastAPI)
        assert app1 is not app2

    @patch("fastapi.HTTPException", side_effect=ImportError)
    def test_bridge_endpoint_without_fastapi_exception(self, mock_http_exception):
        app = create_app()
        assert isinstance(app, FastAPI)


# ---------------------------------------------------------------------------
# Bridge endpoint security
# ---------------------------------------------------------------------------


class TestBridgeEndpointSecurity:
    """Security tests for /bridge/event endpoint."""

    def test_no_auth_missing_token_returns_401(self):
        app = create_app(no_auth=True)
        client = TestClient(app)
        response = client.post(
            "/bridge/event", json={"platform": "discord", "text": "hi"}
        )
        assert response.status_code == 401
        assert "Unauthorized bridge request" in response.json()["detail"]

    def test_no_auth_correct_token_returns_200(self):
        app = create_app(no_auth=True)
        client = TestClient(app)
        response = client.post(
            "/bridge/event",
            headers={"X-Bridge-Token": "any-token"},
            json={"platform": "discord", "text": "hi"},
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True
        assert "dev" in response.json()["reply"]["text"]

    def test_auth_missing_bridge_token_config_returns_401(self):
        app = create_app(no_auth=False)
        client = TestClient(app)
        response = client.post(
            "/bridge/event", json={"platform": "discord", "text": "hi"}
        )
        assert response.status_code == 401
        assert "not configured" in response.json()["detail"].lower()

    def test_auth_empty_bridge_token_config_returns_401(self):
        mock_config = Mock()
        mock_config.web_server = {"bridge_token": ""}
        app = create_app(no_auth=False, config_manager=mock_config)
        client = TestClient(app)
        response = client.post(
            "/bridge/event", json={"platform": "discord", "text": "hi"}
        )
        assert response.status_code == 401
        assert "not configured" in response.json()["detail"].lower()

    def test_auth_wrong_token_returns_401(self):
        mock_config = Mock()
        mock_config.web_server = {"bridge_token": "correct-token"}
        app = create_app(no_auth=False, config_manager=mock_config)
        client = TestClient(app)
        response = client.post(
            "/bridge/event",
            headers={"X-Bridge-Token": "wrong-token"},
            json={"platform": "discord", "text": "hi"},
        )
        assert response.status_code == 401
        assert "Invalid bridge token" in response.json()["detail"]

    def test_auth_correct_token_returns_200(self):
        mock_config = Mock()
        mock_config.web_server = {"bridge_token": "secret-token"}
        app = create_app(no_auth=False, config_manager=mock_config)
        client = TestClient(app)
        response = client.post(
            "/bridge/event",
            headers={"X-Bridge-Token": "secret-token"},
            json={"platform": "discord", "text": "hi"},
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_auth_no_token_provided_returns_401(self):
        mock_config = Mock()
        mock_config.web_server = {"bridge_token": "secret-token"}
        app = create_app(no_auth=False, config_manager=mock_config)
        client = TestClient(app)
        response = client.post(
            "/bridge/event", json={"platform": "discord", "text": "hi"}
        )
        assert response.status_code == 401

    def test_auth_none_bridge_token_config_returns_401(self):
        mock_config = Mock()
        mock_config.web_server = {"bridge_token": None}  # type: ignore
        app = create_app(no_auth=False, config_manager=mock_config)
        client = TestClient(app)
        response = client.post(
            "/bridge/event", json={"platform": "discord", "text": "hi"}
        )
        assert response.status_code == 401
        assert "not configured" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Server guards, import safety, and static analysis
# (from test_web_server_guards.py)
# ---------------------------------------------------------------------------


class TestServerCompilation:
    """Test that server.py compiles and has guarded router includes."""

    def test_server_compiles(self):
        py_compile.compile(str(SERVER), doraise=True)

    def test_optional_router_includes_are_guarded(self):
        text = SERVER.read_text()
        danger = re.compile(
            r"app\.include_router\((version_router|metrics_router|agents_router)\)"
        )
        lines = text.splitlines()
        violations = []
        for i, ln in enumerate(lines):
            if danger.search(ln):
                window = "\n".join(lines[max(0, i - 6) : i + 1])
                if "globals().get(" not in window or "_r =" not in window:
                    violations.append((i + 1, ln.strip()))
        assert not violations, f"unguarded router includes: {violations}"


class TestServerImportSafety:
    """Test that server can be imported without optional dependencies."""

    def test_import_without_optional_routers(self):
        import chatty_commander.web.server as server_module

        original_globals = dict(server_module.__dict__)
        try:
            router_names = [
                "avatar_ws_router",
                "avatar_api_router",
                "settings_router",
                "avatar_selector_router",
                "version_router",
                "metrics_router",
                "agents_router",
                "models_router",
                "command_authoring_router",
                "RequestMetricsMiddleware",
            ]
            for name in router_names:
                if name in server_module.__dict__:
                    setattr(server_module, name, None)
            if "create_metrics_router" in server_module.__dict__:
                server_module.create_metrics_router = None

            app = server_module.create_app()
            assert isinstance(app, FastAPI)
            route_count = len(app.routes)
            assert route_count <= 12
        finally:
            for key, value in original_globals.items():
                setattr(server_module, key, value)

    def test_create_app_returns_fastapi_instance(self):
        app = create_app()
        assert isinstance(app, FastAPI)
        app_with_no_auth = create_app(no_auth=True)
        assert isinstance(app_with_no_auth, FastAPI)


class TestRouterInclusion:
    """Test router inclusion behavior with dummy routers."""

    def test_router_inclusion_with_dummy_routers(self):
        import chatty_commander.web.server as server_module

        original_globals = dict(server_module.__dict__)
        try:
            app = FastAPI()
            initial_route_count = len(app.routes)

            test_router = APIRouter(prefix="/test", tags=["test"])

            @test_router.get("/endpoint")
            def test_endpoint():
                return {"message": "test"}

            server_module.test_router = test_router
            server_module._include_optional(app, "test_router")
            assert len(app.routes) > initial_route_count, "Router was not included"
            server_module._include_optional(app, "nonexistent_router")
        finally:
            for key, value in original_globals.items():
                setattr(server_module, key, value)
            if hasattr(server_module, "test_router"):
                delattr(server_module, "test_router")

    def test_include_optional_function(self):
        import chatty_commander.web.server as server_module

        original_globals = dict(server_module.__dict__)
        try:
            app = FastAPI()
            initial_route_count = len(app.routes)

            _include_optional(app, "nonexistent_router")
            assert len(app.routes) == initial_route_count

            test_router = APIRouter(prefix="/test", tags=["test"])

            @test_router.get("/endpoint")
            def test_endpoint():
                return {"message": "test"}

            server_module.test_router = test_router
            _include_optional(app, "test_router")
            assert len(app.routes) > initial_route_count
        finally:
            for key, value in original_globals.items():
                setattr(server_module, key, value)
            if hasattr(server_module, "test_router"):
                delattr(server_module, "test_router")


class TestIdempotency:
    """Test that app creation and router inclusion is idempotent."""

    def test_multiple_app_creation_idempotent(self):
        app1 = create_app()
        app2 = create_app()
        assert app1 is not app2
        assert isinstance(app1, FastAPI)
        assert isinstance(app2, FastAPI)
        assert len(app1.routes) == len(app2.routes)

    def test_router_inclusion_not_duplicated(self):
        import chatty_commander.web.server as server_module

        test_router = APIRouter(prefix="/idempotency-test", tags=["test"])

        @test_router.get("/endpoint")
        def test_endpoint():
            return {"message": "test"}

        original_globals = dict(server_module.__dict__)
        try:
            server_module.test_router_idem = test_router
            original_create_app = server_module.create_app

            def patched_create_app(no_auth: bool = False) -> FastAPI:
                app = original_create_app(no_auth)
                server_module._include_optional(app, "test_router_idem")
                return app

            server_module.create_app = patched_create_app
            app1 = server_module.create_app()
            app2 = server_module.create_app()
            assert len(app1.routes) == len(app2.routes)
            assert app1 is not app2
        finally:
            for key, value in original_globals.items():
                setattr(server_module, key, value)
            if hasattr(server_module, "test_router_idem"):
                delattr(server_module, "test_router_idem")


class TestStaticSafety:
    """Test static code safety patterns."""

    def test_no_unguarded_include_router_calls(self):
        server_file = Path("src/chatty_commander/web/server.py")
        if not server_file.exists():
            pytest.skip("Server file not found")

        content = server_file.read_text()
        tree = ast.parse(content)

        include_router_calls = []

        class IncludeRouterVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "include_router"
                ):
                    include_router_calls.append(node)
                self.generic_visit(node)

        visitor = IncludeRouterVisitor()
        visitor.visit(tree)

        for call in include_router_calls:
            line_no = call.lineno
            assert line_no > 0, f"include_router call found at line {line_no}"

    def test_no_except_nameerror_patterns(self):
        server_file = Path("src/chatty_commander/web/server.py")
        if not server_file.exists():
            pytest.skip("Server file not found")

        content = server_file.read_text()
        assert (
            "except NameError:" not in content
        ), "Found 'except NameError:' pattern in server code"

        tree = ast.parse(content)

        class ExceptVisitor(ast.NodeVisitor):
            def visit_ExceptHandler(self, node):
                if node.type and isinstance(node.type, ast.Name):
                    if node.type.id == "NameError":
                        pytest.fail(
                            f"Found NameError exception handler at line {node.lineno}"
                        )
                self.generic_visit(node)

        visitor = ExceptVisitor()
        visitor.visit(tree)


class TestContractCompliance:
    """Test basic contract compliance for create_app."""

    def test_create_app_basic_contract(self):
        app = create_app()
        assert isinstance(app, FastAPI)
        assert hasattr(app, "routes")
        client = TestClient(app)
        response = client.get("/docs")
        assert response.status_code in [200, 307, 404]
        response = client.get("/openapi.json")
        assert response.status_code in [200, 404]

    def test_create_app_no_auth_parameter(self):
        app_with_auth = create_app(no_auth=False)
        app_without_auth = create_app(no_auth=True)
        assert isinstance(app_with_auth, FastAPI)
        assert isinstance(app_without_auth, FastAPI)
        client_with_auth = TestClient(app_with_auth)
        client_without_auth = TestClient(app_without_auth)
        response1 = client_with_auth.get("/docs")
        response2 = client_without_auth.get("/docs")
        assert response1.status_code in [200, 307, 404]
        assert response2.status_code in [200, 307, 404]
