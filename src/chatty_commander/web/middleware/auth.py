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
from chatty_commander.web.middleware.service_keys import resolve_service_key_scopes

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

<<<<<<< HEAD
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and validate authentication if required."""
        # Skip auth in no_auth mode
        if self.no_auth:
            return await call_next(request)  # type: ignore[no-any-return]

        # Decode path to prevent URL-encoded or double-encoded path traversal bypasses
        raw_path = request.url.path
=======
    def _decode_and_normalize_path(self, raw_path: str) -> str:
        """Decode URL-encoded path (up to 10 levels) and normalize to prevent traversal bypasses (small helper extracted from dispatch)."""
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
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

<<<<<<< HEAD
        # Skip auth for public endpoints
=======
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if path matches public endpoints (exact or prefix) or OPTIONS (small helper extracted from dispatch)."""
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
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

<<<<<<< HEAD
        # The JWT auth router (/api/v1/auth/*) validates user credentials /
        # bearer tokens itself, so it must NOT require the global X-API-Key
        # (the unauthenticated login form has no key). It sits under /api/ so
        # this exemption has to come before the X-API-Key gate below.
        if path == "/api/v1/auth" or path.startswith("/api/v1/auth/"):
            return await call_next(request)  # type: ignore[no-any-return]

        # Validate API key for protected endpoints
=======
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        if path == "/api" or path.startswith("/api/"):
            api_key = request.headers.get("X-API-Key")
            logger.debug(
                f"API request to {path}, API key present: {api_key is not None}"
            )

<<<<<<< HEAD
            # Get expected legacy single key from env (preferred) or config.
            expected_key = resolve_expected_api_key(self.config_manager)
            logger.debug("Expected API key resolved: present=%s", bool(expected_key))

            # Phase 3 (design §5): the X-API-Key is valid if it matches the
            # legacy single key (→ wildcard scope ['*']) OR any *active* named
            # service key (→ that key's configured scopes). The legacy key is
            # checked first so its byte-for-byte behavior is unchanged; service
            # keys are opt-in and only consulted when an `auth.service_keys`
            # block exists (resolve_service_key_scopes returns None otherwise).
            scopes: list[str] | None = None
            if constant_time_compare(api_key, expected_key):
                scopes = ["*"]
=======
            expected_key = None

            if hasattr(self.config_manager, "auth"):
                expected_key = self.config_manager.auth.get("api_key")
                logger.debug("Found auth config in DummyConfig: key present=%s", bool(expected_key))
            elif hasattr(self.config_manager, "config") and self.config_manager.config:
                auth_config = self.config_manager.config.get("auth", {})
                expected_key = auth_config.get("api_key")
                logger.debug("Found auth config in regular Config: key present=%s", bool(expected_key))
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            else:
                scopes = resolve_service_key_scopes(self.config_manager, api_key)

<<<<<<< HEAD
            if scopes is None:
=======
            if not constant_time_compare(api_key, expected_key):
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                logger.debug("Auth failed for %s - API key mismatch or missing", path)
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=401, content={"detail": "Invalid or missing API key"}
                )

            # Attach the resolved scopes so per-route require_scope dependencies
            # (web/deps/auth.py) can authorize without re-validating the key.
            request.state.scopes = scopes
            logger.debug("Authentication successful (scopes=%s)", scopes)

        return await call_next(request)  # type: ignore[no-any-return]
