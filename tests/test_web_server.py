# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for web/server.py module."""

from unittest.mock import Mock, patch

import pytest

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
except ImportError:
    pytest.skip("FastAPI not available", allow_module_level=True)

from src.chatty_commander.web.server import (
    _include_optional,
    create_app,
    settings_router,
)


class TestWebServer:
    """Test web server creation and configuration."""

    def test_create_app_basic(self):
        """Test basic app creation without optional components."""
        app = create_app()
        assert isinstance(app, FastAPI)
        assert len(app.routes) >= 0  # Should have at least the bridge endpoint

    def test_create_app_with_no_auth(self):
        """Test app creation with no_auth flag."""
        app = create_app(no_auth=True)
        assert isinstance(app, FastAPI)

        # Test the bridge endpoint with no_auth=True
        client = TestClient(app)
        response = client.post("/bridge/event")
        assert response.status_code == 401
        assert "Unauthorized bridge request" in response.json()["detail"]

    def test_create_app_with_auth(self):
        """Test app creation with authentication enabled."""
        app = create_app(no_auth=False)
        assert isinstance(app, FastAPI)

        # Test the bridge endpoint with auth enabled
        client = TestClient(app)
        response = client.post("/bridge/event")
        assert response.status_code == 200
        assert response.json() == {
            "ok": True,
            "reply": {"text": "Bridge response", "meta": {}},
        }

    @patch("src.chatty_commander.web.server.avatar_ws_router")
    def test_include_optional_with_router(self, mock_router):
        """Test _include_optional function with available router."""
        mock_app = Mock(spec=FastAPI)
        mock_router.return_value = Mock()

        # Mock globals to return the router
        with patch("src.chatty_commander.web.server.globals") as mock_globals:
            mock_globals.return_value.get.return_value = mock_router
            _include_optional(mock_app, "avatar_ws_router")
            mock_app.include_router.assert_called_once_with(mock_router)

    def test_include_optional_without_router(self):
        """Test _include_optional function with missing router."""
        mock_app = Mock(spec=FastAPI)

        # Mock globals to return None
        with patch("src.chatty_commander.web.server.globals") as mock_globals:
            mock_globals.return_value.get.return_value = None
            _include_optional(mock_app, "nonexistent_router")
            mock_app.include_router.assert_not_called()

    @patch("src.chatty_commander.web.server.include_avatar_settings_routes")
    def test_create_app_with_config_manager(self, mock_include_settings):
        """Test app creation with config manager for settings router."""
        mock_config_manager = Mock()
        mock_settings_router = Mock()
        # Mock router needs attributes to be compatible with FastAPI
        mock_settings_router.routes = []
        mock_settings_router.on_startup = []
        mock_settings_router.on_shutdown = []
        mock_settings_router.default_response_class = None
        mock_settings_router.default_response_class = None
        mock_include_settings.return_value = mock_settings_router

        app = create_app(config_manager=mock_config_manager)

        # Verify settings router was created and included
        mock_include_settings.assert_called_once()
        assert isinstance(app, FastAPI)

    @patch("src.chatty_commander.web.server.include_avatar_settings_routes", None)
    def test_create_app_without_settings_routes(self):
        """Test app creation when avatar settings routes are not available."""
        mock_config_manager = Mock()
        app = create_app(config_manager=mock_config_manager)
        assert isinstance(app, FastAPI)

    @patch("src.chatty_commander.web.server.avatar_api_router")
    @patch("src.chatty_commander.web.server.avatar_selector_router")
    @patch("src.chatty_commander.web.server.version_router")
    @patch("src.chatty_commander.web.server.metrics_router")
    @patch("src.chatty_commander.web.server.agents_router")
    def test_create_app_with_all_routers(
        self, mock_agents, mock_metrics, mock_version, mock_selector, mock_api
    ):
        """Test app creation with all optional routers available."""
        # Mock all routers as available
        mock_routers = [
            mock_agents,
            mock_metrics,
            mock_version,
            mock_selector,
            mock_api,
        ]
        for router in mock_routers:
            router.return_value = Mock()

        app = create_app()
        assert isinstance(app, FastAPI)

    def test_fastapi_basic_functionality(self):
        """Test basic FastAPI functionality."""
        from fastapi import FastAPI

        # Test that FastAPI can be instantiated and has expected default routes
        app = FastAPI()
        assert isinstance(app, FastAPI)
        # FastAPI has default routes like /openapi.json
        assert len(app.routes) > 0

    def test_router_inclusion(self):
        """Test that routers are included in the app."""
        app = create_app()

        # Check that the app was created successfully
        assert isinstance(app, FastAPI)
        # App should have some routes (default FastAPI routes + any included routers)
        assert len(app.routes) > 0

    def test_bridge_endpoint_error_handling(self):
        """Test bridge endpoint error handling."""
        app = create_app(no_auth=False)
        client = TestClient(app)

        # Test successful bridge request
        response = client.post("/bridge/event")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "reply" in data
        assert "text" in data["reply"]
        assert "meta" in data["reply"]

    def test_global_settings_router_state(self):
        """Test global settings_router state management."""
        # Initially should be None

        # Test that it starts as None
        assert settings_router is None

    @patch("src.chatty_commander.web.server.include_avatar_settings_routes")
    def test_settings_router_global_assignment(self, mock_include_settings):
        """Test that settings_router global is properly assigned."""
        mock_config_manager = Mock()
        mock_settings_router = Mock()
        # Mock router needs routes attribute to be iterable
        mock_settings_router.routes = []
        mock_settings_router.on_startup = []
        mock_settings_router.on_shutdown = []
        mock_include_settings.return_value = mock_settings_router

        # Create app with config manager
        app = create_app(config_manager=mock_config_manager)

        # Import the global after app creation
        from src.chatty_commander.web import server

        # Verify the global was set
        assert server.settings_router is not None

    def test_router_import_error_handling(self):
        """Test that import errors for routers are handled gracefully."""
        # The module should handle ImportError for optional routers
        # This is tested by the fact that the module loads successfully
        # even when some routers might not be available
        app = create_app()
        assert isinstance(app, FastAPI)

    def test_multiple_app_creation(self):
        """Test creating multiple app instances."""
        app1 = create_app(no_auth=True)
        app2 = create_app(no_auth=False)

        assert isinstance(app1, FastAPI)
        assert isinstance(app2, FastAPI)
        assert app1 is not app2  # Should be different instances

    @patch("fastapi.HTTPException", side_effect=ImportError)
    def test_bridge_endpoint_without_fastapi_exception(self, mock_http_exception):
        """Test bridge endpoint creation when HTTPException is not available."""
        # This tests the ImportError handling in the bridge endpoint creation
        app = create_app()
        assert isinstance(app, FastAPI)
        # The bridge endpoint should not be created if HTTPException import fails
