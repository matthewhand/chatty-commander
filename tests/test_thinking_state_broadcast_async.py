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

import asyncio

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
