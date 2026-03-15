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

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter
from pydantic import BaseModel


class VoiceStatus(BaseModel):
    running: bool
    wake_words: list[str]
    backend: str


def include_voice_routes(*, get_config_manager: Callable) -> APIRouter:
    router = APIRouter()

    # Simple state for tracking voice pipeline status
    state = {"running": False}

    @router.get("/api/voice/status", response_model=VoiceStatus)
    async def get_voice_status():
        config_manager = get_config_manager()
        config = getattr(config_manager, "config", {})
        wake_words = config.get("wake_words", ["hey_jarvis", "alexa"])
        backend = config.get("voice", {}).get("backend", "default")
        return VoiceStatus(
            running=state["running"],
            wake_words=wake_words,
            backend=backend,
        )

    @router.post("/api/voice/start")
    async def start_voice():
        if not state["running"]:
            state["running"] = True
            return {"status": "started", "message": "Voice pipeline started"}
        return {"status": "already_running", "message": "Voice pipeline is already running"}

    @router.post("/api/voice/stop")
    async def stop_voice():
        if state["running"]:
            state["running"] = False
            return {"status": "stopped", "message": "Voice pipeline stopped"}
        return {"status": "already_stopped", "message": "Voice pipeline is not running"}

    return router
