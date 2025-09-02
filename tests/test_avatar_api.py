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

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.routes.avatar_api import router as avatar_router


def test_list_animations_endpoint(tmp_path: Path):
    # Create a fake animations directory structure
    anim_dir = tmp_path / "anims"
    anim_dir.mkdir()
    # some allowed and disallowed files
    allowed = ["think_idle.webm", "hack_loop.mp4", "speak.gif", "error.png"]
    for name in allowed:
        (anim_dir / name).write_bytes(b"x")
    (anim_dir / "notes.txt").write_text("ignore")

    app = FastAPI()
    app.include_router(avatar_router)
    client = TestClient(app)
    resp = client.get("/avatar/animations", params={"dir": str(anim_dir)})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["count"] == 4
    files = {a["file"] for a in data["animations"]}
    assert files == set(allowed)
    # category hints should map at least some
    categories = {a["name"]: a["category"] for a in data["animations"]}
    assert categories["think_idle"] in ("thinking", "idle")
    assert categories["hack_loop"] in ("tool_calling", "processing")
