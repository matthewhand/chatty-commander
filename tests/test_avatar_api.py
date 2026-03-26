"""Tests for avatar API routes, GUI launch, settings, and animation selector.

Consolidated from:
- test_avatar_api.py (animation listing and path traversal)
- test_avatar_gui.py (GUI window creation and fallback)
- test_avatar_settings.py (avatar config GET/PUT)
- test_avatar_selector.py (animation label selection)
"""

import json
import unittest
import unittest.mock
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.app import CommandExecutor
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.avatars.avatar_gui import run_avatar_gui
from chatty_commander.web.routes.avatar_api import router as avatar_router
from chatty_commander.web.routes.avatar_selector import router as selector_router
from chatty_commander.web.routes.avatar_settings import include_avatar_settings_routes
from chatty_commander.web.server import create_app
from chatty_commander.web.web_mode import WebModeServer


class _DummyConfig:
    def __init__(self) -> None:
        self.general_models_path = "models-idle"
        self.system_models_path = "models-computer"
        self.chat_models_path = "models-chatty"
        self.config = {"model_actions": {}}
        self.advisors = {"enabled": True}


# ---------------------------------------------------------------------------
# Animation listing (router-level)
# ---------------------------------------------------------------------------


class TestAvatarAnimationsRouter:
    """Test avatar animation listing via the isolated router."""

    def test_list_animations_endpoint(self, tmp_path: Path):
        anim_dir = tmp_path / "anims"
        anim_dir.mkdir()
        allowed = ["think_idle.webm", "hack_loop.mp4", "speak.gif", "error.png"]
        for name in allowed:
            (anim_dir / name).write_bytes(b"x")
        (anim_dir / "notes.txt").write_text("ignore")

        app = FastAPI()
        app.include_router(avatar_router)
        client = TestClient(app)

        with unittest.mock.patch(
            "chatty_commander.web.routes.avatar_api._default_animations_dir",
            return_value=tmp_path,
        ):
            resp = client.get("/avatar/animations", params={"dir": "anims"})
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["count"] == 4
            files = {a["file"] for a in data["animations"]}
            assert files == set(allowed)
            categories = {a["name"]: a["category"] for a in data["animations"]}
            assert categories["think_idle"] in ("thinking", "idle")
            assert categories["hack_loop"] in ("tool_calling", "processing")

    def test_list_animations_path_traversal(self, tmp_path: Path):
        app = FastAPI()
        app.include_router(avatar_router)
        client = TestClient(app)

        with unittest.mock.patch(
            "chatty_commander.web.routes.avatar_api._default_animations_dir",
            return_value=tmp_path,
        ):
            resp = client.get("/avatar/animations", params={"dir": "../"})
            assert resp.status_code == 403

            resp = client.get("/avatar/animations", params={"dir": "/tmp"})
            assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Animation listing (full-app / WebModeServer)
# ---------------------------------------------------------------------------


class TestAvatarAnimationsFullApp:
    """Test avatar animations through create_app and WebModeServer."""

    def test_nonexistent_dir_returns_404(self):
        app = create_app(no_auth=True)
        client = TestClient(app)
        r = client.get("/avatar/animations", params={"dir": "path/does/not/exist"})
        assert r.status_code == 404

    def test_lists_allowed_files(self, tmp_path: Path):
        (tmp_path / "anims").mkdir()
        (tmp_path / "anims" / "think.gif").write_bytes(b"gifdata")
        (tmp_path / "anims" / "speak.mp4").write_bytes(b"mp4data")
        (tmp_path / "anims" / "meta.json").write_text(json.dumps({"name": "meta"}))
        (tmp_path / "anims" / "notes.txt").write_text("x")  # disallowed ext

        cfg = _DummyConfig()
        sm = StateManager()
        mm = ModelManager(cfg)
        ce = CommandExecutor(cfg, mm, sm)
        server = WebModeServer(cfg, sm, mm, ce, no_auth=True)
        client = TestClient(server.app)

        with unittest.mock.patch(
            "chatty_commander.web.routes.avatar_api._default_animations_dir",
            return_value=tmp_path,
        ):
            r = client.get("/avatar/animations", params={"dir": "anims"})
            assert r.status_code == 200
            data = r.json()
            assert data["count"] >= 3
            names = {a["name"] for a in data["animations"]}
            assert {"think", "speak", "meta"}.issubset(names)


# ---------------------------------------------------------------------------
# GUI launch / headless behaviour
# ---------------------------------------------------------------------------


