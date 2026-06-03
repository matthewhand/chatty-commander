from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from chatty_commander.web.middleware.auth import AuthMiddleware


class MockConfigManager:
    def __init__(self, key):
        self.config = {"auth": {"api_key": key}}

def test_auth_middleware_raises_http_exception():
    """Test that AuthMiddleware raises HTTPException instead of returning JSONResponse."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware, config_manager=MockConfigManager("testkey"))

    @app.get("/api/test")
    def test_endpoint():
        return {"status": "ok"}

    # We use a custom exception handler to verify it's an HTTPException being handled by FastAPI
    # although TestClient will normally catch the final response.
    # The key is that it *reaches* FastAPI's exception handling layer.

    client = TestClient(app)

    # Request without API key should fail with 401
    response = client.get("/api/test")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}

def test_auth_middleware_with_custom_handler():
    """Verify that a custom HTTPException handler can catch the middleware's exception."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware, config_manager=MockConfigManager("testkey"))

    @app.exception_handler(HTTPException)
    async def custom_handler(request: Request, exc: HTTPException):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=exc.status_code,
            content={"custom": True, "detail": exc.detail}
        )

    @app.get("/api/test")
    def test_endpoint():
        return {"status": "ok"}

    client = TestClient(app)

    response = client.get("/api/test")
    assert response.status_code == 401
    assert response.json()["custom"] is True
    assert response.json()["detail"] == "Invalid or missing API key"
