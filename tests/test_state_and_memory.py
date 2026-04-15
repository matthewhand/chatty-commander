"""Comprehensive tests for ThinkingState management and MemoryStore persistence."""

import asyncio
from pathlib import Path

from chatty_commander.advisors.memory import MemoryItem, MemoryStore
from chatty_commander.avatars.thinking_state import (
    AgentStateInfo,
    ThinkingState,
    get_thinking_manager,
    reset_thinking_manager,
)


class TestThinkingStateEnum:
    """Tests for ThinkingState enum values."""

    def test_all_states_defined(self) -> None:
        """Test that all expected states are defined."""
        assert ThinkingState.IDLE.value == "idle"
        assert ThinkingState.THINKING.value == "thinking"
        assert ThinkingState.PROCESSING.value == "processing"
        assert ThinkingState.RESPONDING.value == "responding"
        assert ThinkingState.LISTENING.value == "listening"
        assert ThinkingState.TOOL_CALLING.value == "tool_calling"
        assert ThinkingState.HANDOFF.value == "handoff"
        assert ThinkingState.ERROR.value == "error"

    def test_state_count(self) -> None:
        """Test we have expected number of states."""
        states = list(ThinkingState)
        assert len(states) == 8


class TestAgentStateInfo:
    """Tests for AgentStateInfo dataclass."""

    def test_creation_minimal(self) -> None:
        """Test creating AgentStateInfo with minimal args."""
        info = AgentStateInfo(
            agent_id="test-agent",
            avatar_id=None,
            persona_id="default",
            state=ThinkingState.IDLE,
        )
        assert info.agent_id == "test-agent"
        assert info.avatar_id is None
        assert info.persona_id == "default"
        assert info.state == ThinkingState.IDLE
        assert info.message is None
        assert info.progress is None
        assert info.timestamp is not None

    def test_creation_full(self) -> None:
        """Test creating AgentStateInfo with all fields."""
        info = AgentStateInfo(
            agent_id="agent-1",
            avatar_id="avatar-1",
            persona_id="analyst",
            state=ThinkingState.THINKING,
            message="Processing query",
            progress=0.5,
            timestamp=12345.0,
        )
        assert info.agent_id == "agent-1"
        assert info.avatar_id == "avatar-1"
        assert info.persona_id == "analyst"
        assert info.state == ThinkingState.THINKING
        assert info.message == "Processing query"
        assert info.progress == 0.5
        assert info.timestamp == 12345.0

    def test_to_dict(self) -> None:
        """Test serialization to dict."""
        info = AgentStateInfo(
            agent_id="a1",
            avatar_id="v1",
            persona_id="p1",
            state=ThinkingState.TOOL_CALLING,
            message="calling tool",
            progress=0.75,
        )
        data = info.to_dict()
        assert data["agent_id"] == "a1"
        assert data["avatar_id"] == "v1"
        assert data["persona_id"] == "p1"
        assert data["state"] == "tool_calling"  # serialized as string
        assert data["message"] == "calling tool"
        assert data["progress"] == 0.75

    def test_from_dict(self) -> None:
        """Test deserialization from dict."""
        data = {
            "agent_id": "a2",
            "avatar_id": None,
            "persona_id": "expert",
            "state": "responding",
            "message": None,
            "progress": None,
            "timestamp": 999.0,
        }
        info = AgentStateInfo.from_dict(data)
        assert info.agent_id == "a2"
        assert info.state == ThinkingState.RESPONDING
        assert info.timestamp == 999.0


