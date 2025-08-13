from chatty_commander.web.server import create_app
from fastapi.testclient import TestClient


def _reset_agents_store():
    try:
        from chatty_commander.web.routes import agents as _agents_mod

        _agents_mod._STORE.clear()
        _agents_mod._TEAM.clear()
    except Exception:
        pass


def test_e2e_agents_create_update_delete():
    _reset_agents_store()
    app = create_app(no_auth=True)
    client = TestClient(app)

    # Create from description
    r = client.post('/api/v1/agents/blueprints', json={'description': 'Summarizer agent'})
    assert r.status_code == 200
    bp = r.json()
    uid = bp['id']

    # List includes created
    r = client.get('/api/v1/agents/blueprints')
    assert r.status_code == 200
    assert any(i['id'] == uid for i in r.json())

    # Update name
    payload = {
        'name': 'SummarizerX',
        'description': 'd',
        'persona_prompt': 'p',
        'capabilities': [],
        'team_role': None,
        'handoff_triggers': [],
    }
    r = client.put(f'/api/v1/agents/blueprints/{uid}', json=payload)
    assert r.status_code == 200
    assert r.json()['name'] == 'SummarizerX'

    # Delete
    r = client.delete(f'/api/v1/agents/blueprints/{uid}')
    assert r.status_code == 200

    # Final list does not include uid
    r = client.get('/api/v1/agents/blueprints')
    assert all(i['id'] != uid for i in r.json())
