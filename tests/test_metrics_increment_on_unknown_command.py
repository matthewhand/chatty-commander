from chatty_commander.web.web_mode import create_app
from fastapi.testclient import TestClient


def test_metrics_increment_on_unknown_command():
    app = create_app(no_auth=True)
    client = TestClient(app)

    m1 = client.get("/api/v1/metrics").json()
    resp = client.post("/api/v1/command", json={"command": "unknown_command"})
    assert resp.status_code in (200, 404)
    m2 = client.get("/api/v1/metrics").json()

    assert m2["command_post"] >= m1.get("command_post", 0) + 1
