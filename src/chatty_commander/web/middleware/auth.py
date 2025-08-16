"""Authentication middleware for FastAPI."""

import logging
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

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

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and validate authentication if required."""
        # Skip auth in no_auth mode
        if self.no_auth:
            return await call_next(request)

        # Skip auth for public endpoints
        path = request.url.path
        if (
            any(path.startswith(endpoint) for endpoint in self.public_endpoints)
            or path in self.public_exact_endpoints
        ):
            return await call_next(request)

        # Skip auth for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Validate API key for protected endpoints
        if path.startswith("/api/"):
            api_key = request.headers.get("X-API-Key")
            logger.debug(f"API request to {path}, API key present: {api_key is not None}")

            # Get expected API key from config
            expected_key = None

            # Check for DummyConfig pattern (test configs)
            if hasattr(self.config_manager, 'auth'):
                expected_key = self.config_manager.auth.get("api_key")
                logger.debug(f"Found auth config in DummyConfig: {expected_key}")
            # Check for regular Config pattern
            elif hasattr(self.config_manager, 'config') and self.config_manager.config:
                auth_config = self.config_manager.config.get("auth", {})
                expected_key = auth_config.get("api_key")
                logger.debug(f"Found auth config in regular Config: {expected_key}")
            else:
                logger.debug(
                    f"No auth config found, config_manager type: {type(self.config_manager)}"
                )

            # Check if API key is required and valid
            if not expected_key:
                # No API key configured, allow request
                logger.debug("No API key configured, allowing request")
                return await call_next(request)

            if not api_key or api_key != expected_key:
                logger.debug(f"Auth failed - provided: {api_key}, expected: {expected_key}")
                # Return 401 response directly instead of raising exception
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=401, content={"detail": "Invalid or missing API key"}
                )

            logger.debug("Authentication successful")

        return await call_next(request)
