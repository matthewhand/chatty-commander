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

import json
import unittest.mock
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.app import CommandExecutor
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.routes.avatar_api import router as avatar_router
from chatty_commander.web.server import create_app
from chatty_commander.web.web_mode import WebModeServer


class _DummyConfig:
    def __init__(self) -> None:
        self.general_models_path = "models-idle"
        self.system_models_path = "models-computer"
        self.chat_models_path = "models-chatty"
        self.config = {"model_actions": {}}
        self.advisors = {"enabled": True}


# --- router-level tests (lightweight FastAPI) ---


def test_list_animations_endpoint(tmp_path: Path):
    """List animations via the isolated router."""
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


def test_list_animations_path_traversal(tmp_path: Path):
    """Path-traversal attempts must be rejected."""
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


# --- full-app error tests ---


def test_avatar_animations_nonexistent_dir_returns_404():
    """Querying a directory that does not exist should 404."""
    app = create_app(no_auth=True)
    client = TestClient(app)
    r = client.get("/avatar/animations", params={"dir": "path/does/not/exist"})
    assert r.status_code == 404


# --- full WebModeServer integration test ---


def test_avatar_animations_lists_allowed_files(tmp_path: Path):
    """List allowed animation files through the full server stack."""
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
