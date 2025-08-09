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
from typing import Any, Optional, Dict

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.advisors.service import AdvisorsService, AdvisorMessage, AdvisorReply

# Import our core modules from src package
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models for request/response validation
class SystemStatus(BaseModel):
    """System status response model."""

    status: str = Field(..., description="Overall system status")
    current_state: str = Field(..., description="Current operational state")
    active_models: list[str] = Field(..., description="List of loaded models")
    uptime: str = Field(..., description="System uptime")
    version: str = Field(default="0.2.0", description="Application version")


class StateChangeRequest(BaseModel):
    """State change request model."""

    state: str = Field(..., description="Target state", pattern="^(idle|computer|chatty)$")


class CommandRequest(BaseModel):
    """Command execution request model."""

    command: str = Field(..., description="Command name to execute")
    parameters: dict[str, Any] | None = Field(
        default=None, description="Optional command parameters"
    )


class CommandResponse(BaseModel):
    """Command execution response model."""

    success: bool = Field(..., description="Whether command executed successfully")
    message: str = Field(..., description="Execution result message")
    execution_time: float = Field(..., description="Execution time in milliseconds")


class StateInfo(BaseModel):
    """State information response model."""

    current_state: str = Field(..., description="Current operational state")
    active_models: list[str] = Field(..., description="List of active models")
    last_command: str | None = Field(default=None, description="Last detected command")
    timestamp: str = Field(..., description="Timestamp of last state change")


