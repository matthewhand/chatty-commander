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

"""Tests for the audio device endpoints (GET /api/audio/devices, POST /api/audio/device)."""

from __future__ import annotations

import sys
import types

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.routes import audio as audio_module
from chatty_commander.web.routes.audio import include_audio_routes


class DummyConfigManager:
    """Minimal config manager mimicking app.config.Config."""

    def __init__(self) -> None:
        self.config: dict = {}
        self.saved = False

    def save_config(self) -> None:
        self.saved = True


class FailingSaveConfigManager(DummyConfigManager):
    def save_config(self) -> None:
        raise OSError("disk full")


def make_client(config_manager=None) -> TestClient:
    app = FastAPI()
    app.include_router(include_audio_routes(get_config_manager=lambda: config_manager))
    return TestClient(app)


def _install_fake_pyaudio(monkeypatch, devices):
    """Install a fake pyaudio module exposing the given device dicts."""

    class FakePyAudio:
        def get_host_api_info_by_index(self, index):
            assert index == 0
            return {"deviceCount": len(devices)}

        def get_device_info_by_host_api_device_index(self, host_api, index):
            return devices[index]

        def terminate(self):
            pass

    fake = types.ModuleType("pyaudio")
    fake.PyAudio = FakePyAudio
    monkeypatch.setitem(sys.modules, "pyaudio", fake)


# ---------------------------------------------------------------------------
# GET /api/audio/devices
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", ["/api/audio/devices", "/api/v1/audio/devices"])
def test_get_devices_success_with_pyaudio(monkeypatch, path):
    _install_fake_pyaudio(
        monkeypatch,
        [
            {"name": "Built-in Mic", "maxInputChannels": 2, "maxOutputChannels": 0},
            {"name": "Speakers", "maxInputChannels": 0, "maxOutputChannels": 2},
            {"name": "Headset", "maxInputChannels": 1, "maxOutputChannels": 2},
        ],
    )
    client = make_client(DummyConfigManager())
    resp = client.get(path)
    assert resp.status_code == 200
    data = resp.json()
    assert data == {
        "input": ["Built-in Mic", "Headset"],
        "output": ["Speakers", "Headset"],
        "available": True,
    }


@pytest.mark.parametrize("path", ["/api/audio/devices", "/api/v1/audio/devices"])
def test_get_devices_degrades_when_pyaudio_missing(monkeypatch, path):
    # A None entry in sys.modules makes `import pyaudio` raise ImportError.
    monkeypatch.setitem(sys.modules, "pyaudio", None)
    client = make_client(DummyConfigManager())
    resp = client.get(path)
    assert resp.status_code == 200
    assert resp.json() == {"input": [], "output": [], "available": False}


def test_get_devices_degrades_when_enumeration_fails(monkeypatch):
    fake = types.ModuleType("pyaudio")

    class Broken:
        def __init__(self):
            raise RuntimeError("no audio host")

    fake.PyAudio = Broken
    monkeypatch.setitem(sys.modules, "pyaudio", fake)

    client = make_client(DummyConfigManager())
    resp = client.get("/api/audio/devices")
    assert resp.status_code == 200
    assert resp.json() == {"input": [], "output": [], "available": False}


def test_get_devices_response_shape(monkeypatch):
    monkeypatch.setitem(sys.modules, "pyaudio", None)
    client = make_client(None)
    data = client.get("/api/audio/devices").json()
    assert set(data.keys()) == {"input", "output", "available"}
    assert isinstance(data["input"], list)
    assert isinstance(data["output"], list)
    assert isinstance(data["available"], bool)


# ---------------------------------------------------------------------------
# POST /api/audio/device
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", ["/api/audio/device", "/api/v1/audio/device"])
def test_set_device_success_persists_via_config_manager(path):
    cfg = DummyConfigManager()
    client = make_client(cfg)
    resp = client.post(path, json={"device_id": "Built-in Mic"})
    assert resp.status_code == 200
    assert resp.json() == {
        "success": True,
        "device": "Built-in Mic",
        "persisted": True,
    }
    assert cfg.config["audio"]["device"] == "Built-in Mic"
    assert cfg.saved is True


def test_set_device_without_config_manager_uses_module_state():
    client = make_client(None)
    resp = client.post("/api/audio/device", json={"device_id": "USB Headset"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["device"] == "USB Headset"
    assert body["persisted"] is False
    assert audio_module._selected_device["device_id"] == "USB Headset"


def test_set_device_save_failure_degrades_gracefully():
    cfg = FailingSaveConfigManager()
    client = make_client(cfg)
    resp = client.post("/api/audio/device", json={"device_id": "Mic"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["persisted"] is False
    # Selection still retained in module state.
    assert audio_module._selected_device["device_id"] == "Mic"


def test_set_device_rejects_empty_device_id():
    client = make_client(DummyConfigManager())
    resp = client.post("/api/audio/device", json={"device_id": "   "})
    assert resp.status_code == 400
    assert "device_id" in resp.json()["detail"]


def test_set_device_missing_body_field_returns_422():
    client = make_client(DummyConfigManager())
    resp = client.post("/api/audio/device", json={})
    assert resp.status_code == 422
