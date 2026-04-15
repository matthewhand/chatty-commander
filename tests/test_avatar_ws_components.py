"""Comprehensive tests for Avatar WebSocket components and audio queue."""

import asyncio
from typing import Any

from chatty_commander.web.routes.avatar_ws import (
    AvatarAudioQueue,
    AvatarWSConnectionManager,
)


class StubWebSocket:
    """Minimal WebSocket stub for testing."""

    def __init__(self) -> None:
        self.messages: list[str] = []
        self._accepted = False
        self._closed = False

    async def accept(self) -> None:
        self._accepted = True

    async def send_text(self, message: str) -> None:
        if self._closed:
            raise RuntimeError("WebSocket is closed")
        self.messages.append(message)

    async def close(self) -> None:
        self._closed = True


class StubThinkingManager:
    """Stub for ThinkingStateManager."""

    def __init__(self) -> None:
        self.states: dict[str, Any] = {}

    def get_all_states(self) -> dict[str, Any]:
        return self.states.copy()

    def add_broadcast_callback(self, callback: Any) -> None:
        pass

    def remove_broadcast_callback(self, callback: Any) -> None:
        pass


class TestAvatarWSConnectionManager:
    """Tests for AvatarWSConnectionManager."""

    def test_initial_state(self) -> None:
        """Test manager initializes with no connections."""
        manager = AvatarWSConnectionManager()
        assert manager.active_connections == []

    def test_connect_adds_websocket(self) -> None:
        """Test that connect adds websocket to active connections."""
        manager = AvatarWSConnectionManager()
        ws = StubWebSocket()

        async def run():
            await manager.connect(ws)

        asyncio.run(run())
        assert ws in manager.active_connections
        assert ws._accepted

    def test_disconnect_removes_websocket(self) -> None:
        """Test that disconnect removes websocket from active connections."""
        manager = AvatarWSConnectionManager()
        ws = StubWebSocket()

        async def run():
            await manager.connect(ws)
            assert ws in manager.active_connections
            manager.disconnect(ws)
            assert ws not in manager.active_connections

        asyncio.run(run())

    def test_broadcast_state_change_sends_to_all(self) -> None:
        """Test broadcast sends message to all connections."""
        manager = AvatarWSConnectionManager()
        ws1 = StubWebSocket()
        ws2 = StubWebSocket()

        async def run():
            await manager.connect(ws1)
            await manager.connect(ws2)
            manager.broadcast_state_change({"type": "test", "data": {}})
            await asyncio.sleep(0.01)  # Allow async tasks to complete

        asyncio.run(run())
        assert len(ws1.messages) == 2  # Initial state + broadcast
        assert len(ws2.messages) == 2

    def test_broadcast_removes_dead_connections(self) -> None:
        """Test that failed sends remove connection."""
        manager = AvatarWSConnectionManager()
        ws1 = StubWebSocket()
        ws2 = StubWebSocket()

        async def run():
            await manager.connect(ws1)
            await manager.connect(ws2)
            ws2._closed = True  # Simulate dead connection
            manager.broadcast_state_change({"type": "test", "data": {}})
            await asyncio.sleep(0.01)

        asyncio.run(run())
        assert ws1 in manager.active_connections
        assert ws2 not in manager.active_connections

    def test_theme_resolver_enriches_messages(self) -> None:
        """Test that theme resolver adds theme to messages."""
        calls: list[str] = []

        def theme_resolver(persona_id: str) -> str:
            calls.append(persona_id)
            return "dark"

        manager = AvatarWSConnectionManager(theme_resolver=theme_resolver)
        ws = StubWebSocket()

        async def run():
            await manager.connect(ws)
            manager.broadcast_state_change({
                "type": "test",
                "data": {"persona_id": "advisor"},
            })
            await asyncio.sleep(0.01)

        asyncio.run(run())
        # Check that theme_resolver was called
        # May be called during initial snapshot too
        assert len(calls) >= 1


