#!/usr/bin/env python3
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
Web mode server and models.

Provides a FastAPI application that exposes core REST endpoints, optional
advisors endpoints, and a WebSocket for realtime updates. This module keeps a
stable surface used by tests:
- Pydantic models: SystemStatus, StateChangeRequest, CommandRequest,
  CommandResponse, StateInfo, WebSocketMessage
- WebModeServer class with .app and broadcast helpers
- create_app(no_auth: bool) convenience to spin up a minimal app
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import uvicorn
except ImportError:
    uvicorn = None

from collections import defaultdict

from fastapi import FastAPI, Header, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

# Advisors (optional feature set used by tests)
from chatty_commander.advisors.service import AdvisorMessage, AdvisorsService
from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.routes.core import include_core_routes
from chatty_commander.web.routes.version import router as version_router
from chatty_commander.web.routes.ws import include_ws_routes

# Avatar routes (optional)
try:
    from chatty_commander.web.routes.avatar_api import router as avatar_api_router
except ImportError:
    avatar_api_router = None

try:
    from chatty_commander.web.routes.avatar_ws import router as avatar_ws_router
except ImportError:
    avatar_ws_router = None

try:
    from chatty_commander.web.routes.avatar_selector import (
        router as avatar_selector_router,
    )
except ImportError:
    avatar_selector_router = None

try:
    from .routes.agents import router as agents_router
except ImportError:
    agents_router = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Advisor API models
class AdvisorInbound(BaseModel):
    platform: str
    channel: str
    user: str
    text: str
    username: str | None = None
    metadata: dict[str, Any] | None = None


class AdvisorOutbound(BaseModel):
    reply: str
    context_key: str
    persona_id: str
    model: str
    api_mode: str


class ContextStats(BaseModel):
    total_contexts: int
    platform_distribution: dict[str, int]
    persona_distribution: dict[str, int]
    persistence_enabled: bool
    persistence_path: str


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        # Remove server header for security
        if "server" in response.headers:
            del response.headers["server"]

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        # Clean old requests
        current_time = time.time()
        self.requests[client_ip] = [
            req_time
            for req_time in self.requests[client_ip]
            if current_time - req_time < 60
        ]

        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return HTMLResponse(
                content="Rate limit exceeded. Please try again later.",
                status_code=429,
                headers={"Retry-After": "60"},
            )

        # Add current request
        self.requests[client_ip].append(current_time)

        response = await call_next(request)
        return response


class SystemStatus(BaseModel):
    status: str = Field(..., description="Overall system status")
    current_state: str = Field(..., description="Current operational state")
    active_models: list[str] = Field(..., description="List of loaded models")
    uptime: str = Field(..., description="System uptime")
    version: str = Field(default="0.2.0", description="Application version")


class StateChangeRequest(BaseModel):
    state: str = Field(
        ..., description="Target state", pattern="^(idle|computer|chatty)$"
    )


class CommandRequest(BaseModel):
    command: str = Field(..., description="Command name to execute")
    parameters: dict[str, Any] | None = Field(
        default=None, description="Optional parameters"
    )


class CommandResponse(BaseModel):
    success: bool = Field(..., description="Whether command executed successfully")
    message: str = Field(..., description="Execution result message")
    execution_time: float = Field(..., description="Execution time in milliseconds")


class StateInfo(BaseModel):
    current_state: str = Field(..., description="Current operational state")
    active_models: list[str] = Field(..., description="List of active models")
    last_command: str | None = Field(default=None, description="Last detected command")
    timestamp: str = Field(..., description="Timestamp of last state change")


