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

"""Dry-run voice testing pipeline for the in-browser "Voice Test" feature.

Runs the same shape as the local voice pipeline (wakeword -> transcript ->
command match -> action) but NEVER executes real actions: the action stage
only *describes* what would run ("would press ctrl+shift+x") by inspecting the
matched command's configuration (``config.model_actions`` — the same mapping
``CommandExecutor`` dispatches on).

Degrades gracefully when wakeword models / transcription backends are absent
(the normal situation in CI): text simulation frames feed a transcript
directly into command matching, and the real-audio path reports
``transcription_unavailable`` instead of crashing.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

# Hard cap on buffered browser audio (bytes). 16 MiB is ~8.5 minutes of
# 16 kHz/16-bit mono PCM — far beyond any sensible voice-test utterance.
MAX_AUDIO_BUFFER_BYTES = 16 * 1024 * 1024

# Stages emitted to the browser, in pipeline order.
STAGES = ("listening", "wakeword", "transcript", "match", "action", "error")


def stage_event(stage: str, data: dict[str, Any]) -> dict[str, Any]:
    """Build a server->client stage event: ``{stage, data, ts}``."""
    return {
        "stage": stage,
        "data": data,
        "ts": datetime.now(UTC).isoformat(),
    }


def match_command(text: str, model_actions: dict[str, Any]) -> str | None:
    """Match a transcript against configured commands.

    Mirrors ``voice.pipeline.VoicePipeline._match_command``: whole-word /
    contiguous-phrase matching against command names (underscores in names
    are treated as word separators), then a small keyword table for common
    aliases. Substring matching is deliberately avoided so a command named
    "play" does not match "replay" or "display".
    """
    if not text or not isinstance(model_actions, dict) or not model_actions:
        return None

    tokens = re.findall(r"[a-z0-9']+", text.lower())
    token_set = set(tokens)

    def _matches_phrase(phrase: str) -> bool:
        phrase_tokens = re.findall(r"[a-z0-9']+", phrase.lower().strip())
        if not phrase_tokens:
            return False
        if len(phrase_tokens) == 1:
            return phrase_tokens[0] in token_set
        n = len(phrase_tokens)
        return any(
            tokens[i : i + n] == phrase_tokens for i in range(len(tokens) - n + 1)
        )

    # Direct name match first (whole-word, not substring).
    for command_name in model_actions:
        if _matches_phrase(str(command_name)):
            return str(command_name)

    # Keyword-based aliases (same table as the local voice pipeline).
    command_keywords = {
        "hello": ["hello", "hi", "hey", "greet"],
        "lights": ["lights", "light", "lamp", "illumination"],
        "music": ["music", "song", "play", "audio"],
        "weather": ["weather", "temperature", "forecast"],
        "time": ["time", "clock", "hour"],
        "timer": ["timer", "alarm", "remind"],
    }
    for command_name, keywords in command_keywords.items():
        if command_name in model_actions and any(_matches_phrase(k) for k in keywords):
            return command_name

    return None


def describe_dry_run(command_name: str, action: Any) -> str:
    """Describe what executing ``command_name`` WOULD do, without doing it.

    Inspects the same action shapes ``CommandExecutor.execute_command``
    dispatches on (new ``{"action": ...}`` format and the legacy direct-key
    format).
    """
    if not isinstance(action, dict):
        return f"would execute command '{command_name}'"

    def _keys_text(keys: Any) -> str:
        if isinstance(keys, list | tuple):
            return "+".join(str(k) for k in keys)
        return str(keys)

    action_type = action.get("action")
    if action_type == "keypress" or (action_type is None and "keypress" in action):
        keys = action.get("keys") if action_type else action.get("keypress")
        return f"would press {_keys_text(keys)}"
    if action_type == "url" or (action_type is None and "url" in action):
        return f"would open {action.get('url', '')}"
    if action_type == "shell" or (action_type is None and "shell" in action):
        cmd = action.get("cmd") if action_type else action.get("shell")
        return f"would run shell command: {cmd}"
    if action_type == "custom_message":
        return f"would display message: {action.get('message', '')}"
    if action_type == "voice_chat":
        return "would start a voice chat session"
    if action_type == "dograh_call":
        return f"would place dograh call (workflow {action.get('workflow_id')})"
    return f"would execute command '{command_name}'"


class VoiceTestPipeline:
    """One per WebSocket session. Dry-run only — never executes actions."""

    def __init__(self, config_manager: Any = None, transcriber: Any = None) -> None:
        self.config_manager = config_manager
        self.dry_run = True  # the only supported mode in this iteration
        self.sample_rate = 16000
        self._audio_buffer = bytearray()
        # Sentinel-based lazy resolution: None means "resolved, unavailable".
        self._transcriber = transcriber
        self._transcriber_resolved = transcriber is not None

    # ------------------------------------------------------------------ config

    @property
    def model_actions(self) -> dict[str, Any]:
        actions = getattr(self.config_manager, "model_actions", None)
        return actions if isinstance(actions, dict) else {}

    # ------------------------------------------------------------- transcriber

    def _resolve_transcriber(self) -> Any:
        """Find a *real* transcription backend, or None.

        ``VoiceTranscriber`` silently falls back to a mock backend that
        returns canned phrases when audio deps are missing (the CI case);
        a mock would mislead browser users, so it is treated as unavailable.
        """
        if self._transcriber_resolved:
            return self._transcriber
        self._transcriber_resolved = True
        try:
            from chatty_commander.voice.transcription import VoiceTranscriber

            transcriber = VoiceTranscriber(backend="whisper_local")
            backend = getattr(transcriber, "_backend", None)
            if type(backend).__name__ == "MockTranscriptionBackend":
                logger.info("voice-test: only mock transcription available; disabled")
            elif transcriber.is_available():
                self._transcriber = transcriber
        except Exception as e:  # pragma: no cover - depends on host audio stack
            logger.info("voice-test: transcription backend unavailable: %s", e)
        return self._transcriber

    @property
    def transcription_available(self) -> bool:
        return self._resolve_transcriber() is not None

    # ------------------------------------------------------------------ stages

    def start(self, sample_rate: int = 16000) -> dict[str, Any]:
        """Begin a session; returns the initial ``listening`` event."""
        if isinstance(sample_rate, int) and 8000 <= sample_rate <= 192000:
            self.sample_rate = sample_rate
        self._audio_buffer.clear()
        return stage_event(
            "listening",
            {
                "dry_run": True,
                "sample_rate": self.sample_rate,
                "transcription_available": self.transcription_available,
            },
        )

    def feed_audio(self, chunk: bytes) -> dict[str, Any] | None:
        """Buffer a binary audio chunk; returns an error event if over cap."""
        if len(self._audio_buffer) + len(chunk) > MAX_AUDIO_BUFFER_BYTES:
            return stage_event(
                "error",
                {
                    "code": "audio_buffer_full",
                    "message": "audio buffer limit exceeded; chunk dropped",
                },
            )
        self._audio_buffer.extend(chunk)
        return None

    def finish_audio(self) -> list[dict[str, Any]]:
        """Transcribe buffered audio (if a real backend exists) and match."""
        audio = bytes(self._audio_buffer)
        self._audio_buffer.clear()
        if not audio:
            return [
                stage_event(
                    "error",
                    {"code": "no_audio", "message": "no audio received before stop"},
                )
            ]
        transcriber = self._resolve_transcriber()
        if transcriber is None:
            return [
                stage_event(
                    "error",
                    {
                        "code": "transcription_unavailable",
                        "message": (
                            "no transcription backend available; "
                            "use {'type': 'text'} simulation frames instead"
                        ),
                    },
                )
            ]
        try:
            text = transcriber.transcribe_audio_data(audio)
        except Exception as e:
            return [
                stage_event(
                    "error",
                    {"code": "transcription_failed", "message": str(e)},
                )
            ]
        return self.process_text(str(text or ""), simulated=False)

    def process_text(
        self, text: str, *, simulated: bool = True
    ) -> list[dict[str, Any]]:
        """Run a transcript through matching; emit transcript/match/action.

        DRY-RUN ONLY: the action event describes what would run; nothing is
        ever executed from here.
        """
        events = [stage_event("transcript", {"text": text, "simulated": simulated})]
        command = match_command(text, self.model_actions)
        if command is None:
            events.append(stage_event("match", {"matched": False, "text": text}))
            return events
        events.append(stage_event("match", {"matched": True, "command": command}))
        action = self.model_actions.get(command)
        events.append(
            stage_event(
                "action",
                {
                    "command": command,
                    "dry_run": True,
                    "executed": False,
                    "description": describe_dry_run(command, action),
                },
            )
        )
        return events
