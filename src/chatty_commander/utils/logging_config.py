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

"""
Structured logging configuration for ChattyCommander.

Activates JSON-formatted logs when the LOG_FORMAT=json environment variable is set.
Each log record includes: timestamp, level, logger name, message, and request_id
(when available via the RequestIdMiddleware).

Usage:
    # In application startup:
    from chatty_commander.utils.logging_config import configure_logging
    configure_logging()

    # In FastAPI app:
    from chatty_commander.utils.logging_config import RequestIdMiddleware
    app.add_middleware(RequestIdMiddleware)
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from collections.abc import Callable
from contextvars import ContextVar
from typing import Any

# Context variable holding the current request ID (empty string when not in a request)
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Return the current request ID, or empty string if not in a request context."""
    return _request_id_var.get()


class StructuredJSONFormatter(logging.Formatter):
    """JSON log formatter that includes request_id from context.

    Outputs one JSON object per line with fields:
    - time: ISO 8601 timestamp
    - level: log level name
    - logger: logger name
    - message: formatted log message
    - request_id: UUID from the current request context (omitted if empty)
    - exception: formatted exception traceback (omitted if no exception)
    """

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = _request_id_var.get()
        if request_id:
            entry["request_id"] = request_id
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            entry["stack_info"] = self.formatStack(record.stack_info)
        return json.dumps(entry, ensure_ascii=False)


def configure_logging(
    level: str | None = None,
    log_format: str | None = None,
) -> None:
    """Configure root logger based on environment variables.

    Environment variables:
    - LOG_LEVEL: log level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO.
    - LOG_FORMAT: output format. Set to 'json' for structured JSON output.
                  Any other value (or unset) uses the standard plain-text format.

    Args:
        level: Override LOG_LEVEL env var. If None, reads from environment.
        log_format: Override LOG_FORMAT env var. If None, reads from environment.
    """
    effective_level = level or os.environ.get("LOG_LEVEL", "INFO")
    effective_format = log_format or os.environ.get("LOG_FORMAT", "plain")

    numeric_level = getattr(logging, effective_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicate output
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setLevel(numeric_level)

    if effective_format.lower() == "json":
        handler.setFormatter(StructuredJSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s: %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )

    root_logger.addHandler(handler)


# ---------------------------------------------------------------------------
# FastAPI / Starlette middleware
# ---------------------------------------------------------------------------

try:
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware

    class RequestIdMiddleware(BaseHTTPMiddleware):
        """Middleware that assigns a UUID request ID to each incoming request.

        The ID is:
        - Read from the X-Request-ID header if present (allows tracing across services).
        - Generated as a new UUID4 otherwise.
        - Stored in a ContextVar so all log records emitted during the request
          automatically include it via StructuredJSONFormatter.
        - Echoed back in the X-Request-ID response header.
        """

        async def dispatch(
            self, request: Request, call_next: Callable[[Request], Any]
        ) -> Response:
            request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
            token = _request_id_var.set(request_id)
            try:
                response = await call_next(request)
                response.headers["X-Request-ID"] = request_id
                return response
            finally:
                _request_id_var.reset(token)

except Exception:  # pragma: no cover - FastAPI not available in all test envs
    RequestIdMiddleware = None  # type: ignore[assignment,misc]
