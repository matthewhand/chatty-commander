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

"""Consolidated tests for core API v1 routes."""

import pytest
from fastapi.testclient import TestClient

from chatty_commander.web.web_mode import create_app


@pytest.fixture()
def client():
    """Shared test client using a no-auth app instance."""
    app = create_app(no_auth=True)
    return TestClient(app)


# -- config ------------------------------------------------------------------


def test_config_get_increments_metrics(client):
    m1 = client.get("/api/v1/metrics").json()
    client.get("/api/v1/config")
    m2 = client.get("/api/v1/metrics").json()

    assert m2["config_get"] >= m1.get("config_get", 0) + 1


def test_config_put_increments_metrics_and_applies(client):
    m1 = client.get("/api/v1/metrics").json()
    r = client.put("/api/v1/config", json={"foo": {"bar": 1}})
    assert r.status_code == 200
    m2 = client.get("/api/v1/metrics").json()
    assert m2["config_put"] >= m1.get("config_put", 0) + 1

    # Confirm config now exposes the key
    r = client.get("/api/v1/config")
    assert r.status_code == 200
    cfg = r.json()
    assert "foo" in cfg and isinstance(cfg["foo"], dict)


# -- command -----------------------------------------------------------------


def test_command_unknown_returns_200_minimal_app(client):
    resp = client.post("/api/v1/command", json={"command": "does_not_exist"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert isinstance(data["message"], str)
    assert (
        "not found" in data["message"].lower()
        or "no configuration" in data["message"].lower()
    )
    assert data["execution_time"] > 0


def test_metrics_increment_on_unknown_command(client):
    m1 = client.get("/api/v1/metrics").json()
    resp = client.post("/api/v1/command", json={"command": "unknown_command"})
    assert resp.status_code in (200, 404)
    m2 = client.get("/api/v1/metrics").json()

    assert m2["command_post"] >= m1.get("command_post", 0) + 1


# -- state -------------------------------------------------------------------


def test_state_change_invalid_value_returns_422(client):
    r = client.post("/api/v1/state", json={"state": "invalid"})
    assert r.status_code == 422
