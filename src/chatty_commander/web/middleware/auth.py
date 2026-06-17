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
import posixpath
import urllib.parse
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from chatty_commander.utils.security import constant_time_compare

logger = logging.getLogger(__name__)


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

    def _decode_and_normalize_path(self, raw_path: str) -> str:
        """Decode URL-encoded path (up to 10 levels) and normalize to prevent traversal bypasses (small helper extracted from dispatch)."""
        decoded_path = urllib.parse.unquote(raw_path)
        for _ in range(10):
            if "%" not in decoded_path:
                break
            new_decoded = urllib.parse.unquote(decoded_path)
            if new_decoded == decoded_path:
                break
            decoded_path = new_decoded
        path = posixpath.normpath(decoded_path)
        if path.startswith("//"):
            path = "/" + path.lstrip("/")
        return path

    def _is_public_endpoint(self, path: str) -> bool:
        """Check if path matches public endpoints (exact or prefix) or OPTIONS (small helper extracted from dispatch)."""
        if (
            any(path == endpoint or path.startswith(endpoint + "/") for endpoint in self.public_endpoints)
            or path in self.public_exact_endpoints
        ):
            return True
        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if self.no_auth:
            return await call_next(request)  # type: ignore[no-any-return]

        path = self._decode_and_normalize_path(request.url.path)

        if self._is_public_endpoint(path):
            return await call_next(request)  # type: ignore[no-any-return]

        if request.method == "OPTIONS":
            return await call_next(request)  # type: ignore[no-any-return]

        if path == "/api" or path.startswith("/api/"):
            api_key = request.headers.get("X-API-Key")
            logger.debug(
                f"API request to {path}, API key present: {api_key is not None}"
            )

            expected_key = None

            if hasattr(self.config_manager, "auth"):
                expected_key = self.config_manager.auth.get("api_key")
                logger.debug("Found auth config in DummyConfig: key present=%s", bool(expected_key))
            elif hasattr(self.config_manager, "config") and self.config_manager.config:
                auth_config = self.config_manager.config.get("auth", {})
                expected_key = auth_config.get("api_key")
                logger.debug("Found auth config in regular Config: key present=%s", bool(expected_key))
            else:
                logger.debug(
                    "No auth config found, config_manager type: %s", type(self.config_manager).__name__
                )

            if not constant_time_compare(api_key, expected_key):
                logger.debug("Auth failed for %s - API key mismatch or missing", path)
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=401, content={"detail": "Invalid or missing API key"}
                )

            logger.debug("Authentication successful")

        return await call_next(request)  # type: ignore[no-any-return]