class TestAvatarGUI(unittest.TestCase):
    """Test run_avatar_gui window creation, fallback, and error paths."""

    @patch("chatty_commander.avatars.avatar_gui.webview")
    def test_creates_correct_window(self, mock_webview: MagicMock):
        mock_webview.create_window = MagicMock()
        mock_webview.start = MagicMock(return_value=None)
        rc = run_avatar_gui(debug=False)
        self.assertEqual(rc, 0)
        mock_webview.create_window.assert_called_once()
        _args, kwargs = mock_webview.create_window.call_args
        assert kwargs.get("frameless") is True
        assert kwargs.get("on_top") is True
        assert kwargs.get("transparent") is True
        assert kwargs.get("easy_drag") is True
        assert kwargs.get("title") == "Chatty Commander Avatar"
        url = kwargs.get("url")
        assert (
            isinstance(url, str)
            and url.startswith("file://")
            and url.endswith("index.html")
        )
        mock_webview.start.assert_called_once()

    @patch("chatty_commander.avatars.avatar_gui.webview", None)
    def test_missing_pywebview(self):
        rc = run_avatar_gui(debug=False)
        self.assertEqual(rc, 2)

    @patch("chatty_commander.avatars.avatar_gui.webview")
    def test_missing_index(self, mock_webview: MagicMock):
        with patch(
            "chatty_commander.avatars.avatar_gui._avatar_index_path",
            return_value=Path("does/not/exist.html"),
        ):
            rc = run_avatar_gui(debug=False)
            self.assertEqual(rc, 2)
            mock_webview.create_window.assert_not_called()
            mock_webview.start.assert_not_called()

    @patch("chatty_commander.avatars.avatar_gui.webview")
    def test_transparency_fallback_then_success(self, mock_webview: MagicMock):
        calls = {"i": 0}

        def create_window_side_effect(*args, **kwargs):
            calls["i"] += 1
            if calls["i"] == 1:
                raise RuntimeError("no transparency support")
            return None

        mock_webview.create_window = MagicMock(side_effect=create_window_side_effect)
        mock_webview.start = MagicMock(return_value=None)
        rc = run_avatar_gui(debug=False)
        self.assertEqual(rc, 0)
        assert mock_webview.create_window.call_count == 2
        mock_webview.start.assert_called_once()

    @patch("chatty_commander.avatars.avatar_gui.webview")
    def test_total_failure(self, mock_webview: MagicMock):
        mock_webview.create_window = MagicMock(side_effect=RuntimeError("boom"))
        mock_webview.start = MagicMock(return_value=None)
        rc = run_avatar_gui(debug=False)
        self.assertEqual(rc, 2)
        mock_webview.start.assert_not_called()


# ---------------------------------------------------------------------------
# Avatar settings API (GET / PUT)
# ---------------------------------------------------------------------------


class _StubCfg:
    def __init__(self):
        self.config = {}
        self.saved = False

    def save_config(self, *_args, **_kwargs):
        self.saved = True


class TestAvatarSettings:
    """Test avatar settings config endpoints."""

    def test_get_and_put(self):
        cfg = _StubCfg()
        app = FastAPI()
        app.include_router(
            include_avatar_settings_routes(get_config_manager=lambda: cfg)
        )
        client = TestClient(app)

        # GET defaults
        r = client.get("/avatar/config")
        assert r.status_code == 200
        data = r.json()
        assert data["enabled"] is True
        assert "state_map" in data and "thinking" in data["state_map"]

        # PUT update
        payload = {"enabled": False, "state_map": {"thinking": "think2"}}
        r2 = client.put("/avatar/config", json=payload)
        assert r2.status_code == 200, r2.text
        data2 = r2.json()
        assert data2["enabled"] is False
        assert data2["state_map"]["thinking"] == "think2"
        assert cfg.saved is True


# ---------------------------------------------------------------------------
# Animation selector (label classification)
# ---------------------------------------------------------------------------


class TestAvatarSelector:
    """Test animation label selector endpoint."""

    def test_basic_selection(self):
        app = FastAPI()
        app.include_router(selector_router)
        client = TestClient(app)

        resp = client.post(
            "/avatar/animation/choose",
            json={"text": "Let's call a tool to compute"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["label"] in ("hacking", "curious", "neutral")

        resp2 = client.post(
            "/avatar/animation/choose",
            json={
                "text": "Oops, an error occurred!",
                "candidate_labels": ["error", "success"],
            },
        )
        assert resp2.status_code == 200
        assert resp2.json()["label"] == "error"

    def test_labels_via_create_app(self):
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post("/avatar/animation/choose", json={"text": "calling tool now"})
        assert r.status_code == 200
        data = r.json()
        assert data["label"] in {
            "hacking",
            "neutral",
            "error",
            "warning",
            "success",
            "excited",
            "curious",
            "calm",
        }

        r2 = client.post(
            "/avatar/animation/choose",
            json={"text": "oops failure", "candidate_labels": ["error"]},
        )
        assert r2.status_code == 200
        data2 = r2.json()
        assert data2["label"] == "error"
