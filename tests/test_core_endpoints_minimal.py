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

from chatty_commander.web.web_mode import create_app


def test_status_state_command_endpoints_minimal_app():
    app = create_app(no_auth=True)
    client = TestClient(app)

    # Status exists
    r = client.get("/api/v1/status")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "running"
    assert "version" in data

    # Get state
    r = client.get("/api/v1/state")
    assert r.status_code == 200
    assert r.json()["current_state"] == "idle"

    # Change state
    r = client.post("/api/v1/state", json={"state": "computer"})
    assert r.status_code == 200

    # Verify changed
    r = client.get("/api/v1/state")
    assert r.status_code == 200
    assert r.json()["current_state"] == "computer"

    # Execute command
    r = client.post("/api/v1/command", json={"command": "hello"})
    assert r.status_code == 200
    resp = r.json()
    assert resp["success"] is True
    assert "execution_time" in resp