class WebSocketMessage(BaseModel):
    """WebSocket message model."""

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
        self.no_auth = no_auth
        self.start_time = time.time()
        self.last_command: str | None = None
        self.last_state_change = datetime.now()
        # Advisors service (optional)
        self.advisors_service = AdvisorsService(config=config_manager)

        # WebSocket connection management
        self.active_connections: set[WebSocket] = set()

        # Initialize FastAPI app
        self.app = self._create_app()

        # Setup state change callback
        self.state_manager.add_state_change_callback(self._on_state_change)

    def _create_app(self) -> FastAPI:
        """Create and configure FastAPI application."""
        app = FastAPI(
            title="ChattyCommander API",
            description="Voice command automation system with web interface",
            version="0.2.0",
            docs_url="/docs" if self.no_auth else None,
            redoc_url="/redoc" if self.no_auth else None,
        )

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"] if self.no_auth else ["http://localhost:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Register routes
        self._register_routes(app)

        # Serve static files if frontend exists
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
        """Register API routes."""

        @app.get("/api/v1/status", response_model=SystemStatus)
        async def get_status():
            """Get system status."""
            uptime_seconds = time.time() - self.start_time
            uptime_str = self._format_uptime(uptime_seconds)

            return SystemStatus(
                status="running",
                current_state=self.state_manager.current_state,
                active_models=self.state_manager.get_active_models(),
                uptime=uptime_str,
            )

        @app.get("/api/v1/config")
        async def get_config():
            """Get current configuration."""
            # Access config dict attribute for compatibility with tests/mocks
            return getattr(self.config_manager, "config", {})

        @app.put("/api/v1/config")
        async def update_config(config_data: dict[str, Any]):
            """Update configuration."""
            try:
                # Validate and update configuration; tolerate mocks that may not expose methods
                cfg = getattr(self.config_manager, "config", {})
                if isinstance(cfg, dict):
                    cfg.update(config_data)
                # Save if available (real implementation)
                save = getattr(self.config_manager, "save_config", None)
                if callable(save):
                    try:
                        save()
                    except TypeError:
                        # Some implementations may require passing the cfg
                        save(cfg)  # type: ignore[arg-type]
                return {"message": "Configuration updated successfully"}

                # Broadcast configuration change
                await self._broadcast_message(
                    WebSocketMessage(
                        type="config_updated",
                        data={"message": "Configuration updated successfully"},
                    )
                )

                return {"message": "Configuration updated successfully"}
            except Exception as e:
                logger.error(f"Failed to update configuration: {e}")
                raise HTTPException(
                    status_code=500, detail=str(e)
                )  # noqa: B904 - preserving current exception behavior

        @app.get("/api/v1/state", response_model=StateInfo)
        async def get_state():
            """Get current state information."""
            return StateInfo(
                current_state=self.state_manager.current_state,
                active_models=self.state_manager.get_active_models(),
                last_command=self.last_command,
                timestamp=self.last_state_change.isoformat(),
            )

        @app.post("/api/v1/state")
        async def change_state(request: StateChangeRequest):
            """Change system state."""
            try:
                old_state = self.state_manager.current_state
                self.state_manager.change_state(request.state)
                self.last_state_change = datetime.now()

                # Broadcast state change
                await self._broadcast_message(
                    WebSocketMessage(
                        type="state_change",
                        data={
                            "old_state": old_state,
                            "new_state": request.state,
                            "timestamp": self.last_state_change.isoformat(),
                        },
                    )
                )

                return {"message": f"State changed to {request.state}"}
            except Exception as e:
                logger.error(f"Failed to change state: {e}")
                raise HTTPException(
                    status_code=400, detail=str(e)
                )  # noqa: B904 - preserve current error handling

        @app.post("/api/v1/command", response_model=CommandResponse)
        async def execute_command(request: CommandRequest):
            """Execute a command programmatically."""
            start_time = time.time()

            try:
                # Check if command exists in configuration
                config_dict = getattr(self.config_manager, "config", {})
                model_actions = config_dict.get('model_actions', {}) if isinstance(config_dict, dict) else {}
                if request.command not in model_actions:
                    raise HTTPException(
                        status_code=404, detail=f"Command '{request.command}' not found"
                    )

                # Execute the command
                action = model_actions[request.command]
                success = False

                if 'keypress' in action:
                    # Delegate to CommandExecutor.execute_command to keep a single integration surface
                    success = bool(self.command_executor.execute_command(request.command))
                elif 'url' in action:
                    success = bool(self.command_executor.execute_command(request.command))

                execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                self.last_command = request.command

                # Broadcast command execution
                await self._broadcast_message(
                    WebSocketMessage(
                        type="command_executed",
                        data={
                            "command": request.command,
                            "success": success,
                            "execution_time": execution_time,
                            "parameters": request.parameters,
                        },
                    )
                )

                return CommandResponse(
                    success=bool(success),
                    message=(
                        "Command executed successfully" if success else "Command execution failed"
                    ),
                    execution_time=execution_time,
                )
            except HTTPException:
                raise
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(f"Command execution failed: {e}")
                return CommandResponse(
                    success=False,
                    message=f"Command execution failed: {str(e)}",
                    execution_time=execution_time,
                )
        class AdvisorInbound(BaseModel):
            platform: str
            channel: str
            user: str
            text: str
            username: Optional[str] = None
            metadata: Optional[Dict[str, Any]] = None

        class AdvisorOutbound(BaseModel):
            reply: str
            context_key: str
            persona_id: str
            model: str
            api_mode: str


        class ContextStats(BaseModel):
            total_contexts: int
            platform_distribution: Dict[str, int]
            persona_distribution: Dict[str, int]
            persistence_enabled: bool
            persistence_path: str

        @app.post("/api/v1/advisors/message", response_model=AdvisorOutbound)
        async def advisor_message(message: AdvisorInbound):
            """Process a message through the advisor service."""
            try:
                reply = self.advisors_service.handle_message(
                    AdvisorMessage(
                        platform=message.platform,
                        channel=message.channel,
                        user=message.user,
                        text=message.text,
                        username=message.username,
                        metadata=message.metadata
                    )
                )
                return AdvisorOutbound(
                    reply=reply.reply,
                    context_key=reply.context_key,
                    persona_id=reply.persona_id,
                    model=reply.model,
                    api_mode=reply.api_mode
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))


        @app.post("/api/v1/advisors/context/switch")
        async def switch_persona(context_key: str, persona_id: str):
            """Switch persona for a specific context."""
            try:
                success = self.advisors_service.switch_persona(context_key, persona_id)
                if not success:
                    raise HTTPException(status_code=400, detail="Invalid persona or context")
                return {"success": True, "context_key": context_key, "persona_id": persona_id}
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))


        @app.get("/api/v1/advisors/context/stats", response_model=ContextStats)
        async def get_context_stats():
            """Get statistics about current contexts."""
            try:
                stats = self.advisors_service.get_context_stats()
                return ContextStats(**stats)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))


        @app.delete("/api/v1/advisors/context/{context_key}")
        async def clear_context(context_key: str):
            """Clear a specific context."""
            try:
                success = self.advisors_service.clear_context(context_key)
                if not success:
                    raise HTTPException(status_code=404, detail="Context not found")
                return {"success": True, "context_key": context_key}
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        class AdvisorMemoryItem(BaseModel):
            role: str
            content: str
            timestamp: str

        @app.get("/api/v1/advisors/memory", response_model=list[AdvisorMemoryItem])
        async def advisors_memory(platform: str, channel: str, user: str, limit: int = 20):
            if not getattr(self.config_manager, "advisors", {}).get("enabled", False):
                raise HTTPException(status_code=400, detail="Advisors feature disabled")
            items = self.advisors_service.memory.get(platform, channel, user, limit)
            return [AdvisorMemoryItem(role=i.role, content=i.content, timestamp=i.timestamp) for i in items]

        @app.delete("/api/v1/advisors/memory")
        async def advisors_memory_clear(platform: str, channel: str, user: str):
            if not getattr(self.config_manager, "advisors", {}).get("enabled", False):
                raise HTTPException(status_code=400, detail="Advisors feature disabled")
            count = self.advisors_service.memory.clear(platform, channel, user)
            return {"cleared": count}

        from fastapi import Request

        @app.post("/bridge/event")
        async def bridge_event(event: dict[str, Any], request: Request):
            # Auth: shared secret header must match config token
            token_expected = (
                getattr(self.config_manager, "advisors", {})
                .get("bridge", {})
                .get("token", "")
            )
            token_header = request.headers.get("X-Bridge-Token", "")
            if not token_expected or token_header != token_expected:
                raise HTTPException(status_code=401, detail="Unauthorized bridge request")

            # Minimal contract: platform, channel, user, text
            try:
                msg = AdvisorMessage(
                    platform=event.get("platform", "unknown"),
                    channel=event.get("channel", ""),
                    user=event.get("user", ""),
                    text=event.get("text", ""),
                    username=event.get("username"),
                    metadata=event.get("meta")
                )
                reply = self.advisors_service.handle_message(msg)
                return {"ok": True, "reply": {"text": reply.reply, "meta": {}}}
            except Exception as e:
                logger.error(f"Bridge event processing failed: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.active_connections.add(websocket)

            try:
                # Send initial status
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "connection_established",
                            "data": {
                                "current_state": self.state_manager.current_state,
                                "active_models": self.state_manager.get_active_models(),
                                "timestamp": datetime.now().isoformat(),
                            },
                        }
                    )
                )

                # Keep connection alive and handle incoming messages
                while True:
                    try:
                        # Wait for messages (with timeout to allow periodic checks)
                        data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                        message = json.loads(data)

                        # Handle client messages if needed
                        if message.get('type') == 'ping':
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "pong",
                                        "data": {"timestamp": datetime.now().isoformat()},
                                    }
                                )
                            )

                    except TimeoutError:
                        # Send periodic heartbeat
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "heartbeat",
                                    "data": {"timestamp": datetime.now().isoformat()},
                                }
                            )
                        )

            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                self.active_connections.discard(websocket)

        @app.get("/api/v1/health")
        async def health_check():
            """Simple health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime": self._format_uptime(time.time() - self.start_time),
            }

    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format."""
        days, remainder = divmod(int(seconds), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        else:
            return f"{hours}h {minutes}m {seconds}s"

    async def _broadcast_message(self, message: WebSocketMessage) -> None:
        """Broadcast message to all connected WebSocket clients."""
        if not self.active_connections:
            return

        message_json = message.model_dump()
        message_text = json.dumps(message_json)

        # Send to all connected clients
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket client: {e}")
                disconnected.add(connection)

        # Remove disconnected clients
        self.active_connections -= disconnected

    def _on_state_change(self, old_state: str, new_state: str) -> None:
        """Callback for state changes."""
        self.last_state_change = datetime.now()

        # Schedule broadcast (since this might be called from a different thread)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(
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
        except RuntimeError:
            # No event loop running, skip broadcast
            pass

    def on_command_detected(self, command: str, confidence: float = 1.0) -> None:
        """Handle command detection events."""
        self.last_command = command

        # Schedule broadcast
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(
                    self._broadcast_message(
                        WebSocketMessage(
                            type="command_detected",
                            data={
                                "command": command,
                                "confidence": confidence,
                                "timestamp": datetime.now().isoformat(),
                            },
                        )
                    )
                )
        except RuntimeError:
            # No event loop running, skip broadcast
            pass

    def on_system_event(self, event: str, details: str) -> None:
        """Handle system events."""
        # Schedule broadcast
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(
                    self._broadcast_message(
                        WebSocketMessage(
                            type="system_event",
                            data={
                                "event": event,
                                "details": details,
                                "timestamp": datetime.now().isoformat(),
                            },
                        )
                    )
                )
        except RuntimeError:
            # No event loop running, skip broadcast
            pass

    def run(self, host: str = "0.0.0.0", port: int = 8100, log_level: str = "info") -> None:
        """Run the web server."""
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
    """Factory function to create web server instance."""
    return WebModeServer(
        config_manager=config_manager,
        state_manager=state_manager,
        model_manager=model_manager,
        command_executor=command_executor,
        no_auth=no_auth,
    )


if __name__ == "__main__":
    # This allows running the web server standalone for testing
    from chatty_commander.app.command_executor import CommandExecutor
    from chatty_commander.app.config import Config
    from chatty_commander.app.model_manager import ModelManager
    from chatty_commander.app.state_manager import StateManager

    # Initialize components using current constructor signatures
    config_manager = Config()
    state_manager = StateManager()
    model_manager = ModelManager(config_manager)
    command_executor = CommandExecutor(config_manager, model_manager, state_manager)

    # Create and run server
    server = create_web_server(
        config_manager=config_manager,
        state_manager=state_manager,
        model_manager=model_manager,
        command_executor=command_executor,
        no_auth=True,
    )

    server.run()


# Minimal, stateless FastAPI app factory for tests
from fastapi import FastAPI


def create_app(no_auth: bool = True) -> FastAPI:
    app = FastAPI(
        title="ChattyCommander API",
        version="0.2.0",
        docs_url="/docs" if no_auth else None,
        redoc_url="/redoc" if no_auth else None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if no_auth else ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    @app.get("/api/v1/health")
    async def health_check():
        return {"status": "healthy"}
    return app
