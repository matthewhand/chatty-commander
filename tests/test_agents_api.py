from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.chatty_commander.web.routes.agents import router as agents_router


def test_agents_blueprints_crud_and_team():
    app = FastAPI()
    app.include_router(agents_router)
    client = TestClient(app)

    # Create from NL description
    r = client.post('/api/v1/agents/blueprints', json={"description": "Expert analyst who summarizes URLs and hands off to coder"})
    assert r.status_code == 200
    bp1 = r.json()
    aid = bp1['id']

    # List
    r2 = client.get('/api/v1/agents/blueprints')
    assert r2.status_code == 200
    assert any(x['id'] == aid for x in r2.json())

    # Update
    payload = {
        "name": "Analyst",
        "description": "Summarizes URLs",
        "persona_prompt": "You are an analyst",
        "capabilities": ["summarize", "route"],
        "team_role": "analyst",
        "handoff_triggers": ["needs_coding"]
    }
    r3 = client.put(f'/api/v1/agents/blueprints/{aid}', json=payload)
    assert r3.status_code == 200

    # Team info
    r4 = client.get('/api/v1/agents/team')
    assert r4.status_code == 200
    data = r4.json()
    assert 'roles' in data and 'agents' in data

    # Handoff
    # Create a second agent
    r5 = client.post('/api/v1/agents/blueprints', json={"description": "Coder who implements tasks"})
    assert r5.status_code == 200
    bid = r5.json()['id']
    r6 = client.post('/api/v1/agents/team/handoff', json={"from_agent_id": aid, "to_agent_id": bid, "reason": "needs_coding"})
    assert r6.status_code == 200

    # Delete
    r7 = client.delete(f'/api/v1/agents/blueprints/{aid}')
    assert r7.status_code == 200
