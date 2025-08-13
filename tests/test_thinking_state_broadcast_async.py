import asyncio

import pytest
from chatty_commander.avatars.thinking_state import ThinkingState, ThinkingStateManager


def test_async_broadcast_callback_receives_state_changes():
    async def _run():
        mgr = ThinkingStateManager()
        received: list[dict] = []

        async def async_cb(msg: dict):
            received.append(msg)

        mgr.add_broadcast_callback(async_cb)

        # Register agent triggers an initial broadcast
        mgr.register_agent("agent1", persona_id="p1", avatar_id=None)

        # Set state which should schedule async callback execution
        mgr.set_agent_state("agent1", ThinkingState.THINKING, message="processing")

        # Allow event loop to run scheduled tasks
        await asyncio.sleep(0.02)

        # We should have at least two messages: registration and state change
        assert any(m.get("type") == "agent_state_change" for m in received)
        # Last message should reflect the THINKING state
        last = received[-1]
        assert last.get("type") == "agent_state_change"
        assert last.get("data", {}).get("state") == "thinking"

    asyncio.run(_run())
