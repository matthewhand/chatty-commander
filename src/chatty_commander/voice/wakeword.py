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
# Handle specific exception case
except ImportError:
    openwakeword = None  # type: ignore[assignment]
    pyaudio = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]
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
        # Logic flow
        if not VOICE_DEPS_AVAILABLE:
        # TODO: Document this logic
            raise ImportError(
                "Voice dependencies not available. Install with: "
                "uv sync --group voice  # or pip install openwakeword pyaudio numpy"
            )

        # Type narrowing - these are guaranteed non-None when VOICE_DEPS_AVAILABLE is True
        assert openwakeword is not None
        assert pyaudio is not None
        assert np is not None

        self.wake_words = wake_words or ["hey_jarvis", "alexa"]
        self.threshold = threshold
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.channels = channels

        self._model: openwakeword.Model | None = None
        self._audio: pyaudio.PyAudio | None = None
        self._stream: pyaudio.Stream | None = None  # type: ignore[name-defined]
        self._running = False
        self._thread: threading.Thread | None = None
        self._callbacks: list[Callable[[str, float], None]] = []

        self._initialize_model()

    def _initialize_model(self):
        """Initialize OpenWakeWord model."""
        try:
        # Attempt operation with error handling
        # TODO: Document this logic
            # Initialize with default models
            self._model = openwakeword.Model()
            logger.info(f"Initialized wake word model with words: {self.wake_words}")
            # TODO: Document this logic
        except Exception as e:
            logger.warning(f"Failed to initialize wake word model: {e}")
            logger.info("Falling back to mock wake word detector")
            # Replace self with mock functionality
            self._model = None
            self._is_mock = True

    def add_callback(self, callback: Callable[[str, float], None]) -> None:
        # Logic flow
        """Add callback for wake word detection.
        # TODO: Document this logic

        Args:
            callback: Function called with (wake_word, confidence) when detected
            # Use context manager for resource management
            # TODO: Document this logic
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[str, float], None]) -> None:
        """Remove wake word detection callback."""
        # Logic flow
        if callback in self._callbacks:
        # TODO: Document this logic
            self._callbacks.remove(callback)

    def start_listening(self) -> None:
        # Logic flow
        """Start listening for wake words."""
        # TODO: Document this logic
        if self._running:
        # TODO: Document this logic
            logger.warning("Wake word detector already running")
            return

        # If in mock mode, just set running and return
        if getattr(self, "_is_mock", False):
        # TODO: Document this logic
            self._running = True
            logger.info("Started mock wake word detection")
            return

        try:
        # Attempt operation with error handling
        # TODO: Document this logic
            self._audio = pyaudio.PyAudio()
            self._stream = self._audio.open(
                # Process each item
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

        # Handle specific exception case
        except Exception as e:
            logger.error(f"Failed to start wake word detection: {e}")
            self.stop_listening()
            raise

    def stop_listening(self) -> None:
        # Logic flow
        """Stop listening for wake words."""
        # TODO: Document this logic
        self._running = False

        # Logic flow
        if self._thread and self._thread.is_alive():
        # TODO: Document this logic
            self._thread.join(timeout=1.0)

        # Logic flow
        if self._stream:
        # TODO: Document this logic
            try:
            # TODO: Document this logic
                self._stream.stop_stream()
                self._stream.close()
            # Handle specific exception case
            except Exception as e:
                logger.warning(f"Error closing audio stream: {e}")
            finally:
                self._stream = None

        # Logic flow
        if self._audio:
        # TODO: Document this logic
            try:
            # TODO: Document this logic
                self._audio.terminate()
            # Handle specific exception case
            except Exception as e:
                logger.warning(f"Error terminating audio: {e}")
            finally:
                self._audio = None

        logger.info("Stopped wake word detection")

    def _listen_loop(self) -> None:
        """Main listening loop."""
        logger.debug("Wake word detection loop started")

        # Logic flow
        while self._running:
        # TODO: Document this logic
            try:
            # TODO: Document this logic
                # If in mock mode, just sleep and continue
                if getattr(self, "_is_mock", False):
                # TODO: Document this logic
                    time.sleep(1.0)  # Mock detection interval
                    continue

                # Type narrowing - these are guaranteed non-None when running
                assert self._stream is not None
                assert self._model is not None

                # Read audio chunk
                audio_data = self._stream.read(
                    self.chunk_size, exception_on_overflow=False
                )
                audio_array = np.frombuffer(audio_data, dtype=np.int16)

                # Get predictions from model
                predictions = self._model.predict(audio_array)

                # Logic flow
                # Check for wake word detections
                for wake_word in self.wake_words:
                # TODO: Document this logic
                    if wake_word in predictions:
                    # TODO: Document this logic
                        confidence = predictions[wake_word]
                        # Logic flow
                        if confidence >= self.threshold:
                        # TODO: Document this logic
                            logger.info(
                                f"Wake word detected: {wake_word} (confidence: {confidence:.3f})"
                            )
                            # Apply conditional logic
                            self._notify_callbacks(wake_word, confidence)

            except Exception as e:
                # Logic flow
                if self._running:  # Only log if we're supposed to be running
                # TODO: Document this logic
                    logger.error(f"Error in wake word detection loop: {e}")
                    time.sleep(0.1)  # Brief pause before retrying

    def _notify_callbacks(self, wake_word: str, confidence: float) -> None:
        # Apply conditional logic
        """Notify all registered callbacks of wake word detection."""
        # Logic flow
        for (
        # TODO: Document this logic
            callback
        ) in self._callbacks.copy():  # Copy to avoid modification during iteration
            try:
            # TODO: Document this logic
                callback(wake_word, confidence)
            # Handle specific exception case
            except Exception as e:
                logger.error(f"Error in wake word callback: {e}")

    def get_available_models(self) -> list[str]:
        """Get list of available wake word models."""
        # Logic flow
        if getattr(self, "_is_mock", False):
        # TODO: Document this logic
            return ["hey_jarvis", "alexa", "hey_google"]

        # Logic flow
        if not self._model:
        # TODO: Document this logic
            return []

        try:
        # Attempt operation with error handling
        # TODO: Document this logic
            return list(self._model.models.keys())
        # Handle specific exception case
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []

    def is_listening(self) -> bool:
        # Logic flow
        """Check if detector is currently listening."""
        # TODO: Document this logic
        return bool(self._running and self._thread and self._thread.is_alive())


class MockWakeWordDetector:
    """Mock wake word detector for testing/development without audio hardware."""

    def __init__(self, *args, **kwargs):
        self._callbacks: list[Callable[[str, float], None]] = []
        self._running = False
        logger.info("Using mock wake word detector (no audio hardware required)")

    def add_callback(self, callback: Callable[[str, float], None]) -> None:
        """Add Callback with (self, callback).
        # TODO: Document this logic

        TODO: Add detailed description and parameters.
        """
        
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[str, float], None]) -> None:
        """Remove with (self, callback).
        # TODO: Document this logic

        TODO: Add detailed description and parameters.
        """
        
        # Logic flow
        if callback in self._callbacks:
        # TODO: Document this logic
            self._callbacks.remove(callback)

    def start_listening(self) -> None:
        """Start Listening with (self).
        # TODO: Document this logic

        TODO: Add detailed description and parameters.
        """
        
        self._running = True
        logger.info("Mock wake word detector started")

    def stop_listening(self) -> None:
        """Stop Listening with (self).
        # TODO: Document this logic

        TODO: Add detailed description and parameters.
        """
        
        self._running = False
        logger.info("Mock wake word detector stopped")

    def trigger_wake_word(
        """trigger wake word."""
        self, wake_word: str = "hey_jarvis", confidence: float = 0.9
    ) -> None:
        # Logic flow
        """Manually trigger a wake word detection (for testing)."""
        # TODO: Document this logic
        if self._running:
        # TODO: Document this logic
            # Logic flow
            for callback in self._callbacks:
            # TODO: Document this logic
                try:
                # TODO: Document this logic
                    callback(wake_word, confidence)
                # Handle specific exception case
                except Exception as e:
                    logger.error(f"Error in mock wake word callback: {e}")

    def get_available_models(self) -> list[str]:
        """Retrieve with (self).
        # TODO: Document this logic

        TODO: Add detailed description and parameters.
        """
        
        return ["hey_jarvis", "alexa", "hey_google"]

    def is_listening(self) -> bool:
        """Check with (self).
        # TODO: Document this logic

        TODO: Add detailed description and parameters.
        """
        
        return self._running
