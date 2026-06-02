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
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

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


_ALL_LABELS = set(_HINTS.keys()) | {"neutral"}


def _hint_classify(text: str, allowed) -> AnimationChooseResponse:
    """Deterministic keyword-hint classifier used as the reliable fallback."""
    for label, keywords in _HINTS.items():
        if not allowed(label):
            continue
        if any(k in text for k in keywords):
            return AnimationChooseResponse(
                label=label,
                confidence=0.8,
                rationale="keyword-hint match",
            )
    return AnimationChooseResponse(
        label="neutral", confidence=0.5, rationale="no keyword match (default)"
    )


def _llm_classify(text: str, allowed_labels: set[str]) -> str | None:
    """Attempt an LLM-backed classification.

    Returns a single normalized label string if the active LLM backend produced
    a recognisable label, otherwise ``None`` so the caller can fall back to the
    deterministic hint classifier. Any failure (missing backend, network error,
    unparseable output) is swallowed and reported as ``None`` — the endpoint must
    never crash just because an optional LLM is unavailable.
    """
    try:
        from ...llm.manager import get_global_llm_manager
    except Exception:  # pragma: no cover - import guard
        return None

    try:
        manager = get_global_llm_manager()
        if not manager.is_available():
            return None
        options = ", ".join(sorted(allowed_labels))
        prompt = (
            "Classify the emotional/animation intent of the following assistant "
            "text into exactly one of these labels: "
            f"{options}.\n"
            "Respond with ONLY the single label word, nothing else.\n\n"
            f"Text: {text!r}\nLabel:"
        )
        raw = manager.generate_response(prompt)
    except Exception as exc:  # noqa: BLE001 - optional dependency, degrade gracefully
        logger.debug("LLM animation classification unavailable: %s", exc)
        return None

    if not isinstance(raw, str):
        return None
    # Be tolerant of extra whitespace/punctuation around the label, but require
    # an exact label token match so prose responses (e.g. the mock backend) fall
    # back to the deterministic classifier rather than producing garbage.
    candidates = {
        tok.strip(" \t\r\n.,:;!\"'`").lower()
        for tok in raw.replace("\n", " ").split(" ")
    }
    candidates.add(raw.strip(" \t\r\n.,:;!\"'`").lower())
    for label in allowed_labels:
        if label in candidates:
            return label
    return None


@router.post("/avatar/animation/choose", response_model=AnimationChooseResponse)
async def choose_animation(req: AnimationChooseRequest) -> Any:
    try:
        text = (req.text or "").lower()
        labels = set(req.candidate_labels or [])
        if labels:
            labels &= _ALL_LABELS

        def allowed(label: str) -> bool:
            return (not labels) or (label in labels)

        allowed_labels = labels or _ALL_LABELS

        # Prefer an LLM-backed classification when a backend is available; the
        # helper returns None (and we fall back to hints) on any failure or when
        # the output is not a recognisable label.
        llm_label = _llm_classify(text, allowed_labels)
        if llm_label is not None and allowed(llm_label):
            return AnimationChooseResponse(
                label=llm_label,
                confidence=0.9,
                rationale="llm classification",
            )

        # Deterministic keyword-hint fallback (also used when no LLM is present).
        return _hint_classify(text, allowed)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
