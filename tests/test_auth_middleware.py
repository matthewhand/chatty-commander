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
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.middleware.auth import AuthMiddleware


class MockConfig:
    def __init__(self, auth=None, config=None):
        self.auth = auth
        self.config = config


@pytest.fixture
def mock_config():
    return MockConfig(auth={"api_key": "secret-key"})


@pytest.fixture
def app(mock_config):
    app = FastAPI()

    # Add middleware
    app.add_middleware(AuthMiddleware, config_manager=mock_config, no_auth=False)

    @app.get("/")
    async def root():
        return {"message": "public"}

    @app.get("/api/protected")
    async def protected():
        return {"message": "protected"}

    @app.options("/api/protected")
    async def options_protected():
        return {"message": "options"}

    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_public_endpoint(client):
    """Test public endpoint access without API key."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "public"}


def test_protected_endpoint_no_key(client):
    """Test protected endpoint without API key."""
    response = client.get("/api/protected")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}


def test_protected_endpoint_invalid_key(client):
    """Test protected endpoint with invalid API key."""
    response = client.get("/api/protected", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}


def test_protected_endpoint_valid_key(client):
    """Test protected endpoint with valid API key."""
    response = client.get("/api/protected", headers={"X-API-Key": "secret-key"})
    assert response.status_code == 200
    assert response.json() == {"message": "protected"}


def test_options_request(client):
    """Test OPTIONS request bypasses auth."""
    response = client.options("/api/protected")
    assert response.status_code == 200
    assert response.json() == {"message": "options"}


def test_no_auth_mode():
    """Test no_auth mode bypasses auth."""
    config = MockConfig(auth={"api_key": "secret-key"})
    app = FastAPI()
    app.add_middleware(AuthMiddleware, config_manager=config, no_auth=True)

    @app.get("/api/protected")
    async def protected():
        return {"message": "protected"}

    client = TestClient(app)
    response = client.get("/api/protected")
    assert response.status_code == 200
    assert response.json() == {"message": "protected"}


def test_config_dict_structure():
    """Test config structure with 'config' attribute instead of 'auth' attribute."""
    config = MockConfig(config={"auth": {"api_key": "secret-key"}})
    app = FastAPI()
    app.add_middleware(AuthMiddleware, config_manager=config, no_auth=False)

    @app.get("/api/protected")
    async def protected():
        return {"message": "protected"}

    client = TestClient(app)

    # Fail with no key
    response = client.get("/api/protected")
    assert response.status_code == 401

    # Succeed with key
    response = client.get("/api/protected", headers={"X-API-Key": "secret-key"})
    assert response.status_code == 200


def test_missing_config_allows_request():
    """Test that missing auth config allows requests (open by default if not configured)."""
    # No auth config at all
    config = MockConfig()
    app = FastAPI()
    app.add_middleware(AuthMiddleware, config_manager=config, no_auth=False)

    @app.get("/api/protected")
    async def protected():
        return {"message": "protected"}

    client = TestClient(app)
    response = client.get("/api/protected")
    assert response.status_code == 200
    assert response.json() == {"message": "protected"}


def test_docs_endpoints_public():
    """Test documentation endpoints are public."""
    config = MockConfig(auth={"api_key": "secret-key"})
    app = FastAPI()
    app.add_middleware(AuthMiddleware, config_manager=config, no_auth=False)

    # We don't need real docs endpoints, just matching paths
    @app.get("/docs")
    async def docs():
        return {"message": "docs"}

    @app.get("/openapi.json")
    async def openapi():
        return {"message": "openapi"}

    client = TestClient(app)

    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/openapi.json")
    assert response.status_code == 200
