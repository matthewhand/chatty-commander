import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.chatty_commander.avatars.thinking_state import get_thinking_manager, reset_thinking_manager
from src.chatty_commander.web.routes.avatar_ws import manager
from src.chatty_commander.web.routes.avatar_ws import router as avatar_ws_router


def test_avatar_ws_includes_theme_in_snapshot():
    reset_thinking_manager()
    mgr = get_thinking_manager()
    agent_id = "plat-chan-user"
    mgr.register_agent(agent_id, persona_id="expert")

    # Inject a theme resolver for test
    manager.theme_resolver = lambda persona_id: "robot" if persona_id == "expert" else "default"

    app = FastAPI()
    app.include_router(avatar_ws_router)
    client = TestClient(app)

    with client.websocket_connect("/avatar/ws") as ws:
        msg = json.loads(ws.receive_text())
        assert msg["type"] in ("connection_established", "agent_states_snapshot")
        data = msg.get("data", {})
        assert isinstance(data, dict)
        state = data.get(agent_id)
        assert state is not None
        assert state.get("persona_id") == "expert"
        assert state.get("theme") == "robot"
