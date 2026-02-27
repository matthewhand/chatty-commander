"""Tests for the command authoring API endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_generate_command_endpoint_exists():
    """Test that the endpoint exists and accepts requests."""
    # Import the router directly to create a minimal app
    from fastapi import FastAPI
    from chatty_commander.web.routes.command_authoring import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.post(
        "/api/v1/commands/generate",
        json={"description": "open a terminal"},
    )

    # Endpoint exists and processes requests (may return 503 if LLM unavailable,
    # 422 if LLM returns invalid data, or 200 on success)
    assert response.status_code in (200, 422, 503)
    assert response.status_code != 404  # Endpoint must exist


def test_generate_command_endpoint_validates_request():
    """Test that the endpoint validates the request body."""
    from fastapi import FastAPI
    from chatty_commander.web.routes.command_authoring import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    # Empty description should fail validation
    response = client.post(
        "/api/v1/commands/generate",
        json={"description": ""},
    )

    assert response.status_code == 422


def test_generate_command_endpoint_accepts_valid_request():
    """Test that the endpoint accepts a valid request."""
    from fastapi import FastAPI
    from chatty_commander.web.routes.command_authoring import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.post(
        "/api/v1/commands/generate",
        json={"description": "open a terminal window"},
    )

    # Endpoint accepts valid request and returns appropriate status
    # 200 = success with valid LLM response
    # 422 = LLM returned unparsable data
    # 503 = LLM service unavailable
    assert response.status_code in (200, 422, 503)


@pytest.fixture
def client_with_router():
    """Create a test client with the command authoring router."""
    from fastapi import FastAPI
    from chatty_commander.web.routes.command_authoring import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_endpoint_exists_and_has_openapi_schema(client_with_router):
    """Test that the endpoint is documented in OpenAPI schema."""
    response = client_with_router.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    paths = schema.get("paths", {})

    # Check that our endpoint is documented
    assert "/api/v1/commands/generate" in paths
    assert "post" in paths["/api/v1/commands/generate"]
