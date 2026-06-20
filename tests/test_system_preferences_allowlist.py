"""PUT /api/preferences + /api/restore (system.py) must honor the allow-list.

The guard previously read ``if k in ALLOWED_PREF_KEYS or True:`` — the ``or
True`` made it a no-op, so any config key (auth, web_server, ...) could be
overwritten and persisted. These tests pin the real filtering behavior.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.routes.system import ALLOWED_PREF_KEYS, include_system_routes


class FakeConfigManager:
    def __init__(self, config=None):
        self.config = config if config is not None else {}
        self.save_calls = 0

    def save_config(self):
        self.save_calls += 1


def _client(cfg_mgr):
    app = FastAPI()
    app.include_router(
        include_system_routes(
            get_start_time=lambda: 0.0,
            get_config_manager=lambda: cfg_mgr,
        )
    )
    return TestClient(app)


def test_put_preferences_persists_allowed_key():
    cfg_mgr = FakeConfigManager()
    client = _client(cfg_mgr)
    resp = client.put("/api/preferences", json={"ui": {"theme": "light"}})
    assert resp.status_code == 200
    assert cfg_mgr.config["ui"] == {"theme": "light"}
    assert "ui" in ALLOWED_PREF_KEYS


def test_put_preferences_rejects_disallowed_key():
    cfg_mgr = FakeConfigManager({"auth": {"api_key": "secret"}})
    client = _client(cfg_mgr)
    resp = client.put(
        "/api/preferences",
        json={"auth": {"api_key": "attacker"}, "web_server": {"host": "0.0.0.0"}},
    )
    assert resp.status_code == 200
    # Disallowed keys were NOT written.
    assert cfg_mgr.config["auth"] == {"api_key": "secret"}
    assert "web_server" not in cfg_mgr.config
    # And not echoed back as accepted preferences.
    assert resp.json()["preferences"] == {}


def test_put_preferences_mixed_keys_only_allowed_persisted():
    cfg_mgr = FakeConfigManager()
    client = _client(cfg_mgr)
    resp = client.put(
        "/api/preferences",
        json={"ui": {"theme": "dark"}, "auth": {"api_key": "x"}},
    )
    assert resp.status_code == 200
    assert cfg_mgr.config.get("ui") == {"theme": "dark"}
    assert "auth" not in cfg_mgr.config


def test_restore_rejects_disallowed_key():
    cfg_mgr = FakeConfigManager({"auth": {"api_key": "secret"}})
    client = _client(cfg_mgr)
    resp = client.post(
        "/api/restore",
        json={"data": {"general": {"x": 1}, "auth": {"api_key": "attacker"}}},
    )
    assert resp.status_code == 200
    assert cfg_mgr.config["general"] == {"x": 1}
    # auth must remain untouched by a restore payload.
    assert cfg_mgr.config["auth"] == {"api_key": "secret"}
