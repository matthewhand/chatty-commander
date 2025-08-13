"""
Wake word detection using OpenWakeWord.

Supports multiple wake words and provides confidence scoring.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

try:
    import numpy as np
    import openwakeword
    import pyaudio

    VOICE_DEPS_AVAILABLE = True
except ImportError:
    openwakeword = None
    pyaudio = None
    np = None
    VOICE_DEPS_AVAILABLE = False

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """Wake word detector using OpenWakeWord."""

    def __init__(
        self,
        wake_words: list[str] | None = None,
        threshold: float = 0.5,
        chunk_size: int = 1280,  # 80ms at 16kHz
        sample_rate: int = 16000,
        channels: int = 1,
    ):
        if not VOICE_DEPS_AVAILABLE:
            raise ImportError(
                "Voice dependencies not available. Install with: "
                "pip install openwakeword pyaudio numpy"
            )

        self.wake_words = wake_words or ["hey_jarvis", "alexa"]
        self.threshold = threshold
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.channels = channels

        self._model = None
        self._audio = None
        self._stream = None
        self._running = False
        self._thread = None
        self._callbacks: list[Callable[[str, float], None]] = []

        self._initialize_model()

    def _initialize_model(self):
        """Initialize OpenWakeWord model."""
        try:
            # Initialize with default models
            self._model = openwakeword.Model()
            logger.info(f"Initialized wake word model with words: {self.wake_words}")
        except Exception as e:
            logger.error(f"Failed to initialize wake word model: {e}")
            raise

    def add_callback(self, callback: Callable[[str, float], None]) -> None:
        """Add callback for wake word detection.

        Args:
            callback: Function called with (wake_word, confidence) when detected
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[str, float], None]) -> None:
        """Remove wake word detection callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def start_listening(self) -> None:
        """Start listening for wake words."""
        if self._running:
            logger.warning("Wake word detector already running")
            return

        try:
            self._audio = pyaudio.PyAudio()
            self._stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )

            self._running = True
            self._thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._thread.start()
            logger.info("Started wake word detection")

        except Exception as e:
            logger.error(f"Failed to start wake word detection: {e}")
            self.stop_listening()
            raise

    def stop_listening(self) -> None:
        """Stop listening for wake words."""
        self._running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception as e:
                logger.warning(f"Error closing audio stream: {e}")
            finally:
                self._stream = None

        if self._audio:
            try:
                self._audio.terminate()
            except Exception as e:
                logger.warning(f"Error terminating audio: {e}")
            finally:
                self._audio = None

        logger.info("Stopped wake word detection")

    def _listen_loop(self) -> None:
        """Main listening loop."""
        logger.debug("Wake word detection loop started")

        while self._running:
            try:
                # Read audio chunk
                audio_data = self._stream.read(self.chunk_size, exception_on_overflow=False)
                audio_array = np.frombuffer(audio_data, dtype=np.int16)

                # Get predictions from model
                predictions = self._model.predict(audio_array)

                # Check for wake word detections
                for wake_word in self.wake_words:
                    if wake_word in predictions:
                        confidence = predictions[wake_word]
                        if confidence >= self.threshold:
                            logger.info(
                                f"Wake word detected: {wake_word} (confidence: {confidence:.3f})"
                            )
                            self._notify_callbacks(wake_word, confidence)

            except Exception as e:
                if self._running:  # Only log if we're supposed to be running
                    logger.error(f"Error in wake word detection loop: {e}")
                    time.sleep(0.1)  # Brief pause before retrying

    def _notify_callbacks(self, wake_word: str, confidence: float) -> None:
        """Notify all registered callbacks of wake word detection."""
        for callback in self._callbacks.copy():  # Copy to avoid modification during iteration
            try:
                callback(wake_word, confidence)
            except Exception as e:
                logger.error(f"Error in wake word callback: {e}")

    def get_available_models(self) -> list[str]:
        """Get list of available wake word models."""
        if not self._model:
            return []

        try:
            return list(self._model.models.keys())
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []

    def is_listening(self) -> bool:
        """Check if detector is currently listening."""
        return self._running and self._thread and self._thread.is_alive()


class MockWakeWordDetector:
    """Mock wake word detector for testing/development without audio hardware."""

    def __init__(self, *args, **kwargs):
        self._callbacks: list[Callable[[str, float], None]] = []
        self._running = False
        logger.info("Using mock wake word detector (no audio hardware required)")

    def add_callback(self, callback: Callable[[str, float], None]) -> None:
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[str, float], None]) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def start_listening(self) -> None:
        self._running = True
        logger.info("Mock wake word detector started")

    def stop_listening(self) -> None:
        self._running = False
        logger.info("Mock wake word detector stopped")

    def trigger_wake_word(self, wake_word: str = "hey_jarvis", confidence: float = 0.9) -> None:
        """Manually trigger a wake word detection (for testing)."""
        if self._running:
            for callback in self._callbacks:
                try:
                    callback(wake_word, confidence)
                except Exception as e:
                    logger.error(f"Error in mock wake word callback: {e}")

    def get_available_models(self) -> list[str]:
        return ["hey_jarvis", "alexa", "hey_google"]

    def is_listening(self) -> bool:
        return self._running
