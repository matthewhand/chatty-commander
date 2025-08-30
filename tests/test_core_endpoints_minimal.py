from fastapi.testclient import TestClient

from chatty_commander.web.web_mode import create_app


def test_status_state_command_endpoints_minimal_app():
    app = create_app(no_auth=True)
    client = TestClient(app)

    # Status exists
    r = client.get("/api/v1/status")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "running"
    assert "version" in data

    # Get state
    r = client.get("/api/v1/state")
    assert r.status_code == 200
    assert r.json()["current_state"] == "idle"

    # Change state
    r = client.post("/api/v1/state", json={"state": "computer"})
    assert r.status_code == 200

    # Verify changed
    r = client.get("/api/v1/state")
    assert r.status_code == 200
    assert r.json()["current_state"] == "computer"

    # Execute command
    r = client.post("/api/v1/command", json={"command": "hello"})
    assert r.status_code == 200
    resp = r.json()
    assert resp["success"] is True
    assert "execution_time" in resp
