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

"""Authentication middleware for FastAPI."""

import logging
import os
import posixpath
import urllib.parse
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from chatty_commander.utils.security import constant_time_compare

logger = logging.getLogger(__name__)


def resolve_expected_api_key(config_manager) -> str | None:
    """Resolve the expected X-API-Key from env or config.

    Precedence (highest first):
    1. ``CHATTY_API_KEY`` environment variable (non-blank).
    2. ``config_manager.auth["api_key"]`` — test/DummyConfig objects.
    3. ``config_manager.config["auth"]["api_key"]`` — the real ``Config``.

    Returns ``None`` when no key is configured anywhere (the zero-config
    default), in which case authentication cannot succeed.
    """
    env_key = os.environ.get("CHATTY_API_KEY")
    if env_key and env_key.strip():
        return env_key

    key: object = None
    # Check for DummyConfig pattern (test configs)
    if hasattr(config_manager, "auth"):
        key = config_manager.auth.get("api_key")
    # Check for regular Config pattern
    elif hasattr(config_manager, "config") and config_manager.config:
        key = config_manager.config.get("auth", {}).get("api_key")
    return key if isinstance(key, str) else None


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to handle API key authentication."""

    def __init__(self, app, config_manager, no_auth: bool = False):
        super().__init__(app)
        self.config_manager = config_manager
        self.no_auth = no_auth

        # Endpoints that don't require authentication
        self.public_endpoints = {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static",
        }

        # Exact match endpoints that don't require authentication
        self.public_exact_endpoints = {
            "/",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and validate authentication if required."""
        # Skip auth in no_auth mode
        if self.no_auth:
            return await call_next(request)  # type: ignore[no-any-return]

        # Decode path to prevent URL-encoded or double-encoded path traversal bypasses
        raw_path = request.url.path
        decoded_path = urllib.parse.unquote(raw_path)
        for _ in range(10):
            if "%" not in decoded_path:
                break
            new_decoded = urllib.parse.unquote(decoded_path)
            if new_decoded == decoded_path:
                break
            decoded_path = new_decoded
        raw_path = decoded_path

        # Normalize path to prevent path traversal bypasses
        # Use exact match or explicit trailing slash check to prevent partial path matching
        path = posixpath.normpath(raw_path)
        if path.startswith("//"):
            path = "/" + path.lstrip("/")

        # Skip auth for public endpoints
        if (
            any(path == endpoint or path.startswith(endpoint + "/") for endpoint in self.public_endpoints)
            or path in self.public_exact_endpoints
        ):
            return await call_next(request)  # type: ignore[no-any-return]

        # Skip auth for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)  # type: ignore[no-any-return]

        # The JWT auth router (/api/v1/auth/*) validates user credentials /
        # bearer tokens itself, so it must NOT require the global X-API-Key
        # (the unauthenticated login form has no key). It sits under /api/ so
        # this exemption has to come before the X-API-Key gate below.
        if path == "/api/v1/auth" or path.startswith("/api/v1/auth/"):
            return await call_next(request)  # type: ignore[no-any-return]

        # Validate API key for protected endpoints
        if path == "/api" or path.startswith("/api/"):
            api_key = request.headers.get("X-API-Key")
            logger.debug(
                f"API request to {path}, API key present: {api_key is not None}"
            )

            # Get expected API key from env (preferred) or config.
            expected_key = resolve_expected_api_key(self.config_manager)
            logger.debug("Expected API key resolved: present=%s", bool(expected_key))

            # Check if API key is valid
            if not constant_time_compare(api_key, expected_key):
                logger.debug("Auth failed for %s - API key mismatch or missing", path)
                # Return 401 response directly instead of raising exception
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=401, content={"detail": "Invalid or missing API key"}
                )

            logger.debug("Authentication successful")

        return await call_next(request)  # type: ignore[no-any-return]
