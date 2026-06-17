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

"""Light‑weight text‑to‑speech helpers.

This module provides a small facade around optional text‑to‑speech backends.  The
default implementation uses :mod:`pyttsx3` when it is installed which offers an
offline, cross‑platform speech engine.  When the dependency or audio stack is
missing the system gracefully falls back to an in‑memory mock backend so unit
tests can run without additional requirements.

Optional backends
------------------
* **pyttsx3** (default) — offline, cross‑platform; no network.
* **edge / edge-tts** — Microsoft Edge neural voices via the ``edge-tts`` PyPI
  package (``pip install 'chatty-commander[tts-edge]'``).  This backend is
  *optional*, *keyless* (no API key required) and *free*, but it is **cloud
  based and therefore REQUIRES network access** — it streams synthesis from
  Microsoft's online service over a websocket.  It is never the default; when
  unavailable the facade transparently falls back to the mock backend.
* **mock** — in‑memory recorder used by tests / as the universal fallback.

The :func:`synthesize_to_file` helper exposes the edge-tts file synthesis path
without any audio playback, which is handy for demos and for generating audio
fixtures (e.g. the dograh loopback test).  Note that edge-tts emits MP3; callers
that need 16‑bit PCM WAV must convert separately (ffmpeg/pydub).
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
import threading
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)

#: Default Microsoft Edge neural voice used by the edge-tts backend.
DEFAULT_EDGE_VOICE = "en-US-AriaNeural"

try:  # pragma: no cover - optional dependency
    import pyttsx3  # type: ignore
except Exception:  # pragma: no cover - handled gracefully
    pyttsx3 = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import edge_tts  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully
    edge_tts = None  # type: ignore


def _run_coro_sync(coro):
    """Run *coro* to completion from sync code, even if a loop is running.

    Uses :func:`asyncio.run` when no event loop is active; otherwise executes the
    coroutine on a dedicated thread with its own loop to avoid clashing with an
    already-running loop (e.g. inside async server handlers).
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No running loop in this thread — safe to use asyncio.run directly.
        return asyncio.run(coro)

    # A loop is already running; offload to a worker thread with its own loop.
    result: dict[str, object] = {}

    def _worker() -> None:
        result["value"] = asyncio.run(coro)

    thread = threading.Thread(target=_worker)
    thread.start()
    thread.join()
    return result.get("value")


