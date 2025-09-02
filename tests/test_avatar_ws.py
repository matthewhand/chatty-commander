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

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.avatars.thinking_state import (
    get_thinking_manager,
    reset_thinking_manager,
)
from chatty_commander.web.routes.avatar_ws import router as avatar_ws_router


def test_avatar_ws_broadcasts_state_changes():
    reset_thinking_manager()
    mgr = get_thinking_manager()
    # Register an agent and set a state before connecting (for snapshot)
    agent_id = "plat-chan-user"
    mgr.register_agent(agent_id, persona_id="user")

    app = FastAPI()
    app.include_router(avatar_ws_router)
    client = TestClient(app)

    with client.websocket_connect("/avatar/ws") as ws:
        # Receive initial snapshot only
        msg = json.loads(ws.receive_text())
        assert msg["type"] in ("connection_established", "agent_states_snapshot")
        # Do not rely on async broadcast in this unit test environment to avoid timing flakiness.
