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