class WebSocketMessage(BaseModel):
    type: str = Field(..., description="Message type")
    data: dict[str, Any] = Field(..., description="Message data")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class WebModeServer:
    """FastAPI web server for ChattyCommander."""

    def __init__(
        self,
        config_manager: Config,
        state_manager: StateManager,
        model_manager: ModelManager,
        command_executor: CommandExecutor,
        no_auth: bool = False,
    ) -> None:
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.model_manager = model_manager
        self.command_executor = command_executor
        self.no_auth = bool(no_auth)
        self.start_time = time.time()
        self.last_command: str | None = None
        self.commands_executed: int = 0
        self.last_state_change = datetime.now()

        # Performance optimizations
        self._command_cache: dict[str, Any] = {}
        self._state_cache: dict[str, Any] = {}
        self._cache_timeout = 30.0  # 30 seconds cache
        self._last_cache_clear = time.time()

        # Optional advisors service (enabled via config)
        try:
            self.advisors_service = AdvisorsService(config=config_manager)
        except Exception as e:  # noqa: BLE001
            logger.debug(
                "AdvisorsService init failed; continuing without advisors: %s", e
            )
            self.advisors_service = None  # type: ignore[assignment]

        # WebSocket connection management
        self.active_connections: set[WebSocket] = set()

        # Initialize FastAPI app and register routes
        self.app = self._create_app()
        # Hook state change broadcasts
        self.state_manager.add_state_change_callback(self._on_state_change)

    @property
    def config(self) -> Config:
        """Access config manager as 'config' for compatibility."""
        return self.config_manager

    def _execute_command_wrapper(self, cmd: str) -> Any:
        self.commands_executed += 1
        return self.command_executor.execute_command(cmd)

    def _clear_expired_cache(self) -> None:
        """Clear expired cache entries to prevent memory leaks."""
        current_time = time.time()
        if current_time - self._last_cache_clear > self._cache_timeout:
            self._command_cache.clear()
            self._state_cache.clear()
            self._last_cache_clear = current_time

    def _get_cached_command_result(self, command: str) -> Any | None:
        """Get cached command result if available and not expired."""
        self._clear_expired_cache()
        cache_key = f"cmd:{command}"
        if cache_key in self._command_cache:
            cached_time, result = self._command_cache[cache_key]
            if time.time() - cached_time < self._cache_timeout:
                return result
            else:
                del self._command_cache[cache_key]
        return None

    def _cache_command_result(self, command: str, result: Any) -> None:
        """Cache command result for future use."""
        cache_key = f"cmd:{command}"
        self._command_cache[cache_key] = (time.time(), result)

    def run(self, host: str | None = None, port: int | None = None) -> None:
        """Run the web server."""
        if uvicorn is None:
            raise ImportError("uvicorn is not available")

        # Use config values if available
        if host is None and hasattr(self.config_manager, "web_server"):
            host = self.config_manager.web_server.get("host", "0.0.0.0")
        if host is None:
            host = "0.0.0.0"

        if port is None and hasattr(self.config_manager, "web_server"):
            port = self.config_manager.web_server.get("port", 8100)
        if port is None:
            port = 8100

        uvicorn.run(self.app, host=host, port=port)

    # --------------------------
    # App and routing
    # --------------------------
    def _create_app(self) -> FastAPI:
        app = FastAPI(
            title="ChattyCommander API",
            description="Voice command automation system with web interface",
            version="0.2.0",
            docs_url="/docs" if self.no_auth else None,
            redoc_url="/redoc" if self.no_auth else None,
        )

        # Security middleware
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(RateLimitMiddleware, requests_per_minute=10000)

        # CORS policy
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"] if self.no_auth else ["http://localhost:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Core REST via extracted router (status/config/state/command)
        core = include_core_routes(
            get_start_time=lambda: self.start_time,
            get_state_manager=lambda: self.state_manager,
            get_config_manager=lambda: self.config_manager,
            get_last_command=lambda: self.last_command,
            get_last_state_change=lambda: self.last_state_change,
            execute_command_fn=self._execute_command_wrapper,
            get_active_connections=lambda: len(self.active_connections),
            get_cache_size=lambda: len(self._command_cache) + len(self._state_cache),
            get_total_commands=lambda: self.commands_executed,
        )
        app.include_router(core)

        # Version endpoint
        app.include_router(version_router)

        # Agents endpoints
        if agents_router:
            app.include_router(agents_router)

        # Avatar endpoints
        if avatar_api_router:
            app.include_router(avatar_api_router)
        if avatar_ws_router:
            app.include_router(avatar_ws_router)
        if avatar_selector_router:
            app.include_router(avatar_selector_router)

        # WebSocket endpoint using extracted router
        ws = include_ws_routes(
            get_connections=lambda: self.active_connections,
            set_connections=lambda conns: setattr(self, "active_connections", conns),
            get_state_snapshot=lambda: {
                "current_state": self.state_manager.current_state,
                "active_models": (
                    self.state_manager.get_active_models()
                    if hasattr(self.state_manager, "get_active_models")
                    else []
                ),
                "timestamp": self.last_state_change.isoformat(),
            },
            on_message=None,
            heartbeat_seconds=30.0,
        )
        app.include_router(ws)

        # Advisors endpoints (if service available)
        self._register_advisors_routes(app)

        # Bridge endpoints for external integrations
        self._register_bridge_routes(app)

        # Serve static web UI (optional)
        frontend_path = Path("webui/frontend/dist")
        if not frontend_path.exists():
            frontend_path = Path("webui/frontend/build")
        if not frontend_path.exists():
            logger.info("Frontend build not found. Automagically building the frontend UI...")
            try:
                import subprocess
                import sys

                # Check if npm is available
                subprocess.run(["npm", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

                logger.info("Installing frontend dependencies...")
                subprocess.run(["npm", "install", "--no-audit", "--no-fund", "--legacy-peer-deps"], cwd="webui/frontend", stdout=sys.stdout, stderr=sys.stderr, check=True)

                logger.info("Building frontend assets...")
                subprocess.run(["npm", "run", "build"], cwd="webui/frontend", stdout=sys.stdout, stderr=sys.stderr, check=True)

                if Path("webui/frontend/dist").exists():
                    frontend_path = Path("webui/frontend/dist")
                elif Path("webui/frontend/build").exists():
                    frontend_path = Path("webui/frontend/build")
            except FileNotFoundError:
                logger.error("Could not find 'npm' executable. Please install Node.js and run 'npm run build' manually in webui/frontend/.")
            except Exception as e:
                logger.error(f"Automagic frontend build failed: {e}. Please run 'npm run build' manually in webui/frontend/.")

        if frontend_path.exists():
            static_assets = frontend_path / "assets"
            if static_assets.exists():
                app.mount(
                    "/assets", StaticFiles(directory=str(static_assets)), name="assets"
                )

            @app.get("/", response_class=HTMLResponse)
            async def _serve_frontend():  # pragma: no cover - exercised in integration
                index_file = frontend_path / "index.html"
                if index_file.exists():
                    return FileResponse(str(index_file))
                return HTMLResponse(
                    "<h1>ChattyCommander</h1><p>Frontend not built. Run <code>npm run build</code> in webui/frontend/</p>"
                )

        else:
            # Fallback route when frontend is not built
            @app.get("/", response_class=HTMLResponse)
            async def _serve_frontend_fallback():  # pragma: no cover
                return HTMLResponse(
                    "<h1>ChattyCommander</h1><p>Frontend not built. Run <code>npm run build</code> in webui/frontend/</p>"
                )

        # SPA Catch-all: serve index.html for any non-API routes
        # This allows React Router to handle deep linking (e.g. /dashboard)
        if frontend_path.exists():
            @app.exception_handler(404)
            async def spa_fallback(request: Request, exc: HTTPException):
                # If API or static file request fails, let it 404.
                # Otherwise, serve index.html for SPA routing.
                if request.url.path.startswith("/api") or request.url.path.startswith("/assets"):
                     return await app.exception_handler_default(request, exc) if hasattr(app, "exception_handler_default") else HTMLResponse("Not Found", status_code=404)

                index_file = frontend_path / "index.html"
                if index_file.exists():
                    return FileResponse(str(index_file))
                return HTMLResponse("Not Found", status_code=404)


        # Optional avatar UI
        avatar_path = Path("src/chatty_commander/webui/avatar")
        if avatar_path.exists():
            try:
                app.mount(
                    "/avatar-ui", StaticFiles(directory=str(avatar_path)), name="avatar"
                )

                @app.get("/avatar", response_class=HTMLResponse)
                async def _serve_avatar_ui():  # pragma: no cover - exercised in integration
                    index_file = avatar_path / "index.html"
                    if index_file.exists():
                        return FileResponse(str(index_file))
                    return HTMLResponse(
                        "<h1>Avatar UI</h1><p>Avatar UI not found. Ensure index.html exists under src/chatty_commander/webui/avatar/</p>"
                    )

            except Exception as e:  # noqa: BLE001
                logger.warning("Failed to mount avatar UI static files: %s", e)

        return app

    def _register_advisors_routes(self, app: FastAPI) -> None:
        """Register advisors REST endpoints backed by AdvisorsService."""

        @app.get("/api/v1/advisors/personas")
        async def advisor_personas():
            # Return seed data for testing
            if self.no_auth:
                return {"personas": [
                    {"id": "jarvis", "name": "Jarvis", "is_default": True, "system_prompt": "You are a helpful AI assistant named Jarvis."},
                    {"id": "friday", "name": "Friday", "is_default": False, "system_prompt": "You are a witty AI named Friday."},
                    {"id": "hal", "name": "HAL 9000", "is_default": False, "system_prompt": "You are a calm, ominous AI."},
                ]}
            # Production: use advisors_service if available
            svc = self.advisors_service
            if not svc:
                return {"personas": []}
            return {"personas": getattr(svc, "get_personas", lambda: [])()}

        @app.post("/api/v1/advisors/message", response_model=AdvisorOutbound)
        async def advisor_message(
            message: AdvisorInbound,
            x_api_key: str | None = Header(None, alias="X-API-Key"),
        ):
            # Check authentication
            if not self.no_auth:
                expected_key = None
                if hasattr(self.config_manager, "auth"):
                    expected_key = self.config_manager.auth.get("api_key")

                if not expected_key or x_api_key != expected_key:
                    raise HTTPException(status_code=401, detail="Unauthorized")

            if not self.advisors_service:
                raise HTTPException(status_code=500, detail="Advisors unavailable")
            try:
                reply = self.advisors_service.handle_message(
                    AdvisorMessage(
                        platform=message.platform,
                        channel=message.channel,
                        user=message.user,
                        text=message.text,
                        username=message.username,
                        metadata=message.metadata,
                    )
                )
                return AdvisorOutbound(
                    reply=reply.reply,
                    context_key=reply.context_key,
                    persona_id=reply.persona_id,
                    model=reply.model,
                    api_mode=reply.api_mode,
                )
            except HTTPException:
                raise
            except Exception as e:  # noqa: BLE001
                raise HTTPException(status_code=500, detail=str(e)) from e

        @app.post("/api/v1/advisors/context/switch")
        async def switch_persona(context_key: str, persona_id: str):
            svc = self.advisors_service
            if not svc or not getattr(svc, "enabled", False):
                raise HTTPException(status_code=400, detail="Advisors not enabled")
            try:
                success = svc.switch_persona(context_key, persona_id)
                if success:
                    return {
                        "success": True,
                        "context_key": context_key,
                        "persona_id": persona_id,
                    }
                else:
                    raise HTTPException(status_code=400, detail="Invalid persona")
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid persona: {str(e)}"
                ) from e

        @app.delete("/api/v1/advisors/context/{context_key}")
        async def clear_context(context_key: str):
            svc = self.advisors_service
            if not svc or not getattr(svc, "enabled", False):
                raise HTTPException(status_code=400, detail="Advisors not enabled")
            try:
                success = svc.clear_context(context_key)
                if success:
                    return {"success": True, "context_key": context_key}
                else:
                    raise HTTPException(status_code=404, detail="Context not found")
            except Exception as e:
                raise HTTPException(
                    status_code=404, detail=f"Context not found: {str(e)}"
                ) from e

        @app.get("/api/v1/advisors/memory")
        async def advisors_memory(
            platform: str, channel: str, user: str, limit: int = 20
        ):
            svc = self.advisors_service
            if not svc or not getattr(svc, "enabled", False):
                raise HTTPException(status_code=400, detail="Advisors not enabled")
            items = svc.memory.get(platform, channel, user, limit=limit)
            # Convert dataclasses to serializable dicts
            return [
                {"role": i.role, "content": i.content, "timestamp": i.timestamp}
                for i in items
            ]

        @app.delete("/api/v1/advisors/memory")
        async def advisors_memory_clear(platform: str, channel: str, user: str):
            svc = self.advisors_service
            if not svc or not getattr(svc, "enabled", False):
                raise HTTPException(status_code=400, detail="Advisors not enabled")
            count = svc.memory.clear(platform, channel, user)
            return {"cleared": int(count)}

        @app.get("/api/v1/advisors/context/stats", response_model=ContextStats)
        async def advisors_context_stats():
            svc = self.advisors_service
            if not svc or not getattr(svc, "enabled", False):
                raise HTTPException(status_code=400, detail="Advisors not enabled")
            stats = svc.get_context_stats()
            return ContextStats(**stats)

    def _register_bridge_routes(self, app: FastAPI) -> None:
        """Register bridge endpoints for external integrations."""

        @app.post("/bridge/event")
        async def bridge_event(
            event: dict[str, Any],
            x_bridge_token: str | None = Header(None, alias="X-Bridge-Token"),
        ):
            # Check for bridge token in header
            expected_token = "secret"  # TODO: Make configurable
            if not x_bridge_token or x_bridge_token != expected_token:
                raise HTTPException(status_code=401, detail="Invalid bridge token")

            # For now, just echo back the event
            return {"ok": True, "reply": {"text": "Bridge response", "meta": {}}}

    # --------------------------
    # Broadcast helpers and callbacks
    # --------------------------
    def _format_uptime(self, seconds: float) -> str:
        days, remainder = divmod(int(seconds), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds_i = divmod(remainder, 60)
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds_i}s"
        return f"{hours}h {minutes}m {seconds_i}s"

    async def _broadcast_message(self, message: WebSocketMessage) -> None:
        """Broadcast a message to all active WebSocket connections."""
        payload = message.model_dump_json()
        for ws in list(self.active_connections):
            try:
                await ws.send_text(payload)
            except Exception as e:  # noqa: BLE001
                logger.debug("broadcast failed to a client: %s", e)
                try:
                    self.active_connections.discard(ws)
                except Exception:
                    pass

    def _on_state_change(self, old_state: str, new_state: str) -> None:
        self.last_state_change = datetime.now()
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.create_task(
            self._broadcast_message(
                WebSocketMessage(
                    type="state_change",
                    data={
                        "old_state": old_state,
                        "new_state": new_state,
                        "timestamp": self.last_state_change.isoformat(),
                    },
                )
            )
        )

    # Optional convenience callbacks (exposed for tests)
    def on_command_detected(self, command: str, confidence: float) -> None:
        self.commands_executed += 1
        self.last_command = command
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.create_task(
            self._broadcast_message(
                WebSocketMessage(
                    type="command_detected",
                    data={"command": command, "confidence": confidence},
                )
            )
        )

    def on_system_event(self, event_type: str, details: str | dict[str, Any]) -> None:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.create_task(
            self._broadcast_message(
                WebSocketMessage(type=event_type, data={"message": details})
            )
        )


def create_app(
    *,
    config: Config | None = None,
    config_manager: Config | None = None,
    state_manager: StateManager | None = None,
    model_manager: ModelManager | None = None,
    command_executor: CommandExecutor | None = None,
    no_auth: bool = False,
) -> FastAPI:
    """Convenience function to create a minimal FastAPI app for tests."""
    # Use WebModeServer to ensure core routes are included
    cfg = config or config_manager or Config(config_file="")
    sm = state_manager or StateManager(cfg)
    mm = model_manager or ModelManager(cfg)
    ce = command_executor or CommandExecutor(cfg, mm, sm)
    return WebModeServer(cfg, sm, mm, ce, no_auth=no_auth).app


def run_server(
    config_manager: Config,
    state_manager: StateManager,
    model_manager: ModelManager,
    command_executor: CommandExecutor,
    host: str = "0.0.0.0",
    port: int = 8100,
    no_auth: bool = False,
) -> None:
    """Run the web server with uvicorn."""
    if uvicorn is None:
        raise ImportError("uvicorn is not available")

    app = WebModeServer(
        config_manager, state_manager, model_manager, command_executor, no_auth=no_auth
    ).app
    uvicorn.run(app, host=host, port=port)
