import pytest

from chatty_commander.web.routes.avatar_ws import AvatarWSConnectionManager


@pytest.mark.asyncio
async def test_broadcast_with_no_connections_does_not_crash():
    mgr = AvatarWSConnectionManager()
    # ensure empty
    mgr.active_connections.clear()
    # Should not raise
    mgr.broadcast_state_change({"type": "agent_state_change", "data": {}})