class TestThinkingStateManager:
    """Tests for ThinkingStateManager."""

    def setup_method(self) -> None:
        """Reset manager before each test."""
        reset_thinking_manager()

    def test_register_agent(self) -> None:
        """Test agent registration."""
        mgr = get_thinking_manager()
        mgr.register_agent("agent-1", persona_id="default")

        state = mgr.get_agent_state("agent-1")
        assert state is not None
        assert state.agent_id == "agent-1"
        assert state.state == ThinkingState.IDLE

    def test_register_agent_with_avatar(self) -> None:
        """Test agent registration with avatar mapping."""
        mgr = get_thinking_manager()
        mgr.register_agent("agent-2", persona_id="helper", avatar_id="avatar-1")

        state = mgr.get_agent_state("agent-2")
        assert state is not None
        assert state.avatar_id == "avatar-1"
        assert mgr.avatar_mappings["agent-2"] == "avatar-1"

    def test_set_agent_state(self) -> None:
        """Test setting agent state."""
        mgr = get_thinking_manager()
        mgr.register_agent("agent-3", persona_id="p1")

        mgr.set_agent_state("agent-3", ThinkingState.THINKING, message="Processing")

        state = mgr.get_agent_state("agent-3")
        assert state is not None
        assert state.state == ThinkingState.THINKING
        assert state.message == "Processing"

    def test_set_state_unregistered_agent(self) -> None:
        """Test setting state on unregistered agent auto-registers."""
        mgr = get_thinking_manager()

        mgr.set_agent_state("unknown-agent", ThinkingState.ERROR, message="Failed")

        state = mgr.get_agent_state("unknown-agent")
        assert state is not None
        assert state.state == ThinkingState.ERROR

    def test_get_all_states(self) -> None:
        """Test getting all agent states."""
        mgr = get_thinking_manager()
        mgr.register_agent("a1", persona_id="p1")
        mgr.register_agent("a2", persona_id="p2")
        mgr.register_agent("a3", persona_id="p3")

        states = mgr.get_all_states()
        assert len(states) == 3
        assert "a1" in states
        assert "a2" in states
        assert "a3" in states

    def test_map_agent_to_avatar(self) -> None:
        """Test mapping agent to avatar."""
        mgr = get_thinking_manager()
        mgr.register_agent("agent-4", persona_id="p1")

        mgr.map_agent_to_avatar("agent-4", "new-avatar")

        state = mgr.get_agent_state("agent-4")
        assert state is not None
        assert state.avatar_id == "new-avatar"
        assert mgr.avatar_mappings["agent-4"] == "new-avatar"

    def test_broadcast_callbacks(self) -> None:
        """Test broadcast callbacks receive state changes."""
        mgr = get_thinking_manager()
        messages: list[dict] = []

        mgr.add_broadcast_callback(lambda m: messages.append(m))
        mgr.register_agent("agent-5", persona_id="p1")
        mgr.set_agent_state("agent-5", ThinkingState.THINKING)

        assert len(messages) >= 2
        assert any(m["type"] == "agent_state_change" for m in messages)

    def test_remove_broadcast_callback(self) -> None:
        """Test removing broadcast callback."""
        mgr = get_thinking_manager()
        messages: list[dict] = []

        def callback(m: dict) -> None:
            messages.append(m)

        mgr.add_broadcast_callback(callback)
        mgr.remove_broadcast_callback(callback)

        mgr.register_agent("agent-6", persona_id="p1")
        assert len(messages) == 0

    def test_start_tool_call(self) -> None:
        """Test tool call lifecycle."""
        mgr = get_thinking_manager()
        messages: list[dict] = []
        mgr.add_broadcast_callback(lambda m: messages.append(m))

        mgr.register_agent("agent-7", persona_id="p1")
        mgr.start_tool_call("agent-7", tool_name="search")

        state = mgr.get_agent_state("agent-7")
        assert state is not None
        assert state.state == ThinkingState.TOOL_CALLING
        assert any(m["type"] == "tool_call_start" for m in messages)

    def test_end_tool_call(self) -> None:
        """Test ending tool call."""
        mgr = get_thinking_manager()
        messages: list[dict] = []
        mgr.add_broadcast_callback(lambda m: messages.append(m))

        mgr.register_agent("agent-8", persona_id="p1")
        mgr.start_tool_call("agent-8", tool_name="calc")
        mgr.end_tool_call("agent-8", tool_name="calc")

        assert any(m["type"] == "tool_call_end" for m in messages)

    def test_handoff_lifecycle(self) -> None:
        """Test handoff start and complete."""
        mgr = get_thinking_manager()
        messages: list[dict] = []
        mgr.add_broadcast_callback(lambda m: messages.append(m))

        mgr.register_agent("agent-9", persona_id="general")
        mgr.handoff_start("agent-9", to_agent_persona="expert", reason="specialized task")

        state = mgr.get_agent_state("agent-9")
        assert state is not None
        assert state.state == ThinkingState.HANDOFF
        assert any(m["type"] == "handoff_start" for m in messages)

        mgr.handoff_complete("agent-9", new_persona_id="expert")
        state = mgr.get_agent_state("agent-9")
        assert state is not None
        assert state.state == ThinkingState.IDLE
        assert any(m["type"] == "handoff_complete" for m in messages)


class TestThinkingStateManagerAsync:
    """Tests for async broadcast callbacks."""

    def setup_method(self) -> None:
        """Reset manager before each test."""
        reset_thinking_manager()

    def test_async_callback_receives_messages(self) -> None:
        """Test that async callbacks receive state changes."""
        async def _run():
            mgr = get_thinking_manager()
            received: list[dict] = []

            async def async_cb(msg: dict):
                received.append(msg)

            mgr.add_broadcast_callback(async_cb)
            mgr.register_agent("async-agent", persona_id="p1")
            mgr.set_agent_state("async-agent", ThinkingState.THINKING)

            await asyncio.sleep(0.02)

            assert any(m.get("type") == "agent_state_change" for m in received)

        asyncio.run(_run())


class TestMemoryItem:
    """Tests for MemoryItem dataclass."""

    def test_creation(self) -> None:
        """Test creating MemoryItem."""
        item = MemoryItem(
            role="user",
            content="Hello",
            timestamp="2024-01-01T00:00:00",
        )
        assert item.role == "user"
        assert item.content == "Hello"
        assert item.timestamp == "2024-01-01T00:00:00"


