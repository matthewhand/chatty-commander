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

"""Attack-shaped tests for path traversal in the models routes.

Covers upload, download, and delete handlers in
``src/chatty_commander/web/routes/models.py``: ``../`` sequences, absolute
paths, and URL-encoded traversal must never read, write, or delete files
outside the model directories.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.routes.models import create_models_router


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    """Isolated working dir with model dirs and an out-of-bounds secret file.

    Layout:
        tmp_path/secret.onnx        <- must never be readable/deletable via API
        tmp_path/app/               <- cwd for the server
        tmp_path/app/wakewords/     <- upload dir
        tmp_path/app/models-idle/   <- contains a legit model
    """
    app_dir = tmp_path / "app"
    (app_dir / "wakewords").mkdir(parents=True)
    (app_dir / "models-idle").mkdir()
    (app_dir / "models-idle" / "legit.onnx").write_bytes(b"legit-model-bytes")

    secret = tmp_path / "secret.onnx"
    secret.write_bytes(b"out-of-bounds-secret")

    monkeypatch.chdir(app_dir)

    app = FastAPI()
    app.include_router(create_models_router())
    client = TestClient(app)
    return client, app_dir, secret


# ---------------------------------------------------------------------------
# Upload handler
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "evil_name",
    [
        "../evil.onnx",
        "../../evil.onnx",
        "../../secret.onnx",
        "/tmp/evil.onnx",
        "subdir/evil.onnx",
        "....//evil.onnx",
    ],
)
def test_upload_rejects_traversal_filenames(sandbox, tmp_path, evil_name):
    client, app_dir, _secret = sandbox
    resp = client.post(
        "/api/v1/models/upload",
        files={"file": (evil_name, b"payload", "application/octet-stream")},
    )
    assert resp.status_code == 400, resp.text
    # Nothing escaped: no new files anywhere outside the model dirs
    assert not (app_dir / "evil.onnx").exists()
    assert not (tmp_path / "evil.onnx").exists()
    assert not Path("/tmp/evil.onnx").exists()
    # The out-of-bounds file was not overwritten
    assert (tmp_path / "secret.onnx").read_bytes() == b"out-of-bounds-secret"
    # Upload dir stayed empty
    assert list((app_dir / "wakewords").iterdir()) == []


def test_upload_rejects_traversal_even_with_state(sandbox, tmp_path):
    """The state-selected target dir must be protected too."""
    client, app_dir, _secret = sandbox
    resp = client.post(
        "/api/v1/models/upload?state=idle",
        files={"file": ("../../secret.onnx", b"pwn", "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert (tmp_path / "secret.onnx").read_bytes() == b"out-of-bounds-secret"
    assert sorted(p.name for p in (app_dir / "models-idle").iterdir()) == ["legit.onnx"]


def test_upload_rejects_non_onnx_extension(sandbox):
    client, _app_dir, _secret = sandbox
    resp = client.post(
        "/api/v1/models/upload",
        files={"file": ("evil.sh", b"#!/bin/sh", "application/octet-stream")},
    )
    assert resp.status_code == 400


def test_upload_legit_filename_still_works(sandbox):
    client, app_dir, _secret = sandbox
    resp = client.post(
        "/api/v1/models/upload",
        files={"file": ("good.onnx", b"model-bytes", "application/octet-stream")},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["filename"] == "good.onnx"
    assert (app_dir / "wakewords" / "good.onnx").read_bytes() == b"model-bytes"

    # Duplicate upload is refused with 409 (no silent overwrite)
    resp2 = client.post(
        "/api/v1/models/upload",
        files={"file": ("good.onnx", b"other", "application/octet-stream")},
    )
    assert resp2.status_code == 409
    assert (app_dir / "wakewords" / "good.onnx").read_bytes() == b"model-bytes"


# ---------------------------------------------------------------------------
# Download handler
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "evil_path",
    [
        "..%2F..%2Fsecret.onnx",
        "..%2f..%2fsecret.onnx",
        "%2e%2e%2f%2e%2e%2fsecret.onnx",
        "..",
        "..%5C..%5Csecret.onnx",
    ],
)
def test_download_rejects_traversal(sandbox, evil_path):
    client, _app_dir, secret = sandbox
    resp = client.get(f"/api/v1/models/download/{evil_path}")
    assert resp.status_code == 404, resp.text
    assert secret.read_bytes() == b"out-of-bounds-secret"
    assert b"out-of-bounds-secret" not in resp.content


def test_download_absolute_path_rejected(sandbox, tmp_path):
    client, _app_dir, _secret = sandbox
    quoted = str(tmp_path / "secret.onnx").replace("/", "%2F")
    resp = client.get(f"/api/v1/models/download/{quoted}")
    assert resp.status_code == 404
    assert b"out-of-bounds-secret" not in resp.content


def test_download_legit_file_still_works(sandbox):
    client, _app_dir, _secret = sandbox
    resp = client.get("/api/v1/models/download/legit.onnx")
    assert resp.status_code == 200
    assert resp.content == b"legit-model-bytes"


# ---------------------------------------------------------------------------
# Delete handler
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "evil_path",
    [
        "..%2F..%2Fsecret.onnx",
        "%2e%2e%2f%2e%2e%2fsecret.onnx",
        "..",
        "..%5C..%5Csecret.onnx",
    ],
)
def test_delete_rejects_traversal(sandbox, evil_path):
    client, _app_dir, secret = sandbox
    resp = client.delete(f"/api/v1/models/files/{evil_path}")
    assert resp.status_code == 404, resp.text
    assert secret.exists()
    assert secret.read_bytes() == b"out-of-bounds-secret"


def test_delete_absolute_path_rejected(sandbox, tmp_path):
    client, _app_dir, secret = sandbox
    quoted = str(tmp_path / "secret.onnx").replace("/", "%2F")
    resp = client.delete(f"/api/v1/models/files/{quoted}")
    assert resp.status_code == 404
    assert secret.exists()


def test_delete_legit_file_still_works(sandbox):
    client, app_dir, _secret = sandbox
    resp = client.delete("/api/v1/models/files/legit.onnx")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert not (app_dir / "models-idle" / "legit.onnx").exists()


def test_delete_unknown_file_404(sandbox):
    client, _app_dir, _secret = sandbox
    resp = client.delete("/api/v1/models/files/nope.onnx")
    assert resp.status_code == 404
