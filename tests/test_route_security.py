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

import pytest
from fastapi.testclient import TestClient

from chatty_commander.web.server import create_app
from chatty_commander.web.middleware.auth import AuthMiddleware
from chatty_commander.app.config import Config


class TestRouteSecurity:
    """Test suite to automatically scan routes for security vulnerabilities."""

    @pytest.fixture
    def app(self):
        """Create a fresh app instance with auth enabled."""
        config = Config()
        config.config = {"auth": {"api_key": "secret-key"}}

        # Pass the config to create_app if supported, or attach middleware manually
        # create_app in server.py doesn't attach middleware by default,
        # so we need to add it here to simulate a secured environment.
        app = create_app(no_auth=False, config_manager=config)

        # Manually add the AuthMiddleware since create_app only returns the bare app
        # with routers but without the middleware stack usually added in web_mode.py
        app.add_middleware(AuthMiddleware, config_manager=config, no_auth=False)

        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)

    def test_all_api_routes_protected(self, app, client):
        """
        Scan all registered routes and ensure that:
        1. API routes (/api/...) are protected (401/403) when accessed without auth.
        2. Public routes (/docs, /openapi.json) remain accessible.
        """
        public_endpoints = {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/",
            "/assets",  # Static files
            "/health",
            "/metrics",
        }

        # Collect all GET routes
        routes_to_test = []
        for route in app.routes:
            if hasattr(route, "methods") and "GET" in route.methods:
                path = route.path
                # Skip parameterized paths for simple scanning (complex to mock automatically)
                if "{" not in path:
                    routes_to_test.append(path)

        for path in routes_to_test:
            response = client.get(path)

            if path in public_endpoints or path.startswith("/assets/"):
                # Public endpoints should be accessible
                assert response.status_code != 401, f"Public endpoint {path} was blocked"
            elif path.startswith("/api/"):
                # API endpoints MUST be protected
                assert response.status_code in [401, 403], \
                    f"API endpoint {path} is accessible without authentication! Status: {response.status_code}"

    def test_protected_routes_reject_invalid_key(self, app, client):
        """Ensure protected routes reject invalid API keys."""
        # Pick a sample protected route (must exist)
        # Using /api/v1/version which should be present
        protected_path = "/api/v1/version"

        # Test with invalid key
        response = client.get(protected_path, headers={"X-API-Key": "invalid-key"})
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid or missing API key"}

    def test_options_requests_allowed(self, app, client):
        """Ensure OPTIONS requests (CORS preflight) are always allowed."""
        protected_path = "/api/v1/version"
        response = client.options(protected_path)
        assert response.status_code != 401
