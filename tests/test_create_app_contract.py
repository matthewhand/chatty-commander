"""Contract tests for create_app() function.

These tests ensure that create_app() maintains its expected interface
and behavior across different configurations and environments.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.web_mode import create_app


class TestCreateAppContract:
    """Contract tests for create_app() function."""

    def test_create_app_returns_fastapi_instance(self):
        """Test that create_app() returns a FastAPI instance."""
        app = create_app()
        assert isinstance(app, FastAPI)

    def test_create_app_has_required_endpoints(self):
        """Test that create_app() provides required fallback endpoints."""
        app = create_app()
        client = TestClient(app)

        # Test status endpoint
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data

        # Test version endpoint
        response = client.get("/api/v1/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data

    def test_create_app_state_endpoints(self):
        """Test that create_app() provides state management endpoints."""
        app = create_app()
        client = TestClient(app)

        # Test GET state endpoint
        response = client.get("/api/v1/state")
        assert response.status_code == 200
        data = response.json()
        assert "current_state" in data

        # Test POST state endpoint
        response = client.post("/api/v1/state", json={"state": "computer"})
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "computer" in data["message"]

    def test_create_app_command_endpoint(self):
        """Test that create_app() provides command execution endpoint."""
        app = create_app()
        client = TestClient(app)

        # Test POST command endpoint
        response = client.post("/api/v1/command", json={"command": "hello"})
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "execution_time" in data
        assert data["success"] is True

    def test_create_app_idempotent(self):
        """Test that create_app() can be called multiple times safely."""
        app1 = create_app()
        app2 = create_app()

        # Both should be FastAPI instances
        assert isinstance(app1, FastAPI)
        assert isinstance(app2, FastAPI)

        # Both should have the same basic structure
        client1 = TestClient(app1)
        client2 = TestClient(app2)

        response1 = client1.get("/api/v1/status")
        response2 = client2.get("/api/v1/status")

        assert response1.status_code == response2.status_code == 200

    def test_create_app_with_optional_routers(self):
        """Test that create_app() handles optional routers gracefully."""
        # This test verifies that the guarded router inclusion works
        # even when optional routers are not available
        app = create_app()

        # Should still create a valid FastAPI app
        assert isinstance(app, FastAPI)

        # Should still have fallback endpoints
        client = TestClient(app)
        response = client.get("/api/v1/status")
        assert response.status_code == 200

    def test_create_app_openapi_schema(self):
        """Test that create_app() generates a valid OpenAPI schema."""
        app = create_app()

        # Should have OpenAPI schema
        assert hasattr(app, 'openapi')
        schema = app.openapi()
        assert isinstance(schema, dict)
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

    def test_create_app_cors_configuration(self):
        """Test that create_app() has proper CORS configuration."""
        app = create_app()
        client = TestClient(app)

        # Test CORS headers on OPTIONS request
        response = client.options("/api/v1/status")
        # Should not fail (may return 405 Method Not Allowed, but shouldn't crash)
        assert response.status_code in [200, 405]

    def test_create_app_error_handling(self):
        """Test that create_app() has proper error handling."""
        app = create_app()
        client = TestClient(app)

        # Test 404 for non-existent endpoint
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

        # Should return JSON error response
        data = response.json()
        assert "detail" in data

    def test_create_app_idempotency(self):
        """Test that create_app() executed twice does not increase route count."""
        app1 = create_app()
        initial_route_count = len(app1.routes)

        app2 = create_app()
        second_route_count = len(app2.routes)

        # Both apps should have the same number of routes
        assert initial_route_count == second_route_count, (
            f"Route count changed: {initial_route_count} -> {second_route_count}. "
            "create_app() should be idempotent."
        )
