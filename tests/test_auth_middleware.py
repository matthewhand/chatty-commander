from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.middleware.auth import AuthMiddleware


class MockConfigManager:
    def __init__(self, key):
        self.config = {"auth": {"api_key": key}}

def test_auth_middleware_path_traversal():
    """Test that path traversal cannot be used to bypass authentication."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware, config_manager=MockConfigManager("testkey"))

    @app.get("/api/secret")
    def secret():
        return {"secret": "data"}

    client = TestClient(app)

    # Path traversal should not bypass authentication
    response = client.get("/docs/../api/secret")
    assert response.status_code == 401

    # Normal protected request should fail without API key
    response = client.get("/api/secret")
    assert response.status_code == 401

    # Valid API key should work
    response = client.get("/api/secret", headers={"X-API-Key": "testkey"})
    assert response.status_code == 200

def test_auth_middleware_partial_match():
    """Test that partial path matches do not bypass authentication for public endpoints."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware, config_manager=MockConfigManager("testkey"))

    @app.get("/api/secret")
    def secret():
        return {"secret": "data"}

    @app.get("/docs-secret")
    def docs_secret():
        return {"data": "secret docs"}

    client = TestClient(app)

    # Partial match: /docs-secret should NOT be treated as public /docs
    # Since /docs-secret is not an API path, it passes through middleware without auth
    # but the key point is it does NOT match /docs public endpoint
    response = client.get("/docs-secret")
    # This is a non-API path, so it passes through (not 401) but also NOT treated as /docs
    assert response.status_code == 200

    # The important security fix: /docs/../api/secret should require auth
    # This was the vulnerability - path traversal could bypass auth
    response = client.get("/docs/../api/secret")
    assert response.status_code == 401, f"Expected 401 for traversal /docs/../api/secret, got {response.status_code}"

    # Verify /docs itself is public
    @app.get("/docs")
    def docs_page():
        return {"openapi": "docs"}

    response = client.get("/docs")
    assert response.status_code == 200  # public endpoint


def test_auth_middleware_url_encoded_traversal():
    """Test that URL-encoded path traversal attempts are blocked."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware, config_manager=MockConfigManager("testkey"))

    @app.get("/api/secret")
    def secret():
        return {"secret": "data"}

    client = TestClient(app)

    # URL-encoded path traversal should be normalized and blocked
    # %2f = /, so /docs%2f..%2fapi becomes /docs/../api after decoding
    # After normalization this becomes /api which requires auth
    response = client.get("/docs%2f..%2fapi/secret")
    assert response.status_code == 401, f"Expected 401 for URL-encoded traversal, got {response.status_code}"

    # Double encoding should also be handled
    response = client.get("/docs%252f..%252fapi%252fsecret")
    assert response.status_code == 401, f"Expected 401 for double-encoded traversal, got {response.status_code}"


def test_auth_middleware_traversal_patterns():
    """Test various path traversal patterns cannot bypass auth for API endpoints."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware, config_manager=MockConfigManager("testkey"))

    @app.get("/api/secret")
    def secret():
        return {"secret": "data"}

    client = TestClient(app)

    # Various traversal patterns that try to reach /api/secret should require auth
    # The key security fix: these paths should normalize to /api/secret and require auth
    traversal_patterns_to_api = [
        "/../api/secret",
        "/api/../api/secret",
        "/api/./secret",
        "/api//secret",
    ]

    for pattern in traversal_patterns_to_api:
        response = client.get(pattern)
        assert response.status_code == 401, f"Expected 401 for {pattern}, got {response.status_code}"
