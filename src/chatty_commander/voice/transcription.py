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
import os
import tempfile
import time
import wave
from abc import ABC, abstractmethod
from typing import Any

try:
    import numpy as np
    import pyaudio

    AUDIO_DEPS_AVAILABLE = True
except ImportError:
    pyaudio = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]
    AUDIO_DEPS_AVAILABLE = False

logger = logging.getLogger(__name__)


class TranscriptionBackend(ABC):
    """Abstract base class for transcription backends."""

    @abstractmethod
    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
<<<<<<< HEAD
        """Check if backend is available."""
=======
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        pass


class WhisperLocalBackend(TranscriptionBackend):
    """Local Whisper transcription using whisper library."""

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None
        self._initialize_model()

    def _initialize_model(self):
        try:
<<<<<<< HEAD
=======
    
            
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            import whisper

            self._model = whisper.load_model(self.model_size)
            logger.info(f"Loaded Whisper model: {self.model_size}")
<<<<<<< HEAD
=======

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        except ImportError:
            logger.warning(
                "Whisper not available. Install with: pip install openai-whisper"
            )
<<<<<<< HEAD
=======

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")

    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """Transcribe audio using local Whisper model."""
        if not self._model:
<<<<<<< HEAD
            raise RuntimeError("Whisper model not available")

        try:
=======
            
            raise RuntimeError("Whisper model not available")

        try:

        
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            # Convert audio bytes to numpy array
            audio_array = (
                np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            )

            # Transcribe
            result = self._model.transcribe(audio_array)
            text = result.get("text", "").strip()

            logger.debug(f"Whisper transcription: '{text}'")
            return text

<<<<<<< HEAD
=======

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return ""

    def is_available(self) -> bool:
        return self._model is not None


