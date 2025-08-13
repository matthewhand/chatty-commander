from chatty_commander.web.server import create_app
from fastapi.testclient import TestClient


def test_handoff_between_missing_agents_returns_404():
    app = create_app(no_auth=True)
    client = TestClient(app)

    r = client.post(
        "/api/v1/agents/team/handoff",
        json={"from_agent_id": "a", "to_agent_id": "b", "reason": "test"},
    )
    assert r.status_code == 404
