"""
WebSocket routes for Avatar UI to receive agent state updates.

This endpoint broadcasts agent thinking/responding states and supports minimal
control messages from the avatar client.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List, Callable, Optional
import json
import logging

from ...avatars.thinking_state import get_thinking_manager, AgentStateInfo

logger = logging.getLogger(__name__)

router = APIRouter()


class AvatarWSConnectionManager:
    def __init__(self, theme_resolver: Optional[Callable[[str], str]] = None):
        self.active_connections: List[WebSocket] = []
        # optional persona -> theme resolver
        self.theme_resolver = theme_resolver
        # Track the manager instance we've registered with to survive resets in tests
        self._registered_manager = None
        # Register on current manager
        self._ensure_manager()

    def _ensure_manager(self):
        mgr = get_thinking_manager()
        if mgr is not self._registered_manager:
            # remove from old, if any
            try:
                if self._registered_manager is not None:
                    self._registered_manager.remove_broadcast_callback(self.broadcast_state_change)
            except Exception:
                pass
            try:
                mgr.add_broadcast_callback(self.broadcast_state_change)
            except Exception:
                pass
            self._registered_manager = mgr
        return mgr

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # ensure we are bound to the current manager (handles reset in tests)
        mgr = self._ensure_manager()
        # send snapshot of current states (enrich with theme if available)
        data: Dict[str, Any] = {}
        for agent_id, info in mgr.get_all_states().items():
            d = info.to_dict()
            if self.theme_resolver and d.get("persona_id"):
                try:
                    d["theme"] = self.theme_resolver(d["persona_id"])  # type: ignore[arg-type]
                except Exception:
                    pass
            data[agent_id] = d
        snapshot = {"type": "agent_states_snapshot", "data": data}
        try:
            await websocket.send_text(json.dumps(snapshot))
        except Exception as e:
            logger.error(f"Failed to send snapshot to avatar client: {e}")

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send to avatar client: {e}")

    def broadcast_state_change(self, message: Dict[str, Any]) -> None:
        # Optionally enrich with theme based on persona_id
        try:
            data = message.get("data") if isinstance(message, dict) else None
            persona_id = data.get("persona_id") if isinstance(data, dict) else None
            if self.theme_resolver and persona_id:
                try:
                    data["theme"] = self.theme_resolver(persona_id)  # type: ignore[arg-type]
                except Exception:
                    pass
        except Exception:
            pass
        # schedule async broadcast without blocking the caller
        import anyio

        async def _broadcast():
            dead: List[WebSocket] = []
            for connection in list(self.active_connections):
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    dead.append(connection)
            for d in dead:
                self.disconnect(d)

        try:
            anyio.from_thread.run(_broadcast)
        except RuntimeError:
            # Not in a thread capable context; best effort
            import asyncio
            asyncio.create_task(_broadcast())


manager = AvatarWSConnectionManager()


@router.websocket("/avatar/ws")
async def avatar_ws_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Basic protocol: expect JSON messages with type and data
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                continue
            # Handle control messages if needed (e.g., avatar ready)
            msg_type = msg.get("type")
            if msg_type == "avatar_ready":
                await manager.send_personal_message({"type": "ack", "data": "ok"}, websocket)
            # Future: map avatar_id to agent_id etc
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Avatar WS error: {e}")
        manager.disconnect(websocket)