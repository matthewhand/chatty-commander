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

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

class VoiceStatusResponse(BaseModel):
    status: str = Field(..., description="Voice recognition status")
    is_listening: bool = Field(..., description="Whether voice recognition is active")
    last_command: str | None = Field(default=None, description="Last detected voice command")

class StartVoiceRequest(BaseModel):
    pass

class StopVoiceRequest(BaseModel):
    pass

@router.get("/api/voice/status", response_model=VoiceStatusResponse)
async def get_voice_status():
    """Get current voice recognition status."""
    # Placeholder: In a real implementation, this would query the voice engine.
    return VoiceStatusResponse(
        status="active",
        is_listening=True,
        last_command="N/A"
    )

@router.post("/api/voice/start")
async def start_voice_recognition():
    """Start voice recognition."""
    # Logic to start listening
    logger.info("Voice recognition started via API.")
    return {"message": "Voice recognition started"}

@router.post("/api/voice/stop")
async def stop_voice_recognition():
    """Stop voice recognition."""
    # Logic to stop listening
    logger.info("Voice recognition stopped via API.")
    return {"message": "Voice recognition stopped"}
