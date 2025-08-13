"""Light‑weight text‑to‑speech helpers.

This module provides a small facade around optional text‑to‑speech backends.  The
default implementation uses :mod:`pyttsx3` when it is installed which offers an
offline, cross‑platform speech engine.  When the dependency or audio stack is
missing the system gracefully falls back to an in‑memory mock backend so unit
tests can run without additional requirements.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import pyttsx3  # type: ignore
except Exception:  # pragma: no cover - handled gracefully
    pyttsx3 = None  # type: ignore


class TTSBackend(ABC):
    """Abstract interface for text‑to‑speech backends."""

    @abstractmethod
    def speak(self, text: str) -> None:  # pragma: no cover - interface
        """Synthesize ``text`` to audio output."""

    @abstractmethod
    def is_available(self) -> bool:  # pragma: no cover - interface
        """Return ``True`` if the backend can synthesize speech."""


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

    def __init__(self, backend: str = "pyttsx3", **kwargs) -> None:
        if backend == "pyttsx3":
            self.backend: TTSBackend = Pyttsx3Backend()
            if not self.backend.is_available():
                # Fall back to mock backend transparently
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

    def get_backend_info(self) -> dict[str, str | bool]:
        return {
            "backend_type": type(self.backend).__name__,
            "is_available": self.backend.is_available(),
        }


__all__ = ["TextToSpeech", "MockTTSBackend", "Pyttsx3Backend"]

