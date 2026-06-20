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

"""WebSocket endpoint for in-browser voice testing (ROADMAP P2).

Path: ``/ws/voice-test``

Client -> server frames:
  - JSON text frames (control):
      ``{"type": "start", "dry_run": true, "sample_rate": 16000}``
      ``{"type": "text", "text": "take a screenshot"}``   (audio-less simulation)
      ``{"type": "stop"}``                                  (finalize buffered audio)
  - Binary frames: raw PCM/webm audio chunks (buffered until ``stop``).

Server -> client frames (always JSON):
  ``{"stage": "listening"|"wakeword"|"transcript"|"match"|"action"|"error",
     "data": {...}, "ts": "<ISO-8601>"}``

DRY-RUN ONLY: action events describe what WOULD run; nothing is executed.

Auth note: the project's ``AuthMiddleware`` is a Starlette
``BaseHTTPMiddleware`` — it dispatches only HTTP requests and only enforces
API keys on ``/api/*`` paths. WebSocket connections bypass it entirely, so
``/ws/voice-test`` is unauthenticated by the middleware, the same exemption
as the existing ``/ws`` and ``/avatar/ws`` endpoints. This is acceptable for
this iteration precisely because the endpoint is structurally dry-run: it can
describe configured actions but never execute them.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from chatty_commander.app.voice_test_pipeline import VoiceTestPipeline, stage_event

logger = logging.getLogger(__name__)

VOICE_TEST_WS_PATH = "/ws/voice-test"


def _error(message: str, code: str = "bad_frame") -> dict[str, Any]:
    return stage_event("error", {"code": code, "message": message})


async def _handle_control_frame(
    websocket: WebSocket, pipeline: VoiceTestPipeline, raw: str
) -> None:
    """Parse and dispatch one JSON control frame; never raises on bad input."""
    try:
        frame = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        await websocket.send_json(_error("frame is not valid JSON"))
        return
    if not isinstance(frame, dict):
        await websocket.send_json(_error("frame must be a JSON object"))
        return

    frame_type = frame.get("type")
    if frame_type == "start":
        if frame.get("dry_run") is False:
            await websocket.send_json(
                _error(
                    "live execution is not supported; session runs in dry-run mode",
                    code="dry_run_only",
                )
            )
        sample_rate = frame.get("sample_rate", 16000)
        if not isinstance(sample_rate, int):
            sample_rate = 16000
        await websocket.send_json(pipeline.start(sample_rate=sample_rate))
    elif frame_type == "text":
        text = frame.get("text")
        if not isinstance(text, str) or not text.strip():
            await websocket.send_json(
                _error("'text' frame requires a non-empty string 'text' field")
            )
            return
        for event in pipeline.process_text(text):
            await websocket.send_json(event)
    elif frame_type == "stop":
        for event in await pipeline.finish_audio():
            await websocket.send_json(event)
    else:
        await websocket.send_json(
            _error(f"unknown frame type: {frame_type!r}", code="unknown_type")
        )


def include_voice_test_routes(*, get_config_manager: Callable[[], Any]) -> APIRouter:
    """Build the voice-test WebSocket router bound to a config accessor."""
    router = APIRouter()

    @router.websocket(VOICE_TEST_WS_PATH)
    async def voice_test_ws(websocket: WebSocket) -> None:
        await websocket.accept()
        pipeline = VoiceTestPipeline(config_manager=get_config_manager())
        try:
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break
                if message.get("bytes") is not None:
                    event = pipeline.feed_audio(message["bytes"])
                    if event is not None:
                        await websocket.send_json(event)
                    continue
                text = message.get("text")
                if text is None:
                    continue
                await _handle_control_frame(websocket, pipeline, text)
        except WebSocketDisconnect:
            logger.info("voice-test client disconnected")
        except Exception as err:  # noqa: BLE001 - never crash the server loop
            logger.error("voice-test websocket error: %s", err)

    return router


def register_voice_test_routes(app: Any, config_manager: Any = None) -> None:
    """Single-call registration hook used by ``server.register_shared_routers``."""
    app.include_router(
        include_voice_test_routes(get_config_manager=lambda: config_manager)
    )
