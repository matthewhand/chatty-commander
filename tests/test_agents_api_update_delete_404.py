from fastapi.testclient import TestClient

from chatty_commander.web.routes.agents import AgentBlueprintModel
from chatty_commander.web.server import create_app


def test_update_blueprint_nonexistent_returns_404():
    app = create_app(no_auth=True)
    client = TestClient(app)

    payload = AgentBlueprintModel(
        name="X", description="Y", persona_prompt="Z", capabilities=[]
    ).model_dump()
    r = client.put("/api/v1/agents/blueprints/does-not-exist", json=payload)
    assert r.status_code == 404


def test_delete_blueprint_nonexistent_returns_404():
    app = create_app(no_auth=True)
    client = TestClient(app)

    r = client.delete("/api/v1/agents/blueprints/does-not-exist")
    assert r.status_code == 404
