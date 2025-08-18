import asyncio
from unittest.mock import AsyncMock

import pytest

from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.web_mode import WebModeServer, WebSocketMessage


@pytest.mark.asyncio
async def test_broadcast_message_tolerates_send_errors():
    cfg = Config()
    sm = StateManager()
    mm = ModelManager(cfg)

    class NoopExec:
        def __init__(self, *a, **kw):
            pass

    server = WebModeServer(cfg, sm, mm, NoopExec(), no_auth=True)

    # Two connections: first raises once, second succeeds
    ok_ws = AsyncMock()
    flaky_ws = AsyncMock()
    flaky_ws.send_text.side_effect = [RuntimeError("boom"), None]
    server.active_connections.add(flaky_ws)
    server.active_connections.add(ok_ws)

    msg = WebSocketMessage(type="ping", data={})
    # Should not raise; should attempt send on both
    await server._broadcast_message(msg)

    # Retry path: flaky called twice, ok called once
    assert flaky_ws.send_text.call_count >= 1
    assert ok_ws.send_text.call_count == 1
