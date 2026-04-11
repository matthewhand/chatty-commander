import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from chatty_commander.web.middleware.auth import AuthMiddleware
from tests.test_auth import MockConfigManager

@pytest.mark.asyncio
async def test_url_double_encoding_bypass():
    app = FastAPI()

    @app.get("/api/secret")
    def secret():
        return {"secret": "data"}

    middleware = AuthMiddleware(app, config_manager=MockConfigManager("testkey"))

    from fastapi import Request
    from fastapi.responses import JSONResponse

    # quadruple encoded "../api/secret"
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/docs/%2525252F%2525252E%2525252E%2525252Fapi%2525252Fsecret",
        "headers": [],
    }

    request = Request(scope)

    async def mock_call_next(req):
        return JSONResponse(status_code=200, content={"status": "bypassed"})

    response = await middleware.dispatch(request, mock_call_next)

    # Should block %252e%252e%252f (double-encoded ..) - returns 401 Unauthorized
    assert response.status_code == 401