class WhisperAPIBackend(TranscriptionBackend):
    """OpenAI Whisper API transcription."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self._client: Any = None
        self._initialize_client()

    def _initialize_client(self):
        try:
<<<<<<< HEAD
=======
    
            
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            import openai

            self._client = openai.OpenAI(api_key=self.api_key)
            logger.info("Initialized OpenAI Whisper API client")
<<<<<<< HEAD
=======

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        except ImportError:
            logger.warning(
                "OpenAI library not available. Install with: pip install openai"
            )
<<<<<<< HEAD
=======

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")

    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """Transcribe audio using OpenAI Whisper API."""
        if not self._client:
<<<<<<< HEAD
=======
            
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            raise RuntimeError("OpenAI client not available")

        tmp_path: str | None = None
        try:
<<<<<<< HEAD
            # Create temporary WAV file (delete=False so we can reopen it for
            # upload; cleaned up in the finally block below).
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
                # Write WAV header and data
                with wave.open(tmp_file.name, "wb") as wav_file:
=======
    
            
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                
                # Write WAV header and data
                with wave.open(tmp_file.name, "wb") as wav_file:
                    
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_data)

                # Transcribe using OpenAI API
                with open(tmp_file.name, "rb") as audio_file:
<<<<<<< HEAD
=======
                    
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                    transcript = self._client.audio.transcriptions.create(
                        model="whisper-1", file=audio_file
                    )

                text = transcript.text.strip()
                logger.debug(f"OpenAI Whisper transcription: '{text}'")
                return text  # type: ignore[no-any-return]

<<<<<<< HEAD
=======

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        except Exception as e:
            logger.error(f"OpenAI Whisper API transcription failed: {e}")
            return ""
        finally:
            # Always remove the temp file so repeated calls don't leak files.
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

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
<<<<<<< HEAD
=======
            
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        ]
        self.call_count = 0

    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
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
        silence_threshold: float = 500.0,
        **backend_kwargs,
    ):
        if not AUDIO_DEPS_AVAILABLE:
<<<<<<< HEAD
=======
            
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            backend = "mock"

        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.channels = channels
        self.record_timeout = record_timeout
        self.silence_timeout = silence_timeout
        # RMS energy (root-mean-square of int16 samples) below which a chunk is
        # considered silence. The scale is environment-dependent: quieter rooms
        # may want a lower value, noisier ones a higher value. Exposed here so it
        # can be tuned via config rather than being hardcoded in the record loop.
        self.silence_threshold = silence_threshold

        self._backend = self._create_backend(backend, **backend_kwargs)
        self._audio = None
        self._stream = None

    def _create_backend(self, backend: str, **kwargs) -> TranscriptionBackend:
<<<<<<< HEAD
        """Create transcription backend."""
        if backend == "whisper_local":
            return WhisperLocalBackend(**kwargs)
        elif backend == "whisper_api":
            return WhisperAPIBackend(**kwargs)
        elif backend == "mock":
=======
        if backend == "whisper_local":
            
            return WhisperLocalBackend(**kwargs)
        elif backend == "whisper_api":
            
            return WhisperAPIBackend(**kwargs)
        elif backend == "mock":
            
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            return MockTranscriptionBackend(**kwargs)
        else:
            raise ValueError(f"Unknown transcription backend: {backend}")

    def is_available(self) -> bool:
<<<<<<< HEAD
        """Check if transcriber is available."""
=======
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        return self._backend.is_available()

    def transcribe_audio_data(self, audio_data: bytes) -> str:
        """Transcribe raw audio data."""
        return self._backend.transcribe(audio_data, self.sample_rate)

    def record_and_transcribe(self) -> str:
<<<<<<< HEAD
        """Record audio from microphone and transcribe."""
        if not AUDIO_DEPS_AVAILABLE:
=======
        if not AUDIO_DEPS_AVAILABLE:
            
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            logger.warning("Audio recording not available, using mock transcription")
            return self._backend.transcribe(b"", self.sample_rate)

        try:
<<<<<<< HEAD
            audio_data = self._record_audio()
            if audio_data:
                return self.transcribe_audio_data(audio_data)
            return ""
=======
    
            
            audio_data = self._record_audio()
            if audio_data:
                
                return self.transcribe_audio_data(audio_data)
            return ""

>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        except Exception as e:
            logger.error(f"Recording and transcription failed: {e}")
            return ""

    def _record_audio(self) -> bytes:
        """Record audio from microphone."""
        if not AUDIO_DEPS_AVAILABLE:
<<<<<<< HEAD
            return b""

        try:
=======
            
            return b""

        try:
    
            
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            self._audio = pyaudio.PyAudio()
            self._stream = self._audio.open(  # type: ignore[attr-defined]
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
<<<<<<< HEAD
                try:
=======
                
                try:
                    
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                    data = self._stream.read(  # type: ignore[attr-defined]
                        self.chunk_size, exception_on_overflow=False
                    )
                    frames.append(data)

                    # Check for silence (simple volume-based detection)
                    audio_array = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                    volume = np.sqrt(np.dot(audio_array, audio_array) / len(audio_array))

<<<<<<< HEAD
                    if volume < self.silence_threshold:  # RMS silence threshold
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start > self.silence_timeout:
=======
                    if volume < 500:  # Silence threshold
                        
                        if silence_start is None:
                            
                            silence_start = time.time()
                        elif time.time() - silence_start > self.silence_timeout:
                            
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
                            logger.info("Silence detected, stopping recording")
                            break
                    else:
                        silence_start = None

                    # Timeout check
                    if time.time() - start_time > self.record_timeout:
<<<<<<< HEAD
                        logger.info("Recording timeout reached")
                        break

=======
                        
                        logger.info("Recording timeout reached")
                        break

        
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
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
<<<<<<< HEAD
        """Clean up audio resources."""
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
=======
        if self._stream:
            
            try:
                
                self._stream.stop_stream()
                self._stream.close()
    
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            except Exception as e:
                logger.warning(f"Error closing audio stream: {e}")
            finally:
                self._stream = None

        if self._audio:
<<<<<<< HEAD
            try:
                self._audio.terminate()
=======
            
            try:
                
                self._audio.terminate()
    
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
            except Exception as e:
                logger.warning(f"Error terminating audio: {e}")
            finally:
                self._audio = None

    def get_backend_info(self) -> dict[str, Any]:
<<<<<<< HEAD
        """Get information about the current backend."""
=======
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
        return {
            "backend_type": type(self._backend).__name__,
            "is_available": self._backend.is_available(),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "chunk_size": self.chunk_size,
        }

