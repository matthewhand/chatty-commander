import json

from chatty_commander.web.server import create_app
from fastapi.testclient import TestClient


def test_ws_initial_snapshot_contains_state():
    app = create_app(no_auth=True)
    client = TestClient(app)

    with client.websocket_connect("/ws") as ws:
        msg = ws.receive_text()
        data = json.loads(msg)
        assert data.get("type") == "connection_established"
        snap = data.get("data", {})
        assert isinstance(snap, dict)
        assert "current_state" in snap
        assert "active_models" in snap
