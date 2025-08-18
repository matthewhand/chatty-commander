from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.web_mode import create_app


def test_command_unknown_returns_404_minimal_app():
    app = create_app(no_auth=True)
    client = TestClient(app)

    resp = client.post("/api/v1/command", json={"command": "does_not_exist"})
    assert resp.status_code == 404
    data = resp.json()
    assert isinstance(data, dict)
    # FastAPI returns detail for HTTPException
    assert "detail" in data
