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

"""Tests for standardized API error responses (ROADMAP: production hardening).

Asserts the consistent ``{error, code, details, request_id}`` JSON shape on
``/api/*`` paths for 404 (HTTPException), 422 (validation, details preserved),
forced 500 (generic message, no internals leaked, logged server-side), and
that normal routes plus non-API/auth-middleware error bodies are unchanged.
"""

import logging

import pytest

try:
    from fastapi import HTTPException
    from fastapi.testclient import TestClient
    from pydantic import BaseModel
except ImportError:
    pytest.skip("FastAPI not available", allow_module_level=True)

from chatty_commander.web.server import create_app

ERROR_KEYS = {"error", "code", "details", "request_id"}


class _Payload(BaseModel):
    name: str
    count: int


def _make_app():
    app = create_app(no_auth=True)

    @app.post("/api/_test/validate")
    async def _validate(payload: _Payload):  # pragma: no cover - trivial
        return {"ok": True, "name": payload.name}

    @app.get("/api/_test/boom")
    async def _boom():
        raise RuntimeError("secret internal detail: db password is hunter2")

    @app.get("/api/_test/teapot")
    async def _teapot():
        raise HTTPException(status_code=418, detail="short and stout")

    return app


@pytest.fixture
def client():
    return TestClient(_make_app(), raise_server_exceptions=False)


def test_404_standard_shape(client):
    resp = client.get("/api/does/not/exist")
    assert resp.status_code == 404
    body = resp.json()
    assert set(body) == ERROR_KEYS
    assert body["error"] == "Not Found"
    assert body["code"] == "not_found"
    assert body["details"] is None
    # create_app wires RequestIdMiddleware, which generates an ID when the
    # client sends none; the handlers must work either way, so accept a
    # non-empty string or null.
    rid = body["request_id"]
    assert rid is None or (isinstance(rid, str) and rid)


def test_request_id_null_without_middleware():
    """Handlers read the request ID gracefully and yield null when no
    middleware/header provides one (they must not depend on middleware)."""
    from fastapi import FastAPI

    from chatty_commander.web.errors import register_error_handlers

    bare = FastAPI()
    register_error_handlers(bare)
    client = TestClient(bare, raise_server_exceptions=False)
    resp = client.get("/api/missing")
    assert resp.status_code == 404
    body = resp.json()
    assert set(body) == ERROR_KEYS
    assert body["request_id"] is None


def test_http_exception_detail_preserved(client):
    resp = client.get("/api/_test/teapot")
    assert resp.status_code == 418
    body = resp.json()
    assert set(body) == ERROR_KEYS
    assert body["error"] == "short and stout"
    assert body["code"] == "im_a_teapot"


def test_422_validation_details_preserved(client):
    resp = client.post("/api/_test/validate", json={"name": "x", "count": "not-an-int"})
    assert resp.status_code == 422
    body = resp.json()
    assert set(body) == ERROR_KEYS
    assert body["code"] == "validation_error"
    assert body["error"] == "Request validation failed"
    # FastAPI validation error list preserved inside details
    assert isinstance(body["details"], list)
    locs = [tuple(e["loc"]) for e in body["details"]]
    assert ("body", "count") in locs
    assert all("msg" in e and "type" in e for e in body["details"])


def test_forced_500_generic_and_logged(client, caplog):
    with caplog.at_level(logging.ERROR, logger="chatty_commander.web.errors"):
        resp = client.get("/api/_test/boom")
    assert resp.status_code == 500
    body = resp.json()
    assert set(body) == ERROR_KEYS
    assert body["error"] == "Internal server error"
    assert body["code"] == "internal_error"
    assert body["details"] is None
    # No internals or stack traces leaked to the client
    text = resp.text
    assert "hunter2" not in text
    assert "RuntimeError" not in text
    assert "Traceback" not in text
    # ...but the real exception was logged server-side
    assert any(
        r.exc_info and "hunter2" in str(r.exc_info[1]) for r in caplog.records
    ), "expected the underlying exception to be logged server-side"


def test_request_id_echoed_from_header(client):
    resp = client.get("/api/nope", headers={"X-Request-ID": "req-abc-123"})
    assert resp.status_code == 404
    assert resp.json()["request_id"] == "req-abc-123"


def test_request_id_from_request_state_preferred():
    app = _make_app()

    @app.middleware("http")
    async def _set_state_rid(request, call_next):
        request.state.request_id = "state-rid-42"
        return await call_next(request)

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/api/nope", headers={"X-Request-ID": "header-rid"})
    assert resp.status_code == 404
    assert resp.json()["request_id"] == "state-rid-42"


def test_normal_route_unchanged(client):
    resp = client.get("/api/v1/version")
    assert resp.status_code == 200
    body = resp.json()
    assert "version" in body
    assert "error" not in body


def test_non_api_path_keeps_default_shape(client):
    # /bridge/event raises HTTPException(401) on a non-/api path: default
    # FastAPI {"detail": ...} shape must be preserved there.
    resp = client.post("/bridge/event")
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Unauthorized bridge request"}


def test_non_api_404_keeps_default_shape(client):
    resp = client.get("/definitely/not/api")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Not Found"}


def test_auth_middleware_401_bypasses_handlers():
    """AuthMiddleware returns its 401 JSONResponse directly from the
    middleware layer, so the standardized handlers never see it and its
    body shape is unchanged (verified, per task)."""

    class DummyConfig:
        auth = {"api_key": "sekrit"}

    client = TestClient(
        create_app(no_auth=False, config_manager=DummyConfig()),
        raise_server_exceptions=False,
    )
    resp = client.get("/api/v1/version")
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Invalid or missing API key"}
    # With the right key the request passes through normally.
    ok = client.get("/api/v1/version", headers={"X-API-Key": "sekrit"})
    assert ok.status_code == 200


def test_web_mode_server_gets_same_handlers():
    """Both app factories share register_shared_routers, so WebModeServer's
    app must produce the same standardized shape.

    Tested via 422 (validation) rather than 404 because web_mode registers a
    status-code-specific ``@app.exception_handler(404)`` SPA fallback (when a
    frontend build exists) that takes precedence over class-based handlers
    for 404s — a pre-existing behavior outside this feature's scope.
    """
    pytest.importorskip("fastapi")
    from unittest.mock import MagicMock

    from chatty_commander.web.web_mode import WebModeServer

    config = MagicMock()
    config.web_server = {}
    server = WebModeServer(
        config_manager=config,
        state_manager=MagicMock(),
        model_manager=MagicMock(),
        command_executor=MagicMock(),
        no_auth=True,
    )
    client = TestClient(server.app, raise_server_exceptions=False)
    resp = client.post("/api/v1/command", json={})
    assert resp.status_code == 422
    body = resp.json()
    assert set(body) == ERROR_KEYS
    assert body["code"] == "validation_error"
    assert isinstance(body["details"], list)
