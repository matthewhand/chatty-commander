from chatty_commander.web.server import create_app
from fastapi.testclient import TestClient


def test_create_blueprint_invalid_payload_returns_400():
    app = create_app(no_auth=True)
    client = TestClient(app)
    # Missing required fields for AgentBlueprintModel; payload will fail validation in route
    r = client.post("/api/v1/agents/blueprints", json={"name": 123})
    assert r.status_code == 400
