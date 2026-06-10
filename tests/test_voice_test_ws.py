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

"""WebSocket tests for /ws/voice-test (in-browser voice testing, dry-run)."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.app.voice_test_pipeline import VoiceTestPipeline
from chatty_commander.web.routes.voice_test import (
    VOICE_TEST_WS_PATH,
    include_voice_test_routes,
)


class DummyConfigManager:
    model_actions = {
        "screenshot": {"action": "keypress", "keys": "ctrl+shift+x"},
        "open_jellyfin": {"action": "url", "url": "https://example.com/jellyfin"},
    }


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    cfg = DummyConfigManager()
    app.include_router(include_voice_test_routes(get_config_manager=lambda: cfg))
    return TestClient(app)


def _assert_event_shape(ev: dict) -> None:
    assert set(ev) == {"stage", "data", "ts"}
    assert isinstance(ev["data"], dict)
    assert isinstance(ev["ts"], str)


def test_start_frame_yields_listening_event(client: TestClient):
    with client.websocket_connect(VOICE_TEST_WS_PATH) as ws:
        ws.send_json({"type": "start", "dry_run": True, "sample_rate": 16000})
        ev = ws.receive_json()
        _assert_event_shape(ev)
        assert ev["stage"] == "listening"
        assert ev["data"]["dry_run"] is True
        assert ev["data"]["sample_rate"] == 16000
        assert "transcription_available" in ev["data"]


def test_text_simulation_produces_match_and_dry_run_action(client: TestClient):
    with client.websocket_connect(VOICE_TEST_WS_PATH) as ws:
        ws.send_json({"type": "start", "dry_run": True, "sample_rate": 16000})
        ws.receive_json()  # listening

        ws.send_json({"type": "text", "text": "please take a screenshot"})
        transcript = ws.receive_json()
        match = ws.receive_json()
        action = ws.receive_json()
        for ev in (transcript, match, action):
            _assert_event_shape(ev)
        assert transcript["stage"] == "transcript"
        assert transcript["data"]["text"] == "please take a screenshot"
        assert match["stage"] == "match"
        assert match["data"] == {"matched": True, "command": "screenshot"}
        assert action["stage"] == "action"
        assert action["data"]["dry_run"] is True
        assert action["data"]["executed"] is False
        assert action["data"]["description"] == "would press ctrl+shift+x"


def test_unknown_text_produces_no_match_event(client: TestClient):
    with client.websocket_connect(VOICE_TEST_WS_PATH) as ws:
        ws.send_json({"type": "text", "text": "gibberish flooble"})
        transcript = ws.receive_json()
        match = ws.receive_json()
        assert transcript["stage"] == "transcript"
        assert match["stage"] == "match"
        assert match["data"]["matched"] is False
        # No action event follows; the connection stays usable.
        ws.send_json({"type": "text", "text": "open jellyfin"})
        assert ws.receive_json()["stage"] == "transcript"
        assert ws.receive_json()["data"]["command"] == "open_jellyfin"
        assert (
            ws.receive_json()["data"]["description"]
            == "would open https://example.com/jellyfin"
        )


def test_malformed_frames_produce_error_events_not_crashes(client: TestClient):
    with client.websocket_connect(VOICE_TEST_WS_PATH) as ws:
        # Not JSON at all
        ws.send_text("{this is not json")
        ev = ws.receive_json()
        _assert_event_shape(ev)
        assert ev["stage"] == "error"

        # JSON but not an object
        ws.send_text("[1, 2, 3]")
        assert ws.receive_json()["stage"] == "error"

        # Unknown frame type
        ws.send_json({"type": "frobnicate"})
        ev = ws.receive_json()
        assert ev["stage"] == "error"
        assert ev["data"]["code"] == "unknown_type"

        # 'text' frame missing its text field
        ws.send_json({"type": "text"})
        assert ws.receive_json()["stage"] == "error"

        # Connection still works afterwards
        ws.send_json({"type": "text", "text": "screenshot"})
        assert ws.receive_json()["stage"] == "transcript"


def test_dry_run_false_is_refused_but_session_continues(client: TestClient):
    with client.websocket_connect(VOICE_TEST_WS_PATH) as ws:
        ws.send_json({"type": "start", "dry_run": False})
        refusal = ws.receive_json()
        assert refusal["stage"] == "error"
        assert refusal["data"]["code"] == "dry_run_only"
        listening = ws.receive_json()
        assert listening["stage"] == "listening"
        assert listening["data"]["dry_run"] is True  # forced dry-run


def test_audio_chunks_then_stop_degrades_without_backend(
    client: TestClient, monkeypatch
):
    # Force the "no real transcription backend" CI condition deterministically.
    monkeypatch.setattr(VoiceTestPipeline, "_resolve_transcriber", lambda self: None)
    with client.websocket_connect(VOICE_TEST_WS_PATH) as ws:
        ws.send_json({"type": "start", "dry_run": True, "sample_rate": 16000})
        ws.receive_json()
        ws.send_bytes(b"\x00\x01" * 1600)
        ws.send_json({"type": "stop"})
        ev = ws.receive_json()
        assert ev["stage"] == "error"
        assert ev["data"]["code"] == "transcription_unavailable"


def test_audio_then_stop_with_fake_backend_runs_full_pipeline(
    client: TestClient, monkeypatch
):
    class FakeTranscriber:
        def transcribe_audio_data(self, audio: bytes) -> str:
            assert audio  # buffered chunks arrive here
            return "take a screenshot"

    monkeypatch.setattr(
        VoiceTestPipeline, "_resolve_transcriber", lambda self: FakeTranscriber()
    )
    with client.websocket_connect(VOICE_TEST_WS_PATH) as ws:
        ws.send_json({"type": "start", "dry_run": True})
        ws.receive_json()
        ws.send_bytes(b"\x00\x01" * 1600)
        ws.send_json({"type": "stop"})
        transcript = ws.receive_json()
        match = ws.receive_json()
        action = ws.receive_json()
        assert transcript["stage"] == "transcript"
        assert transcript["data"]["simulated"] is False
        assert match["data"]["command"] == "screenshot"
        assert action["data"]["dry_run"] is True
        assert action["data"]["description"] == "would press ctrl+shift+x"


def test_stop_without_audio_reports_no_audio(client: TestClient):
    with client.websocket_connect(VOICE_TEST_WS_PATH) as ws:
        ws.send_json({"type": "stop"})
        ev = ws.receive_json()
        assert ev["stage"] == "error"
        assert ev["data"]["code"] == "no_audio"


def test_endpoint_registered_via_create_app_shared_routers():
    from chatty_commander.web.server import create_app

    app = create_app(no_auth=True, config_manager=DummyConfigManager())
    client = TestClient(app)
    with client.websocket_connect(VOICE_TEST_WS_PATH) as ws:
        ws.send_json({"type": "text", "text": "screenshot"})
        assert ws.receive_json()["stage"] == "transcript"
        assert ws.receive_json()["data"]["command"] == "screenshot"
        assert ws.receive_json()["data"]["executed"] is False


def test_websocket_bypasses_http_auth_middleware_like_existing_ws():
    """AuthMiddleware (BaseHTTPMiddleware) covers HTTP /api/* only; WebSocket
    connections bypass it — documented exemption matching /ws and /avatar/ws.
    Safe here because the endpoint is structurally dry-run."""
    from chatty_commander.web.server import create_app

    cfg = DummyConfigManager()
    cfg.auth = {"api_key": "sekrit"}  # type: ignore[attr-defined]
    app = create_app(no_auth=False, config_manager=cfg)
    client = TestClient(app)
    # No X-API-Key supplied, connection still succeeds (middleware exemption).
    with client.websocket_connect(VOICE_TEST_WS_PATH) as ws:
        ws.send_json({"type": "start", "dry_run": True})
        assert ws.receive_json()["stage"] == "listening"
