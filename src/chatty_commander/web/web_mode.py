#!/usr/bin/env python3
"""
web_mode.py

FastAPI web server implementation for ChattyCommander.
Provides REST API endpoints and WebSocket support for web interface.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Security,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.utils.logger import setup_logger

logger = logging.getLogger(__name__)


class SystemStatus(BaseModel):
    status: str
    current_state: str
    active_models: list[str]
    uptime: str
    version: str = Field(default="0.2.0")


class StateChangeRequest(BaseModel):
    state: str = Field(..., pattern="^(idle|computer|chatty)$")


class CommandRequest(BaseModel):
    command: str
    parameters: dict[str, Any] | None = None


class CommandResponse(BaseModel):
    success: bool
    message: str
    execution_time: float


class StateInfo(BaseModel):
    current_state: str
    active_models: list[str]
    last_command: str | None
    timestamp: str


class WebSocketMessage(BaseModel):
    type: str
    data: dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class WebModeServer:
    def __init__(
        self,
        config_manager: Config,
        state_manager: StateManager,
        model_manager: ModelManager,
        command_executor: CommandExecutor,
        no_auth: bool = False,
    ) -> None:
        global logger
        logger = setup_logger(__name__, config=config_manager)

        self.config_manager = config_manager
        self.state_manager = state_manager
        self.model_manager = model_manager
        self.command_executor = command_executor
        self.no_auth = no_auth
        self._expected_api_key = getattr(self.config_manager, "auth", {}).get("api_key", "")
        self.start_time = time.time()
        self.last_command: str | None = None
        self.last_state_change = datetime.now()

        self.active_connections: set[WebSocket] = set()
        self.app = self._create_app()
        self.state_manager.add_state_change_callback(self._on_state_change)

    async def _require_api_key(self, api_key: str = Security(APIKeyHeader(name="X-API-Key", auto_error=False))):
        if self.no_auth:
            return
        expected = self._expected_api_key
        if not expected or api_key != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")

    def _create_app(self) -> FastAPI:
        app = FastAPI(
            title="ChattyCommander API",
            description="Voice command automation system with web interface",
            version="0.2.0",
            docs_url="/docs" if self.no_auth else None,
            redoc_url="/redoc" if self.no_auth else None,
        )

        origins = ["*"] if self.no_auth else getattr(self.config_manager, "auth", {}).get("allowed_origins", ["http://localhost:3000"])
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._register_routes(app)

        frontend_path = Path("webui/frontend/dist")
        if frontend_path.exists():
            app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

            @app.get("/", response_class=HTMLResponse)
            async def serve_frontend():
                index_file = frontend_path / "index.html"
                if index_file.exists():
                    return FileResponse(str(index_file))
                return HTMLResponse(
                    "<h1>ChattyCommander</h1><p>Frontend not built. Run <code>npm run build</code> in webui/frontend/</p>"
                )

        return app

    def _register_routes(self, app: FastAPI) -> None:
        deps = [] if self.no_auth else [Depends(self._require_api_key)]

        @app.get("/api/v1/status", response_model=SystemStatus, dependencies=deps)
        async def get_status():
            uptime_seconds = time.time() - self.start_time
            return SystemStatus(
                status="running",
                current_state=self.state_manager.current_state,
                active_models=self.state_manager.get_active_models(),
                uptime=self._format_uptime(uptime_seconds),
            )

        @app.get("/api/v1/config", dependencies=deps)
        async def get_config():
            return getattr(self.config_manager, "config", {})

        @app.put("/api/v1/config", dependencies=deps)
        async def update_config(config_data: dict[str, Any]):
            try:
                cfg = getattr(self.config_manager, "config", {})
                if isinstance(cfg, dict):
                    cfg.update(config_data)
                save = getattr(self.config_manager, "save_config", None)
                if callable(save):
                    try:
                        save()
                    except TypeError:
                        save(cfg)  # type: ignore[arg-type]
                await self._broadcast_message(WebSocketMessage(type="config_updated", data={"message": "Configuration updated successfully"}))
                return {"message": "Configuration updated successfully"}
            except Exception as e:
                logger.error(f"Failed to update configuration: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/api/v1/state", response_model=StateInfo, dependencies=deps)
        async def get_state():
            return StateInfo(
                current_state=self.state_manager.current_state,
                active_models=self.state_manager.get_active_models(),
                last_command=self.last_command,
                timestamp=self.last_state_change.isoformat(),
            )

        @app.post("/api/v1/state", dependencies=deps)
        async def change_state(request: StateChangeRequest):
            try:
                old_state = self.state_manager.current_state
                self.state_manager.change_state(request.state)
                self.last_state_change = datetime.now()
                await self._broadcast_message(
                    WebSocketMessage(
                        type="state_change",
                        data={"old_state": old_state, "new_state": request.state, "timestamp": self.last_state_change.isoformat()},
                    )
                )
                return {"message": f"State changed to {request.state}"}
            except Exception as e:
                logger.error(f"Failed to change state: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @app.post("/api/v1/command", response_model=CommandResponse, dependencies=deps)
        async def execute_command(request: CommandRequest):
            start_time = time.time()
            try:
                config_dict = getattr(self.config_manager, "config", {})
                model_actions = config_dict.get("model_actions", {}) if isinstance(config_dict, dict) else {}
                if request.command not in model_actions:
                    raise HTTPException(status_code=404, detail=f"Command '{request.command}' not found")

                success = bool(self.command_executor.execute_command(request.command))
                execution_time = (time.time() - start_time) * 1000
                self.last_command = request.command
                await self._broadcast_message(
                    WebSocketMessage(
                        type="command_executed",
                        data={"command": request.command, "success": success, "execution_time": execution_time, "parameters": request.parameters},
                    )
                )
                return CommandResponse(success=success, message=("Command executed successfully" if success else "Command execution failed"), execution_time=execution_time)
            except HTTPException:
                raise
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(f"Command execution failed: {e}")
                return CommandResponse(success=False, message=f"Command execution failed: {str(e)}", execution_time=execution_time)

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            if not self.no_auth:
                api_key = websocket.headers.get("x-api-key") or websocket.headers.get("X-API-Key")
                if not self._expected_api_key or api_key != self._expected_api_key:
                    await websocket.close(code=1008)
                    return
            await websocket.accept()
            self.active_connections.add(websocket)
            try:
                await websocket.send_text(json.dumps({"type": "connection_established", "timestamp": datetime.now().isoformat()}))
                while True:
                    try:
                        data = await websocket.receive_text()
                        if data:
                            await websocket.send_text(json.dumps({"type": "echo", "data": data}))
                    except WebSocketDisconnect:
                        break
            finally:
                self.active_connections.discard(websocket)

    def _format_uptime(self, seconds: float) -> str:
        seconds = int(seconds)
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        if d:
            return f"{d}d {h}h {m}m {s}s"
        return f"{h}h {m}m {s}s"

    async def _broadcast_message(self, message: WebSocketMessage) -> None:
        payload = message.model_dump()
        dead: list[WebSocket] = []
        for ws in list(self.active_connections):
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                # Mark for removal and continue with others
                dead.append(ws)
        for ws in dead:
            self.active_connections.discard(ws)

    def _on_state_change(self, old: str, new: str) -> None:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(
                    self._broadcast_message(
                        WebSocketMessage(type="state_change", data={"old_state": old, "new_state": new, "timestamp": datetime.now().isoformat()})
                    )
                )
        except RuntimeError:
            pass

    def on_command_detected(self, command: str, confidence: float | None = None) -> None:
        self.last_command = command
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(
                    self._broadcast_message(
                        WebSocketMessage(type="command_detected", data={"command": command, "confidence": confidence})
                    )
                )
        except RuntimeError:
            pass

    def on_system_event(self, event: str, details: str) -> None:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(
                    self._broadcast_message(
                        WebSocketMessage(type="system_event", data={"event": event, "details": details, "timestamp": datetime.now().isoformat()})
                    )
                )
        except RuntimeError:
            pass

    def run(self, host: str = "0.0.0.0", port: int = 8100, log_level: str = "info") -> None:
        logger.info(f"🚀 Starting ChattyCommander web server on {host}:{port}")
        logger.info(f"📖 API documentation: http://{host}:{port}/docs")
        logger.info(f"🔧 Authentication: {'Disabled' if self.no_auth else 'Enabled'}")
        uvicorn.run(self.app, host=host, port=port, log_level=log_level, access_log=True)


def create_web_server(
    config_manager: Config,
    state_manager: StateManager,
    model_manager: ModelManager,
    command_executor: CommandExecutor,
    no_auth: bool = False,
) -> WebModeServer:
    return WebModeServer(config_manager, state_manager, model_manager, command_executor, no_auth=no_auth)


if __name__ == "__main__":
    config_manager = Config()
    state_manager = StateManager()
    model_manager = ModelManager(config_manager)
    command_executor = CommandExecutor(config_manager, model_manager, state_manager)
    server = create_web_server(config_manager, state_manager, model_manager, command_executor, no_auth=True)
    server.run(host="0.0.0.0", port=8100, log_level="info")