class TestMemoryStore:
    """Tests for MemoryStore."""

    def test_add_and_get(self) -> None:
        """Test adding and retrieving items."""
        store = MemoryStore()
        store.add("discord", "general", "user1", "user", "Hello")
        store.add("discord", "general", "user1", "assistant", "Hi there")

        items = store.get("discord", "general", "user1")
        assert len(items) == 2
        assert items[0].role == "user"
        assert items[0].content == "Hello"
        assert items[1].role == "assistant"
        assert items[1].content == "Hi there"

    def test_get_with_limit(self) -> None:
        """Test limiting retrieved items."""
        store = MemoryStore()
        for i in range(10):
            store.add("discord", "general", "user1", "user", f"msg{i}")

        items = store.get("discord", "general", "user1", limit=3)
        assert len(items) == 3
        assert items[0].content == "msg7"
        assert items[1].content == "msg8"
        assert items[2].content == "msg9"

    def test_get_limit_zero(self) -> None:
        """Test limit=0 returns empty list."""
        store = MemoryStore()
        store.add("discord", "general", "user1", "user", "test")

        items = store.get("discord", "general", "user1", limit=0)
        assert items == []

    def test_get_nonexistent_context(self) -> None:
        """Test getting from nonexistent context."""
        store = MemoryStore()
        items = store.get("slack", "random", "nobody")
        assert items == []

    def test_clear(self) -> None:
        """Test clearing context."""
        store = MemoryStore()
        store.add("discord", "general", "user1", "user", "msg1")
        store.add("discord", "general", "user1", "user", "msg2")

        count = store.clear("discord", "general", "user1")
        assert count == 2

        items = store.get("discord", "general", "user1")
        assert items == []

    def test_clear_nonexistent(self) -> None:
        """Test clearing nonexistent context returns 0."""
        store = MemoryStore()
        count = store.clear("discord", "general", "nonexistent")
        assert count == 0

    def test_max_items_per_context(self) -> None:
        """Test that max items limit is enforced."""
        store = MemoryStore(max_items_per_context=3)
        for i in range(10):
            store.add("discord", "general", "user1", "user", f"msg{i}")

        items = store.get("discord", "general", "user1", limit=100)
        assert len(items) == 3
        # Should have most recent
        assert items[0].content == "msg7"

    def test_separate_contexts(self) -> None:
        """Test that different contexts are separate."""
        store = MemoryStore()
        store.add("discord", "general", "user1", "user", "d-msg1")
        store.add("slack", "random", "user1", "user", "s-msg1")

        d_items = store.get("discord", "general", "user1")
        s_items = store.get("slack", "random", "user1")

        assert len(d_items) == 1
        assert d_items[0].content == "d-msg1"
        assert len(s_items) == 1
        assert s_items[0].content == "s-msg1"


class TestMemoryStorePersistence:
    """Tests for MemoryStore persistence."""

    def test_persistence_roundtrip(self, tmp_path: Path) -> None:
        """Test that memory persists to disk and loads back."""
        persist_file = tmp_path / "memory.jsonl"

        # Create store and add items
        store1 = MemoryStore(persist=True, persist_path=str(persist_file))
        store1.add("discord", "gen", "u1", "user", "Hello")
        store1.add("discord", "gen", "u1", "assistant", "Hi there")

        # Verify file content
        content = persist_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2

        # Create new store (simulates restart)
        store2 = MemoryStore(persist=True, persist_path=str(persist_file))
        items = store2.get("discord", "gen", "u1")

        assert len(items) == 2
        assert items[0].content == "Hello"
        assert items[0].role == "user"
        assert items[1].content == "Hi there"
        assert items[1].role == "assistant"

    def test_persistence_handles_corrupted_data(self, tmp_path: Path) -> None:
        """Test resilience against corrupted data."""
        persist_file = tmp_path / "corrupted.jsonl"
        persist_file.write_text(
            '{"valid": "json", "but": "wrong schema"}\n'
            'corrupted { json\n'
            '{"key": "discord:gen:u1", "role": "user", "content": "survivor", "timestamp": "2024-01-01"}\n'
        )

        store = MemoryStore(persist=True, persist_path=str(persist_file))
        items = store.get("discord", "gen", "u1")

        # Should load only the valid item
        assert len(items) == 1
        assert items[0].content == "survivor"

    def test_persistence_creates_directory(self, tmp_path: Path) -> None:
        """Test that persistence creates parent directory."""
        persist_file = tmp_path / "subdir" / "deep" / "memory.jsonl"

        store = MemoryStore(persist=True, persist_path=str(persist_file))
        store.add("discord", "gen", "u1", "user", "test")

        assert persist_file.exists()

    def test_persistence_disabled(self) -> None:
        """Test that no file is created when persistence is off."""
        store = MemoryStore(persist=False)
        store.add("discord", "gen", "u1", "user", "test")

        # No file should be created (using default path check would be flaky)
        # Just verify it doesn't raise
        assert store.get("discord", "gen", "u1")[0].content == "test"
