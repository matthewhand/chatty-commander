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

"""Shared transcript -> command matching used by BOTH voice pipelines.

The real :class:`~chatty_commander.voice.pipeline.VoicePipeline` (the source of
truth for what actually executes) and the dry-run
:class:`~chatty_commander.app.voice_test_pipeline.VoiceTestPipeline` (the
in-browser "Voice Test" feature) previously each carried their own copy of the
word-boundary matcher and keyword table. The copies drifted — the voice-test
table was missing the ``play_music`` aliases the real pipeline had — so the
browser dry-run could report "no match" for an utterance the real pipeline
would happily execute. This module is the single source so they cannot diverge.

Matching is word-boundary aware (not naive substring): a command named "play"
does not match words like "replay"/"display"/"player", and an underscore-joined
command name like "play_music" matches the spoken phrase "play music". Single
word phrases require an exact token; multi-word phrases require the token
sequence to appear contiguously.
"""

from __future__ import annotations

import re
from typing import Any


def get_keyword_map() -> dict[str, list[str]]:
    """Return the keyword (alias) mapping used for fuzzy command matching.

    This is the canonical table. Keep additions here (and only here) so both
    pipelines stay in sync.
    """
    return {
        "hello": ["hello", "hi", "hey", "greet"],
        "lights": ["lights", "light", "lamp", "illumination"],
        "music": ["music", "song", "play", "audio"],
        "play_music": ["music", "song", "play", "audio"],
        "weather": ["weather", "temperature", "forecast"],
        "time": ["time", "clock", "hour"],
        "timer": ["timer", "alarm", "remind"],
    }


def matches_phrase(phrase: str, tokens: list[str]) -> bool:
    """Return True if ``phrase`` appears as a whole word/phrase in ``tokens``.

    ``tokens`` is the already-tokenized transcript (lowercase word tokens).
    Single-word phrases require an exact token match; multi-word phrases
    require the token sequence to appear contiguously.
    """
    phrase = phrase.lower().strip()
    if not phrase:
        return False
    phrase_tokens = re.findall(r"[a-z0-9']+", phrase)
    if not phrase_tokens:
        return False
    if len(phrase_tokens) == 1:
        return phrase_tokens[0] in tokens
    n = len(phrase_tokens)
    for i in range(len(tokens) - n + 1):
        if tokens[i : i + n] == phrase_tokens:
            return True
    return False


def tokenize(text: str) -> list[str]:
    """Tokenize a transcript into lowercase word tokens."""
    return re.findall(r"[a-z0-9']+", text.lower())


def match_command(text: str, model_actions: dict[str, Any] | None) -> str | None:
    """Match a transcript against configured commands.

    Two-phase, mirroring the real voice pipeline exactly:

    1. Direct name match: the first command whose (underscore-as-separator)
       name appears as a whole word/phrase in the transcript.
    2. Keyword alias match: the first command present in ``model_actions``
       whose keyword table entry has a whole-word/phrase hit.

    Returns the matched command name, or ``None``.
    """
    if not text or not isinstance(model_actions, dict) or not model_actions:
        return None

    tokens = tokenize(text)

    # Direct name match first (whole-word/phrase, not substring).
    for command_name in model_actions:
        if matches_phrase(str(command_name), tokens):
            return str(command_name)

    # Keyword-based aliases (only for commands present in model_actions).
    for command_name, keywords in get_keyword_map().items():
        if command_name in model_actions:
            for keyword in keywords:
                if matches_phrase(keyword, tokens):
                    return command_name

    return None
