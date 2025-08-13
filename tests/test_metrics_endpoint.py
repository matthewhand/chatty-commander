from chatty_commander.web.web_mode import create_app
from fastapi.testclient import TestClient


def test_metrics_counts_increment():
    app = create_app(no_auth=True)
    client = TestClient(app)

    # Initial metrics
    m1 = client.get("/api/v1/metrics").json()

    # Call some endpoints
    client.get("/api/v1/health")
    client.get("/api/v1/status")
    client.get("/api/v1/state")
    client.post("/api/v1/state", json={"state": "chatty"})
    client.post("/api/v1/command", json={"command": "hello"})

    m2 = client.get("/api/v1/metrics").json()

    assert m2["status"] >= (m1.get("status", 0) + 1)
    assert m2["config_get"] >= m1.get("config_get", 0)
    assert m2["state_get"] >= (m1.get("state_get", 0) + 1)
    assert m2["state_post"] >= (m1.get("state_post", 0) + 1)
    assert m2["command_post"] >= (m1.get("command_post", 0) + 1)
