from chatty_commander.web.server import create_app
from fastapi.testclient import TestClient


def test_create_agent_blueprint_from_description():
    app = create_app(no_auth=True)
    client = TestClient(app)

    payload = {"description": "My helpful agent who summarizes docs"}
    r = client.post("/api/v1/agents/blueprints", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data["name"]
    assert data["persona_prompt"]
