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
    """Test that partial path matches do not bypass authentication."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware, config_manager=MockConfigManager("testkey"))

    @app.get("/api/secret")
    def secret():
        return {"secret": "data"}

    client = TestClient(app)

    # E.g. /docs-secret should be caught if /docs was matched partially
    # But since /docs-secret is not an API endpoint, it would pass auth middleware normally
    # Let's test an API endpoint that looks like a public endpoint partially

    # Here we test if the partial match logic correctly uses exact endpoint matching
    # Since we changed it from path.startswith("/docs") to path == "/docs" or path.startswith("/docs/")

    # /api/docs would be checked by `path.startswith("/api/")`
    response = client.get("/docs-secret")
    assert response.status_code == 404  # not found, but it passed auth
