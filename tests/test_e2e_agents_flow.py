# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from fastapi.testclient import TestClient

from chatty_commander.web.server import create_app


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
    r = client.post(
        "/api/v1/agents/blueprints", json={"description": "Summarizer agent"}
    )
    assert r.status_code == 200
    bp = r.json()
    uid = bp["id"]

    # List includes created
    r = client.get("/api/v1/agents/blueprints")
    assert r.status_code == 200
    assert any(i["id"] == uid for i in r.json())

    # Update name
    payload = {
        "name": "SummarizerX",
        "description": "d",
        "persona_prompt": "p",
        "capabilities": [],
        "team_role": None,
        "handoff_triggers": [],
    }
    r = client.put(f"/api/v1/agents/blueprints/{uid}", json=payload)
    assert r.status_code == 200
    assert r.json()["name"] == "SummarizerX"

    # Delete
    r = client.delete(f"/api/v1/agents/blueprints/{uid}")
    assert r.status_code == 200

    # Final list does not include uid
    r = client.get("/api/v1/agents/blueprints")
    assert all(i["id"] != uid for i in r.json())
