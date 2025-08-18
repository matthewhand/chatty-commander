import json

from fastapi.testclient import TestClient

from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.web_mode import WebModeServer


def test_ws_initial_snapshot_contains_state():
    cfg = Config()
    sm = StateManager()
    mm = ModelManager(cfg)

    class NoopExec:
        def __init__(self, *a, **kw):
            pass

    server = WebModeServer(cfg, sm, mm, NoopExec(), no_auth=True)
    app = server._create_app()
    client = TestClient(app)

    with client.websocket_connect("/ws") as ws:
        msg = ws.receive_text()
        data = json.loads(msg)
        assert data.get("type") == "connection_established"
        snap = data.get("data", {})
        assert isinstance(snap, dict)
        assert "current_state" in snap
        assert "active_models" in snap
