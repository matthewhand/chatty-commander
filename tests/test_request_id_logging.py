"""Tests for ROADMAP 'Structured logging': LOG_FORMAT=json via setup_logger and
the request-ID middleware at chatty_commander.web.middleware.request_id.

Covers:
- setup_logger emits parseable JSON (level/name/message/request_id) when
  LOG_FORMAT=json, and keeps the human-readable default otherwise.
- RequestIdMiddleware echoes an inbound X-Request-ID, generates a UUID when
  absent, and propagates the ID to log records emitted inside route handlers
  via the contextvar.
- server.create_app wires the middleware.
"""

from __future__ import annotations

import json
import logging
import uuid
from io import StringIO

import pytest


def _fresh_logger_via_setup(name: str) -> tuple[logging.Logger, StringIO]:
    """Run setup_logger for a fresh logger name and capture its console output."""
    from chatty_commander.utils.logger import setup_logger

    logger = setup_logger(name)
    stream = StringIO()
    # Redirect the console handler that setup_logger attached
    handlers = [
        h
        for h in logger.handlers
        if isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.FileHandler)
    ]
    assert handlers, "setup_logger should attach a console handler"
    handlers[0].stream = stream
    return logger, stream


class TestSetupLoggerJsonFormat:
    def test_json_mode_emits_parseable_json_with_required_fields(self, monkeypatch):
        monkeypatch.setenv("LOG_FORMAT", "json")
        from chatty_commander.utils.logging_config import _request_id_var

        logger, stream = _fresh_logger_via_setup("test.jsonmode.fields")

        token = _request_id_var.set("rid-json-mode-1")
        try:
            logger.warning("structured hello")
        finally:
            _request_id_var.reset(token)

        lines = [line for line in stream.getvalue().splitlines() if line.strip()]
        assert lines, "expected a log line"
        parsed = json.loads(lines[-1])
        assert parsed["level"] == "WARNING"
        assert parsed["name"] == "test.jsonmode.fields"
        assert parsed["message"] == "structured hello"
        assert parsed["request_id"] == "rid-json-mode-1"
        assert "time" in parsed

    def test_json_mode_omits_request_id_outside_request_context(self, monkeypatch):
        monkeypatch.setenv("LOG_FORMAT", "json")
        logger, stream = _fresh_logger_via_setup("test.jsonmode.norid")

        logger.info("no request context")

        parsed = json.loads(stream.getvalue().splitlines()[-1])
        assert parsed["message"] == "no request context"
        assert "request_id" not in parsed

    def test_default_format_is_unchanged_human_format(self, monkeypatch):
        monkeypatch.delenv("LOG_FORMAT", raising=False)
        logger, stream = _fresh_logger_via_setup("test.plainmode.default")

        logger.info("plain hello")

        line = stream.getvalue().splitlines()[-1]
        # Existing human format: "<asctime> - <name> - <level> - <message>"
        assert " - test.plainmode.default - INFO - plain hello" in line
        with pytest.raises(json.JSONDecodeError):
            json.loads(line)

    def test_non_json_value_keeps_human_format(self, monkeypatch):
        monkeypatch.setenv("LOG_FORMAT", "fancy")
        logger, stream = _fresh_logger_via_setup("test.plainmode.other")

        logger.info("still plain")

        line = stream.getvalue().splitlines()[-1]
        assert " - test.plainmode.other - INFO - still plain" in line


def _middleware_app():
    fastapi = pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from chatty_commander.web.middleware.request_id import RequestIdMiddleware

    if RequestIdMiddleware is None:
        pytest.skip("RequestIdMiddleware unavailable (no starlette)")

    app = fastapi.FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/rid")
    async def rid():
        from chatty_commander.web.middleware.request_id import get_request_id

        return {"request_id": get_request_id()}

    return app, TestClient(app)


class TestRequestIdMiddleware:
    def test_echoes_inbound_x_request_id(self):
        _, client = _middleware_app()
        resp = client.get("/rid", headers={"X-Request-ID": "trace-abc-123"})
        assert resp.status_code == 200
        assert resp.headers["x-request-id"] == "trace-abc-123"
        # Contextvar inside the route saw the same ID
        assert resp.json()["request_id"] == "trace-abc-123"

    def test_generates_uuid_when_header_absent(self):
        _, client = _middleware_app()
        resp = client.get("/rid")
        assert resp.status_code == 200
        rid = resp.headers["x-request-id"]
        uuid.UUID(rid)  # raises if not a valid UUID
        assert resp.json()["request_id"] == rid

    def test_route_log_records_carry_request_id_in_json_mode(self):
        """A log emitted inside a route, formatted by the JSON formatter,
        includes the inbound request ID."""
        fastapi = pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from chatty_commander.utils.logger import JSONFormatter
        from chatty_commander.web.middleware.request_id import RequestIdMiddleware

        if RequestIdMiddleware is None:
            pytest.skip("RequestIdMiddleware unavailable (no starlette)")

        app = fastapi.FastAPI()
        app.add_middleware(RequestIdMiddleware)

        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())
        route_logger = logging.getLogger("test.route.jsonlogs")
        route_logger.setLevel(logging.INFO)
        route_logger.addHandler(handler)
        route_logger.propagate = False

        @app.get("/logme")
        async def logme():
            route_logger.info("handling request")
            return {"ok": True}

        try:
            client = TestClient(app)
            resp = client.get("/logme", headers={"X-Request-ID": "rid-route-77"})
            assert resp.status_code == 200
        finally:
            route_logger.removeHandler(handler)

        parsed = json.loads(stream.getvalue().splitlines()[-1])
        assert parsed["message"] == "handling request"
        assert parsed["name"] == "test.route.jsonlogs"
        assert parsed["level"] == "INFO"
        assert parsed["request_id"] == "rid-route-77"


class TestCreateAppWiring:
    def test_create_app_responses_carry_x_request_id(self):
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from chatty_commander.web.server import create_app

        app = create_app(no_auth=True)
        client = TestClient(app)

        resp = client.get("/api/v1/version")
        assert "x-request-id" in resp.headers
        uuid.UUID(resp.headers["x-request-id"])

        resp = client.get("/api/v1/version", headers={"X-Request-ID": "wired-1"})
        assert resp.headers.get("x-request-id") == "wired-1"
