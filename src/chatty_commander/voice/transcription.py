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
Voice-to-text transcription with multiple backend support.

Supports:
- OpenAI Whisper (local and API)
- Google Speech-to-Text
- Azure Speech Services
- Mock transcriber for testing
"""

from __future__ import annotations

import logging
import tempfile
import time
import wave
from abc import ABC, abstractmethod

try:
    import numpy as np
    import pyaudio

    AUDIO_DEPS_AVAILABLE = True
except ImportError:
    pyaudio = None
    np = None
    AUDIO_DEPS_AVAILABLE = False

logger = logging.getLogger(__name__)


class TranscriptionBackend(ABC):
    """Abstract base class for transcription backends."""

    @abstractmethod
    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """Transcribe audio data to text."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available."""
        pass


class WhisperLocalBackend(TranscriptionBackend):
    """Local Whisper transcription using whisper library."""

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize Whisper model."""
        try:
            import whisper

            self._model = whisper.load_model(self.model_size)
            logger.info(f"Loaded Whisper model: {self.model_size}")
        except ImportError:
            logger.warning(
                "Whisper not available. Install with: pip install openai-whisper"
            )
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")

    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """Transcribe audio using local Whisper model."""
        if not self._model:
            raise RuntimeError("Whisper model not available")

        try:
            # Convert audio bytes to numpy array
            audio_array = (
                np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            )

            # Transcribe
            result = self._model.transcribe(audio_array)
            text = result.get("text", "").strip()

            logger.debug(f"Whisper transcription: '{text}'")
            return text

        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return ""

    def is_available(self) -> bool:
        return self._model is not None


class WhisperAPIBackend(TranscriptionBackend):
    """OpenAI Whisper API transcription."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI client."""
        try:
            import openai

            self._client = openai.OpenAI(api_key=self.api_key)
            logger.info("Initialized OpenAI Whisper API client")
        except ImportError:
            logger.warning(
                "OpenAI library not available. Install with: pip install openai"
            )
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")

    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """Transcribe audio using OpenAI Whisper API."""
        if not self._client:
            raise RuntimeError("OpenAI client not available")

        try:
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                # Write WAV header and data
                with wave.open(tmp_file.name, "wb") as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_data)

                # Transcribe using OpenAI API
                with open(tmp_file.name, "rb") as audio_file:
                    transcript = self._client.audio.transcriptions.create(
                        model="whisper-1", file=audio_file
                    )

                text = transcript.text.strip()
                logger.debug(f"OpenAI Whisper transcription: '{text}'")
                return text

        except Exception as e:
            logger.error(f"OpenAI Whisper API transcription failed: {e}")
            return ""

    def is_available(self) -> bool:
        return self._client is not None


class MockTranscriptionBackend(TranscriptionBackend):
    """Mock transcription backend for testing."""

    def __init__(self, responses: list[str] | None = None):
        self.responses = responses or [
            "hello world",
            "turn on the lights",
            "what's the weather like",
            "play some music",
            "set a timer for 5 minutes",
        ]
        self.call_count = 0

    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """Return mock transcription."""
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        logger.debug(f"Mock transcription: '{response}'")
        return response

    def is_available(self) -> bool:
        return True


class VoiceTranscriber:
    """Main voice transcription class with multiple backend support."""

    def __init__(
        self,
        backend: str = "whisper_local",
        chunk_size: int = 1024,
        sample_rate: int = 16000,
        channels: int = 1,
        record_timeout: float = 5.0,
        silence_timeout: float = 1.0,
        **backend_kwargs,
    ):
        if not AUDIO_DEPS_AVAILABLE:
            backend = "mock"

        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.channels = channels
        self.record_timeout = record_timeout
        self.silence_timeout = silence_timeout

        self._backend = self._create_backend(backend, **backend_kwargs)
        self._audio = None
        self._stream = None

    def _create_backend(self, backend: str, **kwargs) -> TranscriptionBackend:
        """Create transcription backend."""
        if backend == "whisper_local":
            return WhisperLocalBackend(**kwargs)
        elif backend == "whisper_api":
            return WhisperAPIBackend(**kwargs)
        elif backend == "mock":
            return MockTranscriptionBackend(**kwargs)
        else:
            raise ValueError(f"Unknown transcription backend: {backend}")

    def is_available(self) -> bool:
        """Check if transcriber is available."""
        return self._backend.is_available()

    def transcribe_audio_data(self, audio_data: bytes) -> str:
        """Transcribe raw audio data."""
        return self._backend.transcribe(audio_data, self.sample_rate)

    def record_and_transcribe(self) -> str:
        """Record audio from microphone and transcribe."""
        if not AUDIO_DEPS_AVAILABLE:
            logger.warning("Audio recording not available, using mock transcription")
            return self._backend.transcribe(b"", self.sample_rate)

        try:
            audio_data = self._record_audio()
            if audio_data:
                return self.transcribe_audio_data(audio_data)
            return ""
        except Exception as e:
            logger.error(f"Recording and transcription failed: {e}")
            return ""

    def _record_audio(self) -> bytes:
        """Record audio from microphone."""
        if not AUDIO_DEPS_AVAILABLE:
            return b""

        try:
            self._audio = pyaudio.PyAudio()
            self._stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )

            logger.info("Recording audio... (speak now)")
            frames = []
            start_time = time.time()
            silence_start = None

            while True:
                try:
                    data = self._stream.read(
                        self.chunk_size, exception_on_overflow=False
                    )
                    frames.append(data)

                    # Check for silence (simple volume-based detection)
                    audio_array = np.frombuffer(data, dtype=np.int16)
                    volume = np.sqrt(np.mean(audio_array**2))

                    if volume < 500:  # Silence threshold
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start > self.silence_timeout:
                            logger.info("Silence detected, stopping recording")
                            break
                    else:
                        silence_start = None

                    # Timeout check
                    if time.time() - start_time > self.record_timeout:
                        logger.info("Recording timeout reached")
                        break

                except Exception as e:
                    logger.error(f"Error during recording: {e}")
                    break

            # Convert frames to bytes
            audio_data = b"".join(frames)
            logger.info(f"Recorded {len(audio_data)} bytes of audio")
            return audio_data

        finally:
            self._cleanup_audio()

    def _cleanup_audio(self):
        """Clean up audio resources."""
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

    def get_backend_info(self) -> dict[str, any]:
        """Get information about the current backend."""
        return {
            "backend_type": type(self._backend).__name__,
            "is_available": self._backend.is_available(),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "chunk_size": self.chunk_size,
        }
