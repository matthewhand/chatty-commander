from chatty_commander.web.server import create_app
from fastapi.testclient import TestClient


def test_list_blueprints_initially_empty():
    # Isolate global store
    try:
        from chatty_commander.web.routes import agents as _agents_mod

        _agents_mod._STORE.clear()
        _agents_mod._TEAM.clear()
    except Exception:
        pass
    app = create_app(no_auth=True)
    client = TestClient(app)

    r = client.get("/api/v1/agents/blueprints")
    assert r.status_code == 200
    assert r.json() == []
