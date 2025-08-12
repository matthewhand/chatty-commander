from chatty_commander.web.routes.agents import AgentBlueprintModel
from chatty_commander.web.server import create_app
from fastapi.testclient import TestClient


def test_agents_crud_happy_path_isolated_store():
    # Isolate store
    try:
        from chatty_commander.web.routes import agents as _agents_mod

        _agents_mod._STORE.clear()
        _agents_mod._TEAM.clear()
    except Exception:
        pass

    app = create_app(no_auth=True)
    client = TestClient(app)

    payload = AgentBlueprintModel(
        name="A1",
        description="desc",
        persona_prompt="prompt",
        capabilities=["x"],
    ).model_dump()

    # Create
    r = client.post("/api/v1/agents/blueprints", json=payload)
    assert r.status_code == 200
    created = r.json()
    uid = created["id"]

    # List
    r = client.get("/api/v1/agents/blueprints")
    assert r.status_code == 200
    items = r.json()
    assert any(i["id"] == uid for i in items)

    # Update
    payload["name"] = "A1-Updated"
    r = client.put(f"/api/v1/agents/blueprints/{uid}", json=payload)
    assert r.status_code == 200
    assert r.json()["name"] == "A1-Updated"

    # Delete
    r = client.delete(f"/api/v1/agents/blueprints/{uid}")
    assert r.status_code == 200

    # List empty again
    r = client.get("/api/v1/agents/blueprints")
    assert all(i["id"] != uid for i in r.json())