async def _edge_save(text: str, path: str, voice: str) -> None:
    """Synthesize *text* with edge-tts and save the audio to *path*."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(path)


def synthesize_to_file(
    text: str,
    path: str | os.PathLike[str],
    voice: str = DEFAULT_EDGE_VOICE,
) -> Path:
    """Synthesize *text* to an audio file at *path* using edge-tts.

    This is a thin, playback-free wrapper around the async edge-tts ``save`` API
    suitable for demos and fixture generation.  The output format is whatever
    edge-tts produces (MP3).

    :param text: Text to synthesize.
    :param path: Destination file path for the audio.
    :param voice: Edge neural voice name (defaults to :data:`DEFAULT_EDGE_VOICE`).
    :returns: The :class:`~pathlib.Path` that was written.
    :raises RuntimeError: if the ``edge-tts`` package is not installed.

    .. note:: edge-tts is cloud based and requires network access.
    """
    if edge_tts is None:
        raise RuntimeError(
            "edge-tts backend is not available; install with "
            "'pip install chatty-commander[tts-edge]'"
        )
    target = Path(path)
    _run_coro_sync(_edge_save(text, str(target), voice))
    return target


class TTSBackend(ABC):
    """Abstract interface for text‑to‑speech backends."""

    @abstractmethod
    def speak(self, text: str) -> None:  # pragma: no cover - interface
        pass

    @abstractmethod
    def is_available(self) -> bool:  # pragma: no cover - interface
        """Return ``True`` if the backend can synthesize speech."""
<<<<<<< HEAD
=======
        pass
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16


class Pyttsx3Backend(TTSBackend):
    """Backend powered by :mod:`pyttsx3`."""

    def __init__(self) -> None:
        self._engine = None
        if pyttsx3 is not None:
            try:
                self._engine = pyttsx3.init()
            except Exception as exc:  # pragma: no cover - environment specific
                logger.warning("Failed to initialise pyttsx3: %s", exc)
                self._engine = None
        else:
            logger.info("pyttsx3 not installed; falling back to mock TTS backend")

    def speak(self, text: str) -> None:  # pragma: no cover - requires audio stack
        if not self._engine:
            raise RuntimeError("pyttsx3 backend is not available")
        self._engine.say(text)
        self._engine.runAndWait()

    def is_available(self) -> bool:
        return self._engine is not None


class EdgeTTSBackend(TTSBackend):
    """Backend powered by Microsoft Edge neural voices via :mod:`edge_tts`.

    Optional, keyless and free, but **cloud based** — it streams synthesis from
    Microsoft's online service and therefore requires network access.  Output is
    MP3; this backend synthesizes to a temporary file and then plays it back
    best-effort using whatever audio player is available on the host, degrading
    to a logged warning when none is found (no heavy playback dependency is
    pulled in).
    """

    #: Audio players tried (in order) for best-effort playback.
    _PLAYERS = ("ffplay", "afplay", "aplay", "mpg123", "mpv", "cvlc")

    def __init__(self, voice: str = DEFAULT_EDGE_VOICE) -> None:
        self.voice = voice
        if edge_tts is None:
            logger.info("edge-tts not installed; falling back to mock TTS backend")

    def is_available(self) -> bool:
        return edge_tts is not None

    def _play_file(self, path: str) -> None:
        """Best-effort playback of *path*; warn (don't raise) if unsupported."""
        try:  # optional, lightweight dependency if present
            import playsound  # type: ignore

            playsound.playsound(path)
            return
        except Exception:
            pass

        for player in self._PLAYERS:
            exe = shutil.which(player)
            if not exe:
                continue
            args = [exe]
            if player == "ffplay":
                args += ["-nodisp", "-autoexit", "-loglevel", "quiet"]
            elif player == "cvlc":
                args += ["--play-and-exit", "--quiet"]
            args.append(path)
            try:
                subprocess.run(args, check=False)
                return
            except Exception as exc:  # pragma: no cover - environment specific
                logger.debug("Playback via %s failed: %s", player, exc)

        logger.warning(
            "edge-tts synthesized audio but no audio player was found; "
            "skipping playback (file: %s)",
            path,
        )

    def speak(self, text: str) -> None:
        if edge_tts is None:
            raise RuntimeError("edge-tts backend is not available")
        fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        try:
            _run_coro_sync(_edge_save(text, tmp_path, self.voice))
            self._play_file(tmp_path)
        finally:
            try:
                os.remove(tmp_path)
            except OSError:  # pragma: no cover - best effort cleanup
                pass


class MockTTSBackend(TTSBackend):
    """In‑memory backend that records spoken text for tests."""

    def __init__(self) -> None:
        self.spoken: list[str] = []

    def speak(self, text: str) -> None:
        self.spoken.append(text)

    def is_available(self) -> bool:
        return True


class TextToSpeech:
    """Facade that selects an appropriate :class:`TTSBackend`."""

<<<<<<< HEAD
    def __init__(
        self,
        backend: str = "pyttsx3",
        *,
        voice: str = DEFAULT_EDGE_VOICE,
        **kwargs,
    ) -> None:
=======
    def __init__(self, backend: str = "pyttsx3", **kwargs) -> None:
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        if backend == "pyttsx3":
            self.backend: TTSBackend = Pyttsx3Backend()
            if not self.backend.is_available():
                # Fall back to mock backend transparently
                self.backend = MockTTSBackend()
        elif backend in ("edge", "edge-tts"):
            self.backend = EdgeTTSBackend(voice=voice)
            if not self.backend.is_available():
                # edge-tts requires the optional dependency + network; fall back.
                self.backend = MockTTSBackend()
        elif backend == "mock":
            self.backend = MockTTSBackend()
        else:
            raise ValueError(f"Unknown TTS backend: {backend}")

    def speak(self, text: str) -> None:
        try:
            self.backend.speak(text)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("TTS failure: %s", exc)

    def is_available(self) -> bool:
        return self.backend.is_available()

<<<<<<< HEAD
    def get_backend_info(self) -> dict[str, str | bool]:
=======
    def get_backend_info(self) -> dict:
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        return {
            "backend_type": type(self.backend).__name__,
            "is_available": self.backend.is_available(),
        }


__all__ = [
    "TextToSpeech",
    "MockTTSBackend",
    "Pyttsx3Backend",
    "EdgeTTSBackend",
    "synthesize_to_file",
    "DEFAULT_EDGE_VOICE",
]
