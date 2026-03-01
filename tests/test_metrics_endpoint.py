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


def test_metrics_counts_increment():
    app = create_app(no_auth=True)
    client = TestClient(app)

    # Initial metrics
    m1 = client.get("/api/v1/metrics").json()

    # Call some endpoints
    client.get("/api/v1/health")
    client.get("/api/v1/status")
    client.get("/api/v1/state")
    client.post("/api/v1/state", json={"state": "chatty"})
    client.post("/api/v1/command", json={"command": "hello"})

    m2 = client.get("/api/v1/metrics").json()

    assert m2["status"] >= (m1.get("status", 0) + 1)
    assert m2["response_time_avg"] >= 0.0
    assert m2["config_get"] >= m1.get("config_get", 0)
    assert m2["state_get"] >= (m1.get("state_get", 0) + 1)
    assert m2["state_post"] >= (m1.get("state_post", 0) + 1)
    assert m2["command_post"] >= (m1.get("command_post", 0) + 1)
