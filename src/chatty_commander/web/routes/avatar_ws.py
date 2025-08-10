"""
WebSocket routes for Avatar UI to receive agent state updates.

This endpoint broadcasts agent thinking/responding states and supports minimal
control messages from the avatar client.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List
import json
import logging

from ...avatars.thinking_state import get_thinking_manager, AgentStateInfo

logger = logging.getLogger(__name__)

router = APIRouter()


class AvatarWSConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # register broadcast callback
        self.thinking_manager = get_thinking_manager()
        self.thinking_manager.add_broadcast_callback(self.broadcast_state_change)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # send snapshot of current states
        snapshot = {
            "type": "agent_states_snapshot",
            "data": {agent_id: info.to_dict() for agent_id, info in self.thinking_manager.get_all_states().items()}
        }
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