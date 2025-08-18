import json

from fastapi.testclient import TestClient

from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.web_mode import WebModeServer


def test_ws_ping_pong():
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
        # Receive initial connection established snapshot
        data = json.loads(ws.receive_text())
        assert data.get("type") == "connection_established"
        # Send ping and expect pong promptly (or heartbeat if supported by router)
        ws.send_text(json.dumps({"type": "ping"}))
        msg = json.loads(ws.receive_text())
        assert msg.get("type") in {"pong", "heartbeat"}
