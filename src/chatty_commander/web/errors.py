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

"""Standardized JSON error responses for the ChattyCommander API.

ROADMAP "Standardized error responses": every error returned from an
``/api/*`` path uses one consistent JSON shape::

    {"error": <human message>, "code": <machine code>, "details": <extra|null>,
     "request_id": <id|null>}

Covered cases (registered via :func:`register_error_handlers`):

- ``HTTPException`` (and Starlette's base ``HTTPException``) — ``error`` is the
  exception detail, ``code`` is a slug of the HTTP reason phrase
  (e.g. ``not_found``).
- Request validation failures (FastAPI 422) — the original validation error
  list is preserved under ``details``.
- Unhandled exceptions — a generic 500 body; the real exception is logged
  server-side and never leaked to the client.

Non-``/api`` paths keep FastAPI's default ``{"detail": ...}`` responses so
existing endpoints (``/bridge/event``, docs, static files) are unchanged.

Note on auth: ``AuthMiddleware`` returns its 401 ``JSONResponse`` directly
from the middleware layer, so it never reaches these exception handlers and
its ``{"detail": "Invalid or missing API key"}`` body is intentionally
untouched.

``request_id`` is read opportunistically — from ``request.state.request_id``
if some middleware set it, else from the ``X-Request-ID`` request header, else
from the logging-context ContextVar populated by ``RequestIdMiddleware`` —
and is ``null`` when none is available. No middleware is required for the
handlers to work.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import http_exception_handler as _default_http_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

logger = logging.getLogger(__name__)

#: Generic message returned for unhandled exceptions — never the repr/str of
#: the underlying exception, which could leak internals.
INTERNAL_ERROR_MESSAGE = "Internal server error"


def _is_api_path(request: Request) -> bool:
    """Return True when the request targets an ``/api`` path."""
    path = request.url.path
    return path == "/api" or path.startswith("/api/")


def get_request_id(request: Request) -> str | None:
    """Best-effort request ID lookup; ``None`` when unavailable.

    Checks, in order: ``request.state.request_id`` (set by request-ID
    middleware when present), the ``X-Request-ID`` request header, and the
    logging ContextVar used by ``RequestIdMiddleware``. The handlers never
    require any of these to exist.
    """
    rid = getattr(request.state, "request_id", None)
    if rid:
        return str(rid)
    rid = request.headers.get("X-Request-ID")
    if rid:
        return rid
    try:
        from chatty_commander.utils.logging_config import (
            get_request_id as _ctx_request_id,
        )

        rid = _ctx_request_id()
    except Exception:  # pragma: no cover - optional dependency path
        rid = None
    return rid or None


def error_payload(
    error: str,
    code: str,
    details: Any = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Build the standardized error body."""
    return {
        "error": error,
        "code": code,
        "details": details,
        "request_id": request_id,
    }


def _status_code_slug(status_code: int) -> str:
    """Machine-readable code for an HTTP status, e.g. 404 -> ``not_found``."""
    try:
        phrase = HTTPStatus(status_code).phrase
    except ValueError:
        return f"http_{status_code}"
    slug = "".join(
        c if c.isalnum() else "_" for c in phrase.lower().replace("'", "")
    )
    return slug


async def _handle_http_exception(
    request: Request, exc: StarletteHTTPException
) -> Response:
    """Standardize HTTPException bodies on /api paths; default elsewhere."""
    if not _is_api_path(request):
        return await _default_http_handler(request, exc)

    detail = exc.detail
    if isinstance(detail, str):
        error, details = detail, None
    else:
        # Non-string details (dicts/lists) belong in `details`, with the
        # reason phrase as the human-readable message.
        error = HTTPStatus(exc.status_code).phrase if 100 <= exc.status_code < 600 else "Error"
        details = jsonable_encoder(detail)

    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(
            error=error,
            code=_status_code_slug(exc.status_code),
            details=details,
            request_id=get_request_id(request),
        ),
        headers=getattr(exc, "headers", None),
    )


async def _handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Standardize FastAPI 422 bodies, preserving validation details."""
    details = jsonable_encoder(exc.errors())
    if not _is_api_path(request):
        # Default FastAPI shape for non-API paths.
        return JSONResponse(status_code=422, content={"detail": details})

    return JSONResponse(
        status_code=422,
        content=error_payload(
            error="Request validation failed",
            code="validation_error",
            details=details,
            request_id=get_request_id(request),
        ),
    )


async def _handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    """Return a generic 500 body; log the real exception server-side only."""
    logger.exception(
        "Unhandled exception on %s %s", request.method, request.url.path, exc_info=exc
    )
    if not _is_api_path(request):
        # Match Starlette's default plain 500 for non-API paths.
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )

    return JSONResponse(
        status_code=500,
        content=error_payload(
            error=INTERNAL_ERROR_MESSAGE,
            code="internal_error",
            details=None,
            request_id=get_request_id(request),
        ),
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register the standardized error handlers on ``app``.

    Idempotent: handler registration is a dict assignment keyed by exception
    class, so calling this twice is harmless. Safe to call on the minimal
    FastAPI stub used when FastAPI is unavailable (no-op).
    """
    add = getattr(app, "add_exception_handler", None)
    if add is None:  # minimal stub app in import-degraded environments
        return
    add(StarletteHTTPException, _handle_http_exception)
    add(RequestValidationError, _handle_validation_error)
    add(Exception, _handle_unhandled_exception)
