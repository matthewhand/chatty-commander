import json

from chatty_commander.web.server import create_app
from fastapi.testclient import TestClient


def test_ws_ping_pong():
    app = create_app(no_auth=True)
    client = TestClient(app)

    with client.websocket_connect("/ws") as ws:
        # Receive initial connection established snapshot
        data = json.loads(ws.receive_text())
        assert data.get("type") == "connection_established"
        # Send ping and expect pong promptly (or heartbeat if supported by router)
        ws.send_text(json.dumps({"type": "ping"}))
        msg = json.loads(ws.receive_text())
        assert msg.get("type") in {"pong", "heartbeat"}
