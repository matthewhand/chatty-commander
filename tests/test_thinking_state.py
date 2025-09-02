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

from chatty_commander.avatars.thinking_state import (
    ThinkingState,
    get_thinking_manager,
    reset_thinking_manager,
)


def test_thinking_state_tool_call_and_handoff_broadcasts():
    reset_thinking_manager()
    mgr = get_thinking_manager()
    messages = []
    mgr.add_broadcast_callback(lambda m: messages.append(m))

    agent = "platform-chan-user"
    mgr.register_agent(agent, persona_id="default")

    # Start tool call
    mgr.start_tool_call(agent, tool_name="calc")
    assert any(m["type"] == "tool_call_start" for m in messages)
    # Should also set state to tool_calling
    state = mgr.get_agent_state(agent)
    assert state.state == ThinkingState.TOOL_CALLING

    # End tool call
    mgr.end_tool_call(agent, tool_name="calc")
    assert any(m["type"] == "tool_call_end" for m in messages)

    # Handoff
    mgr.handoff_start(agent, to_agent_persona="expert", reason="specialist task")
    assert any(m["type"] == "handoff_start" for m in messages)
    state = mgr.get_agent_state(agent)
    assert state.state == ThinkingState.HANDOFF

    mgr.handoff_complete(agent, new_persona_id="expert")
    assert any(m["type"] == "handoff_complete" for m in messages)
    state = mgr.get_agent_state(agent)
    assert state.state == ThinkingState.IDLE
