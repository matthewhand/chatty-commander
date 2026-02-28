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

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

AllowedLabel = Literal[
    "excited", "calm", "curious", "warning", "success", "error", "neutral", "hacking"
]


class AnimationChooseRequest(BaseModel):
    text: str = Field(..., description="Text to classify")
    candidate_labels: list[str] | None = Field(
        default=None, description="Optional subset of allowed labels"
    )


class AnimationChooseResponse(BaseModel):
    label: str
    confidence: float = 0.5
    rationale: str | None = None


_HINTS = {
    "hacking": ["tool", "call", "compute", "hack", "mcp"],
    "error": ["error", "fail", "exception", "oops"],
    "warning": ["warn", "caution", "risky"],
    "success": ["success", "done", "completed", "great"],
    "excited": ["amazing", "wow", "excited"],
    "curious": ["hmm", "curious", "think"],
    "calm": ["calm", "steady"],
}


@router.post("/avatar/animation/choose", response_model=AnimationChooseResponse)
async def choose_animation(req: AnimationChooseRequest) -> Any:
    try:
        text = (req.text or "").lower()
        labels = set(req.candidate_labels or [])
        if labels:
            labels &= set(_HINTS.keys()) | {"neutral"}

        def allowed(label: str) -> bool:
            return (not labels) or (label in labels)

        for label, keywords in _HINTS.items():
            if not allowed(label):
                continue
            if any(k in text for k in keywords):
                return AnimationChooseResponse(label=label, confidence=0.8)
        return AnimationChooseResponse(label="neutral", confidence=0.5)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
