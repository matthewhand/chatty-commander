#!/usr/bin/env python3
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

from fastapi import FastAPI, Header, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Advisors (optional feature set used by tests)
from chatty_commander.advisors.service import AdvisorMessage, AdvisorsService
from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.routes.core import include_core_routes
from chatty_commander.web.routes.version import router as version_router
from chatty_commander.web.routes.ws import include_ws_routes

try:
    from .routes.agents import router as agents_router
except ImportError:
    agents_router = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemStatus(BaseModel):
    status: str = Field(..., description="Overall system status")
    current_state: str = Field(..., description="Current operational state")
    active_models: list[str] = Field(..., description="List of loaded models")
    uptime: str = Field(..., description="System uptime")
    version: str = Field(default="0.2.0", description="Application version")


class StateChangeRequest(BaseModel):
    state: str = Field(..., description="Target state", pattern="^(idle|computer|chatty)$")


class CommandRequest(BaseModel):
    command: str = Field(..., description="Command name to execute")
    parameters: dict[str, Any] | None = Field(default=None, description="Optional parameters")


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
        self.last_state_change = datetime.now()

        # Optional advisors service (enabled via config)
        try:
            self.advisors_service = AdvisorsService(config=config_manager)
        except Exception as e:  # noqa: BLE001
            logger.debug("AdvisorsService init failed; continuing without advisors: %s", e)
            self.advisors_service = None  # type: ignore[assignment]

        # WebSocket connection management
        self.active_connections: set[WebSocket] = set()

        # Initialize FastAPI app and register routes
        self.app = self._create_app()
        # Hook state change broadcasts
        self.state_manager.add_state_change_callback(self._on_state_change)

    def run(self, host: str | None = None, port: int | None = None) -> None:
        """Run the web server."""
        if uvicorn is None:
            raise ImportError("uvicorn is not available")

        # Use config values if available
        if host is None and hasattr(self.config_manager, 'web_server'):
            host = self.config_manager.web_server.get('host', '0.0.0.0')
        if host is None:
            host = '0.0.0.0'

        if port is None and hasattr(self.config_manager, 'web_server'):
            port = self.config_manager.web_server.get('port', 8100)
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
            execute_command_fn=lambda cmd: self.command_executor.execute_command(cmd),
        )
        app.include_router(core)

        # Version endpoint
        app.include_router(version_router)

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
        if frontend_path.exists():
            app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

            @app.get("/", response_class=HTMLResponse)
            async def _serve_frontend():  # pragma: no cover - exercised in integration
                index_file = frontend_path / "index.html"
                if index_file.exists():
                    return FileResponse(str(index_file))
                return HTMLResponse(
                    "<h1>ChattyCommander</h1><p>Frontend not built. Run <code>npm run build</code> in webui/frontend/</p>"
                )

        # Optional avatar UI
        avatar_path = Path("src/chatty_commander/webui/avatar")
        if avatar_path.exists():
            try:
                app.mount("/avatar-ui", StaticFiles(directory=str(avatar_path)), name="avatar")

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

        @app.post("/api/v1/advisors/message", response_model=AdvisorOutbound)
        async def advisor_message(message: AdvisorInbound):
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

        @app.get("/api/v1/advisors/memory")
        async def advisors_memory(platform: str, channel: str, user: str, limit: int = 20):
            svc = self.advisors_service
            if not svc or not getattr(svc, "enabled", False):
                raise HTTPException(status_code=400, detail="Advisors not enabled")
            items = svc.memory.get(platform, channel, user, limit=limit)
            # Convert dataclasses to serializable dicts
            return [{"role": i.role, "content": i.content, "timestamp": i.timestamp} for i in items]

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
            self._broadcast_message(WebSocketMessage(type=event_type, data={"message": details}))
        )


def create_app(
    *,
    config_manager: Config | None = None,
    state_manager: StateManager | None = None,
    model_manager: ModelManager | None = None,
    command_executor: CommandExecutor | None = None,
    no_auth: bool = False,
) -> FastAPI:
    """Convenience function to create a minimal FastAPI app for tests."""
    # Defer to the newer server.create_app to keep assembly consistent
    try:
        from .server import create_app as _create

        # Use an in-memory config to avoid external config.json affecting tests
        cfg = config_manager or Config(config_file="")
        sm = state_manager or StateManager(cfg)
        mm = model_manager or ModelManager(cfg)
        ce = command_executor or CommandExecutor(cfg, mm, sm)
        return _create(
            config_manager=cfg,
            state_manager=sm,
            model_manager=mm,
            command_executor=ce,
            no_auth=no_auth,
        )
    except Exception:
        # Fallback: construct locally
        cfg = config_manager or Config(config_file="")
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