class TestAvatarAudioQueue:
    """Tests for AvatarAudioQueue."""

    def test_enqueue_processes_message(self) -> None:
        """Test that enqueued messages are processed."""
        manager = AvatarWSConnectionManager()
        queue = AvatarAudioQueue(manager)

        async def run():
            await queue.enqueue("agent-1", "Hello", b"audio_data")
            await queue.queue.join()
            await asyncio.sleep(0.01)

        asyncio.run(run())
        assert queue.queue.empty()

    def test_enqueue_sequences_messages(self) -> None:
        """Test that multiple messages are processed sequentially."""
        manager = AvatarWSConnectionManager()
        queue = AvatarAudioQueue(manager)
        events: list[dict] = []

        def capture(msg: dict) -> None:
            events.append(msg)

        manager.broadcast_state_change = capture

        async def run():
            # Use very short audio to speed up test
            await queue.enqueue("a", "msg1", b"xx")  # 2 bytes = ~2ms
            await queue.enqueue("a", "msg2", b"xx")
            await queue.queue.join()
            await asyncio.sleep(0.01)

        asyncio.run(run())
        # Should have start and end for each message
        starts = [e for e in events if e.get("type") == "avatar_audio_start"]
        assert len(starts) == 2
        assert starts[0]["data"]["message"] == "msg1"
        assert starts[1]["data"]["message"] == "msg2"

    def test_interrupt_cancels_current_playback(self) -> None:
        """Test that interrupt cancels current playback."""
        manager = AvatarWSConnectionManager()
        queue = AvatarAudioQueue(manager)
        events: list[dict] = []

        def capture(msg: dict) -> None:
            events.append(msg)

        manager.broadcast_state_change = capture

        async def slow_play(audio: bytes | None) -> None:
            await asyncio.sleep(1.0)  # Long playback

        queue._play_audio = slow_play  # type: ignore

        async def run():
            await queue.enqueue("agent", "long", b"x")
            await asyncio.sleep(0.01)  # Let playback start
            await queue.interrupt("agent", "priority", b"y")
            await queue.queue.join()
            await asyncio.sleep(0.01)

        asyncio.run(run())
        # Should see interrupted flag
        interrupted = any(
            e.get("data", {}).get("interrupted")
            for e in events
            if e.get("type") == "avatar_audio_end"
        )
        assert interrupted

    def test_interrupt_clears_pending_messages(self) -> None:
        """Test that interrupt clears queue."""
        manager = AvatarWSConnectionManager()
        queue = AvatarAudioQueue(manager)
        events: list[dict] = []

        def capture(msg: dict) -> None:
            events.append(msg)

        manager.broadcast_state_change = capture

        async def run():
            # Queue multiple messages
            await queue.enqueue("a", "to-clear-1", b"x")
            await queue.enqueue("a", "to-clear-2", b"x")
            await queue.enqueue("a", "to-clear-3", b"x")
            # Interrupt before processing
            await queue.interrupt("a", "priority", b"y")
            await queue.queue.join()
            await asyncio.sleep(0.01)

        asyncio.run(run())
        # Should only see the priority message
        starts = [e for e in events if e.get("type") == "avatar_audio_start"]
        messages = [s["data"]["message"] for s in starts]
        assert "priority" in messages
        assert "to-clear-1" not in messages

    def test_is_speaking_property(self) -> None:
        """Test is_speaking reflects playback state."""
        manager = AvatarWSConnectionManager()
        queue = AvatarAudioQueue(manager)
        speaking_states: list[bool] = []

        async def record_and_play(audio: bytes | None) -> None:
            speaking_states.append(queue.is_speaking)
            await asyncio.sleep(0.05)
            speaking_states.append(queue.is_speaking)

        queue._play_audio = record_and_play  # type: ignore

        async def run():
            assert queue.is_speaking is False
            await queue.enqueue("a", "test", b"x")
            await queue.queue.join()
            await asyncio.sleep(0.01)

        asyncio.run(run())
        # During playback, should be True
        assert any(speaking_states)

    def test_empty_audio_plays_nothing(self) -> None:
        """Test that None audio is handled without error."""
        manager = AvatarWSConnectionManager()
        queue = AvatarAudioQueue(manager)

        async def run():
            await queue.enqueue("a", "text_only", None)
            await queue.queue.join()

        # Should not raise
        asyncio.run(run())

    def test_multiple_agents_share_queue(self) -> None:
        """Test that multiple agents can enqueue messages."""
        manager = AvatarWSConnectionManager()
        queue = AvatarAudioQueue(manager)
        events: list[dict] = []

        def capture(msg: dict) -> None:
            events.append(msg)

        manager.broadcast_state_change = capture

        async def run():
            await queue.enqueue("agent-1", "hello", b"x")
            await queue.enqueue("agent-2", "world", b"x")
            await queue.queue.join()
            await asyncio.sleep(0.01)

        asyncio.run(run())
        starts = [e for e in events if e.get("type") == "avatar_audio_start"]
        agents = {s["data"]["agent_id"] for s in starts}
        assert agents == {"agent-1", "agent-2"}


class TestAvatarAudioQueueEdgeCases:
    """Edge case tests for AvatarAudioQueue."""

    def test_interrupt_when_idle(self) -> None:
        """Test interrupt works when queue is idle."""
        manager = AvatarWSConnectionManager()
        queue = AvatarAudioQueue(manager)

        async def run():
            # Interrupt on idle queue should not raise
            await queue.interrupt("a", "priority", b"x")
            await queue.queue.join()
            await asyncio.sleep(0.01)

        asyncio.run(run())

    def test_enqueue_after_interrupt(self) -> None:
        """Test that queue works after interrupt."""
        manager = AvatarWSConnectionManager()
        queue = AvatarAudioQueue(manager)

        async def run():
            await queue.interrupt("a", "p1", b"x")
            await queue.queue.join()
            await queue.enqueue("a", "p2", b"x")
            await queue.queue.join()
            await asyncio.sleep(0.01)

        # Should not raise or hang
        asyncio.run(run())

    def test_concurrent_enqueues(self) -> None:
        """Test that concurrent enqueue operations work."""
        manager = AvatarWSConnectionManager()
        queue = AvatarAudioQueue(manager)

        async def run():
            # Enqueue multiple items concurrently
            tasks = [
                queue.enqueue("a", f"msg{i}", b"x")
                for i in range(5)
            ]
            await asyncio.gather(*tasks)
            await queue.queue.join()
            await asyncio.sleep(0.01)

        asyncio.run(run())
        assert queue.queue.empty()
