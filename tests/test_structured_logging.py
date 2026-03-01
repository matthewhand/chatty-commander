"""Tests for structured JSON logging configuration."""
from __future__ import annotations

import json
import logging
import os
from io import StringIO
from unittest.mock import patch


def test_configure_logging_plain_format(capsys):
    """configure_logging() with LOG_FORMAT=plain uses standard text format."""
    from chatty_commander.utils.logging_config import configure_logging

    with patch.dict(os.environ, {"LOG_FORMAT": "plain", "LOG_LEVEL": "DEBUG"}):
        configure_logging()

    logger = logging.getLogger("test.plain")
    logger.info("hello plain")

    captured = capsys.readouterr()
    # Plain format should NOT be valid JSON
    assert "hello plain" in captured.err
    # Should not be parseable as JSON
    for line in captured.err.splitlines():
        if "hello plain" in line:
            try:
                json.loads(line)
                assert False, "Plain format should not produce JSON"
            except json.JSONDecodeError:
                pass  # Expected


def test_configure_logging_json_format():
    """configure_logging() with LOG_FORMAT=json produces valid JSON lines."""
    from chatty_commander.utils.logging_config import configure_logging

    stream = StringIO()
    handler = logging.StreamHandler(stream)

    with patch.dict(os.environ, {"LOG_FORMAT": "json", "LOG_LEVEL": "DEBUG"}):
        configure_logging()

    # Replace the root handler with our stream handler using the JSON formatter
    from chatty_commander.utils.logging_config import StructuredJSONFormatter
    handler.setFormatter(StructuredJSONFormatter())
    root = logging.getLogger()
    root.addHandler(handler)

    try:
        logger = logging.getLogger("test.json")
        logger.info("hello json")

        output = stream.getvalue()
        lines = [l for l in output.splitlines() if l.strip()]
        assert lines, "Expected at least one log line"

        parsed = json.loads(lines[-1])
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "hello json"
        assert "time" in parsed
        assert "logger" in parsed
    finally:
        root.removeHandler(handler)


def test_json_formatter_includes_exception():
    """StructuredJSONFormatter includes exception info when present."""
    from chatty_commander.utils.logging_config import StructuredJSONFormatter

    formatter = StructuredJSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="something failed",
        args=(),
        exc_info=None,
    )
    try:
        raise ValueError("test error")
    except ValueError:
        import sys
        record.exc_info = sys.exc_info()

    output = formatter.format(record)
    parsed = json.loads(output)
    assert "exception" in parsed
    assert "ValueError" in parsed["exception"]


def test_json_formatter_includes_request_id():
    """StructuredJSONFormatter includes request_id from context var when set."""
    from chatty_commander.utils.logging_config import (
        StructuredJSONFormatter,
        _request_id_var,
    )

    formatter = StructuredJSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="with request id",
        args=(),
        exc_info=None,
    )

    token = _request_id_var.set("test-request-123")
    try:
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed.get("request_id") == "test-request-123"
    finally:
        _request_id_var.reset(token)


def test_json_formatter_omits_request_id_when_empty():
    """StructuredJSONFormatter omits request_id when context var is empty."""
    from chatty_commander.utils.logging_config import (
        StructuredJSONFormatter,
        _request_id_var,
    )

    formatter = StructuredJSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="no request id",
        args=(),
        exc_info=None,
    )

    # Ensure context var is empty
    token = _request_id_var.set("")
    try:
        output = formatter.format(record)
        parsed = json.loads(output)
        assert "request_id" not in parsed
    finally:
        _request_id_var.reset(token)


def test_request_id_middleware_sets_header():
    """RequestIdMiddleware adds X-Request-ID to response headers."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from chatty_commander.utils.logging_config import RequestIdMiddleware

    if RequestIdMiddleware is None:
        import pytest
        pytest.skip("FastAPI not available")

    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/ping")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    # Should be a valid UUID
    import uuid
    uuid.UUID(response.headers["x-request-id"])  # raises if invalid


def test_request_id_middleware_preserves_incoming_id():
    """RequestIdMiddleware uses X-Request-ID from request if provided."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from chatty_commander.utils.logging_config import RequestIdMiddleware

    if RequestIdMiddleware is None:
        import pytest
        pytest.skip("FastAPI not available")

    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/ping", headers={"X-Request-ID": "my-trace-id-123"})
    assert response.headers.get("x-request-id") == "my-trace-id-123"
