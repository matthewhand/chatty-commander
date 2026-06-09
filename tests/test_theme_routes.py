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

"""Tests for GET /api/themes and GET/POST /api/theme (web/routes/themes.py)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.routes.themes import (
    AVAILABLE_THEMES,
    DEFAULT_THEME,
    include_theme_routes,
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
    app.include_router(include_theme_routes(get_config_manager=lambda: cfg_mgr))
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /api/themes
# ---------------------------------------------------------------------------


def test_get_themes_lists_daisyui_themes():
    client = make_client(FakeConfigManager())
    resp = client.get("/api/themes")
    assert resp.status_code == 200
    data = resp.json()
    # Response shape
    assert set(data.keys()) == {"themes", "current"}
    assert isinstance(data["themes"], list)
    # All themes the frontend supports (tailwind.config.js daisyui.themes)
    assert data["themes"] == list(AVAILABLE_THEMES)
    assert {"dark", "light", "cyberpunk", "synthwave"} <= set(data["themes"])
    assert data["current"] == DEFAULT_THEME


def test_get_themes_reports_persisted_current_theme():
    cfg_mgr = FakeConfigManager({"ui": {"theme": "cyberpunk"}})
    client = make_client(cfg_mgr)
    resp = client.get("/api/themes")
    assert resp.status_code == 200
    assert resp.json()["current"] == "cyberpunk"


def test_get_themes_degrades_gracefully_when_config_manager_broken():
    def broken():
        raise RuntimeError("config unavailable")

    app = FastAPI()
    app.include_router(include_theme_routes(get_config_manager=broken))
    client = TestClient(app)

    resp = client.get("/api/themes")
    assert resp.status_code == 200
    assert resp.json()["current"] == DEFAULT_THEME


# ---------------------------------------------------------------------------
# GET /api/theme
# ---------------------------------------------------------------------------


def test_get_theme_defaults_to_dark():
    client = make_client(FakeConfigManager())
    resp = client.get("/api/theme")
    assert resp.status_code == 200
    assert resp.json() == {"theme": DEFAULT_THEME}


def test_get_theme_returns_persisted_theme():
    cfg_mgr = FakeConfigManager({"ui": {"theme": "synthwave"}})
    client = make_client(cfg_mgr)
    resp = client.get("/api/theme")
    assert resp.status_code == 200
    assert resp.json() == {"theme": "synthwave"}


def test_get_theme_ignores_invalid_persisted_value():
    # Non-string / empty values fall back to the default theme
    cfg_mgr = FakeConfigManager({"ui": {"theme": ""}})
    client = make_client(cfg_mgr)
    resp = client.get("/api/theme")
    assert resp.status_code == 200
    assert resp.json() == {"theme": DEFAULT_THEME}


# ---------------------------------------------------------------------------
# POST /api/theme
# ---------------------------------------------------------------------------


def test_set_theme_success_persists_and_round_trips():
    cfg_mgr = FakeConfigManager()
    client = make_client(cfg_mgr)

    resp = client.post("/api/theme", json={"theme": "light"})
    assert resp.status_code == 200
    data = resp.json()
    # Response shape
    assert set(data.keys()) == {"success", "theme"}
    assert data == {"success": True, "theme": "light"}

    # Persisted under ui.theme (where /api/v1/config + ThemeProvider read it)
    assert cfg_mgr.config["ui"]["theme"] == "light"
    assert cfg_mgr.save_calls == 1

    # Round trip via GET
    assert client.get("/api/theme").json() == {"theme": "light"}


def test_set_theme_preserves_other_ui_settings():
    cfg_mgr = FakeConfigManager({"ui": {"language": "en"}})
    client = make_client(cfg_mgr)
    resp = client.post("/api/theme", json={"theme": "cyberpunk"})
    assert resp.status_code == 200
    assert cfg_mgr.config["ui"] == {"language": "en", "theme": "cyberpunk"}


def test_set_theme_unknown_theme_returns_400():
    cfg_mgr = FakeConfigManager()
    client = make_client(cfg_mgr)
    resp = client.post("/api/theme", json={"theme": "solarized"})
    assert resp.status_code == 400
    assert "solarized" in resp.json()["detail"]
    # Nothing persisted
    assert "ui" not in cfg_mgr.config
    assert cfg_mgr.save_calls == 0


def test_set_theme_missing_body_field_returns_422():
    client = make_client(FakeConfigManager())
    resp = client.post("/api/theme", json={})
    assert resp.status_code == 422


def test_set_theme_succeeds_even_if_persistence_unavailable():
    # No config manager at all — theme still applies client-side
    client = make_client(None)
    resp = client.post("/api/theme", json={"theme": "dark"})
    assert resp.status_code == 200
    assert resp.json() == {"success": True, "theme": "dark"}


def test_set_theme_succeeds_even_if_save_raises():
    class ExplodingSave(FakeConfigManager):
        def save_config(self):
            raise OSError("disk full")

    cfg_mgr = ExplodingSave()
    client = make_client(cfg_mgr)
    resp = client.post("/api/theme", json={"theme": "light"})
    assert resp.status_code == 200
    assert resp.json() == {"success": True, "theme": "light"}


# ---------------------------------------------------------------------------
# Registration in the real apps
# ---------------------------------------------------------------------------


def test_theme_routes_registered_in_web_mode_app():
    from chatty_commander.web.web_mode import create_app

    client = TestClient(create_app(no_auth=True))
    resp = client.get("/api/themes")
    assert resp.status_code == 200
    assert "themes" in resp.json()

    resp = client.get("/api/theme")
    assert resp.status_code == 200
    assert "theme" in resp.json()


def test_theme_routes_registered_in_server_app():
    from chatty_commander.web.server import create_app

    cfg_mgr = FakeConfigManager()
    client = TestClient(create_app(no_auth=True, config_manager=cfg_mgr))

    resp = client.get("/api/themes")
    assert resp.status_code == 200

    resp = client.post("/api/theme", json={"theme": "synthwave"})
    assert resp.status_code == 200
    assert cfg_mgr.config["ui"]["theme"] == "synthwave"
