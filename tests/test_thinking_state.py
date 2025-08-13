from chatty_commander.avatars.thinking_state import (
    get_thinking_manager,
    reset_thinking_manager,
    ThinkingState,
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
