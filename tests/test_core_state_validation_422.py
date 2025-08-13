from chatty_commander.web.web_mode import create_app
from fastapi.testclient import TestClient


def test_state_change_invalid_value_returns_422():
    app = create_app(no_auth=True)
    client = TestClient(app)

    r = client.post("/api/v1/state", json={"state": "invalid"})
    assert r.status_code == 422
