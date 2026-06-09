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

"""Tests for GET/PUT /api/preferences (web/routes/preferences.py)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.routes.preferences import (
    _DEFAULTS,
    include_preferences_routes,
)


class FakeConfigManager:
    """Minimal config manager exposing ``config`` dict + ``save_config``."""

    def __init__(self, config=None):
        self.config = config if config is not None else {}
        self.save_calls = 0

    def save_config(self):
        self.save_calls += 1


def make_client(cfg_mgr):
    app = FastAPI()
    app.include_router(
        include_preferences_routes(get_config_manager=lambda: cfg_mgr)
    )
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /api/preferences
# ---------------------------------------------------------------------------


def test_get_preferences_returns_defaults_when_unset():
    cfg_mgr = FakeConfigManager()
    client = make_client(cfg_mgr)

    resp = client.get("/api/preferences")
    assert resp.status_code == 200
    data = resp.json()
    assert data == _DEFAULTS
    # Response shape: known keys with expected types
    assert isinstance(data["theme"], str)
    assert isinstance(data["notifications"], bool)
    assert isinstance(data["language"], str)
    assert isinstance(data["auto_start"], bool)
    assert isinstance(data["telemetry"], bool)


def test_get_preferences_returns_saved_values_merged_with_defaults():
    cfg_mgr = FakeConfigManager({"preferences": {"theme": "light"}})
    client = make_client(cfg_mgr)

    data = client.get("/api/preferences").json()
    assert data["theme"] == "light"  # saved value wins
    assert data["notifications"] is True  # default filled in
    assert data["language"] == "en"


def test_get_preferences_degrades_to_defaults_without_config_manager():
    client = make_client(None)
    resp = client.get("/api/preferences")
    assert resp.status_code == 200
    assert resp.json() == _DEFAULTS


def test_get_preferences_degrades_to_defaults_when_manager_raises():
    def boom():
        raise RuntimeError("config backend unavailable")

    app = FastAPI()
    app.include_router(include_preferences_routes(get_config_manager=boom))
    client = TestClient(app)

    resp = client.get("/api/preferences")
    assert resp.status_code == 200
    assert resp.json() == _DEFAULTS


# ---------------------------------------------------------------------------
# PUT /api/preferences
# ---------------------------------------------------------------------------


def test_put_preferences_updates_and_persists():
    cfg_mgr = FakeConfigManager()
    client = make_client(cfg_mgr)

    resp = client.put(
        "/api/preferences",
        json={"theme": "light", "notifications": False, "language": "fr"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["theme"] == "light"
    assert data["notifications"] is False
    assert data["language"] == "fr"
    # Untouched keys keep their defaults
    assert data["auto_start"] is False

    # Persisted under the 'preferences' section of the config
    assert cfg_mgr.config["preferences"]["theme"] == "light"
    assert cfg_mgr.config["preferences"]["notifications"] is False
    assert cfg_mgr.save_calls == 1

    # And a subsequent GET reflects the update
    assert client.get("/api/preferences").json()["theme"] == "light"


def test_put_preferences_partial_update_keeps_existing_values():
    cfg_mgr = FakeConfigManager({"preferences": {"theme": "light"}})
    client = make_client(cfg_mgr)

    data = client.put("/api/preferences", json={"notifications": False}).json()
    assert data["theme"] == "light"
    assert data["notifications"] is False


def test_put_preferences_allows_extra_keys():
    cfg_mgr = FakeConfigManager()
    client = make_client(cfg_mgr)

    data = client.put(
        "/api/preferences", json={"theme": "dark", "avatar_size": "large"}
    ).json()
    assert data["avatar_size"] == "large"
    assert cfg_mgr.config["preferences"]["avatar_size"] == "large"


def test_put_preferences_rejects_invalid_types():
    cfg_mgr = FakeConfigManager()
    client = make_client(cfg_mgr)

    resp = client.put("/api/preferences", json={"notifications": "definitely"})
    assert resp.status_code == 422

    resp = client.put("/api/preferences", json={"theme": 123})
    assert resp.status_code == 422

    # Nothing was persisted
    assert cfg_mgr.save_calls == 0


def test_put_preferences_error_path_returns_500_when_save_fails():
    class ExplodingConfigManager(FakeConfigManager):
        def save_config(self):
            raise RuntimeError("disk full")

    client = make_client(ExplodingConfigManager())
    resp = client.put("/api/preferences", json={"theme": "light"})
    assert resp.status_code == 500
    assert "disk full" in resp.json()["detail"]


def test_put_preferences_without_config_manager_degrades_gracefully():
    client = make_client(None)
    resp = client.put("/api/preferences", json={"theme": "light"})
    assert resp.status_code == 200
    assert resp.json()["theme"] == "light"


# ---------------------------------------------------------------------------
# Router registration in the real apps
# ---------------------------------------------------------------------------


def test_preferences_registered_in_web_mode_app():
    from chatty_commander.web.web_mode import create_app

    app = create_app(no_auth=True)
    client = TestClient(app)

    resp = client.get("/api/preferences")
    assert resp.status_code == 200
    assert "theme" in resp.json()


def test_preferences_registered_in_server_create_app():
    from chatty_commander.web.server import create_app

    app = create_app(no_auth=True, config_manager=FakeConfigManager())
    client = TestClient(app)

    resp = client.get("/api/preferences")
    assert resp.status_code == 200
    assert "theme" in resp.json()
