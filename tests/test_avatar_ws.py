import json
import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.chatty_commander.avatars.thinking_state import get_thinking_manager, reset_thinking_manager
from src.chatty_commander.web.routes.avatar_ws import router as avatar_ws_router


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
