"""
WebSocket routes for Avatar UI to receive agent state updates.

This endpoint broadcasts agent thinking/responding states and supports minimal
control messages from the avatar client.
"""

import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...avatars.thinking_state import get_thinking_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class AvatarWSConnectionManager:
    def __init__(self, theme_resolver: Callable[[str], str] | None = None):
        self.active_connections: list[WebSocket] = []
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
        data: dict[str, Any] = {}
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

    async def send_personal_message(self, message: dict[str, Any], websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send to avatar client: {e}")

    def broadcast_state_change(self, message: dict[str, Any]) -> None:
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

        async def _broadcast():
            dead: list[WebSocket] = []
            for connection in list(self.active_connections):
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    dead.append(connection)
            for d in dead:
                self.disconnect(d)

        # Schedule or run the coroutine safely depending on context
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_broadcast())
        except RuntimeError:
            # No running loop in this thread; run synchronously
            try:
                asyncio.run(_broadcast())
            except RuntimeError:
                # If already in an event loop in a different framework context, fall back to task creation
                loop = asyncio.get_event_loop()
                loop.create_task(_broadcast())


manager = AvatarWSConnectionManager()


class AvatarAudioQueue:
    """Queue managing sequential avatar speech playback.

    Messages with optional audio are enqueued. Only one message is played at a
    time; additional messages wait in the queue.  The queue broadcasts start/end
    events through ``AvatarWSConnectionManager`` so connected avatar clients can
    update their state.

    An interrupt API is provided to clear pending messages and immediately play
    a high priority one (useful for alerts).
    """

    def __init__(self, ws_manager: AvatarWSConnectionManager) -> None:
        self.manager = ws_manager
        self.queue: asyncio.Queue[tuple[str, str, bytes | None]] = asyncio.Queue()
        self._processor_task: asyncio.Task | None = None
        self._current_play_task: asyncio.Task | None = None

    @property
    def is_speaking(self) -> bool:
        """Return ``True`` if audio is currently being played."""

        return self._current_play_task is not None and not self._current_play_task.done()

    async def _play_audio(self, audio: bytes | None) -> None:
        """Placeholder for audio playback.

        In production this would stream audio to an output device. For testing
        we simply sleep for a duration based on the audio length if provided.
        """

        if audio:
            # Rough heuristic: 1000 bytes ~= 1 second
            await asyncio.sleep(max(len(audio) / 1000.0, 0))
        else:
            await asyncio.sleep(0)

    async def _process(self) -> None:
        while not self.queue.empty():
            agent_id, message, audio = await self.queue.get()
            start = {
                "type": "avatar_audio_start",
                "data": {"agent_id": agent_id, "message": message},
            }
            self.manager.broadcast_state_change(start)
            try:
                self._current_play_task = asyncio.create_task(self._play_audio(audio))
                await self._current_play_task
            except asyncio.CancelledError:
                end = {
                    "type": "avatar_audio_end",
                    "data": {"agent_id": agent_id, "interrupted": True},
                }
                self.manager.broadcast_state_change(end)
            else:
                end = {
                    "type": "avatar_audio_end",
                    "data": {"agent_id": agent_id},
                }
                self.manager.broadcast_state_change(end)
            finally:
                self._current_play_task = None
                self.queue.task_done()

        self._processor_task = None

    def _ensure_processor(self) -> None:
        if self._processor_task is None or self._processor_task.done():
            try:
                loop = asyncio.get_running_loop()
                self._processor_task = loop.create_task(self._process())
            except RuntimeError:
                asyncio.run(self._process())

    async def enqueue(self, agent_id: str, message: str, audio: bytes | None = None) -> None:
        """Add a message to the queue for playback."""

        await self.queue.put((agent_id, message, audio))
        self._ensure_processor()

    async def interrupt(self, agent_id: str, message: str, audio: bytes | None = None) -> None:
        """Interrupt current playback and play a priority message immediately."""

        # Clear any pending messages
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except asyncio.QueueEmpty:
                break

        # Cancel currently playing audio
        if self._current_play_task and not self._current_play_task.done():
            self._current_play_task.cancel()
            try:
                await self._current_play_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

        # Queue the priority message and ensure processor running
        await self.queue.put((agent_id, message, audio))
        self._ensure_processor()


# Global audio queue instance
audio_queue = AvatarAudioQueue(manager)


async def queue_avatar_message(agent_id: str, message: str, audio: bytes | None = None) -> None:
    """Public helper to queue avatar speech."""

    await audio_queue.enqueue(agent_id, message, audio)


async def interrupt_avatar_queue(agent_id: str, message: str, audio: bytes | None = None) -> None:
    """Public helper to interrupt current avatar speech with a priority message."""

    await audio_queue.interrupt(agent_id, message, audio)


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
