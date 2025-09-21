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

"""Enhanced voice processing with improved quality and intelligence.

TODO: This is an experimental implementation that needs testing and validation.
TODO: Verify all audio dependencies (pyaudio, whisper, etc.) are available.
TODO: Test noise reduction and VAD functionality.
TODO: Validate transcription accuracy with different engines.
TODO: Confirm wake word detection works reliably.
TODO: Test on different audio hardware configurations.
"""

import logging
import queue
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np


@dataclass
class VoiceProcessingConfig:
    """Configuration for enhanced voice processing."""

    sample_rate: int = 16000
    chunk_size: int = 1024
    noise_reduction_enabled: bool = True
    voice_activity_detection: bool = True
    echo_cancellation: bool = True
    auto_gain_control: bool = True
    confidence_threshold: float = 0.7
    silence_timeout: float = 2.0
    max_recording_duration: float = 30.0


@dataclass
class VoiceResult:
    """Result from voice processing."""

    text: str
    confidence: float
    duration: float
    timestamp: datetime
    language: str | None = None
    intent: str | None = None
    wake_word_detected: bool = False


class EnhancedVoiceProcessor:
    """Enhanced voice processor with improved quality and intelligence."""

    def __init__(self, config: VoiceProcessingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.processing_thread = None

        # Voice activity detection state
        self.vad_enabled = config.voice_activity_detection
        self.silence_counter = 0
        self.speech_detected = False

        # Audio processing components
        self.noise_reducer = None
        self.echo_canceller = None
        self.auto_gain = None

        # Transcription components
        self.transcriber = None
        self.wake_word_detector = None

        # Callbacks
        self.on_speech_start: Callable | None = None
        self.on_speech_end: Callable | None = None
        self.on_transcription: Callable[[VoiceResult], None] | None = None
        self.on_wake_word: Callable[[str], None] | None = None

        self._initialize_components()

    def _initialize_components(self):
        """Initialize voice processing components."""
        try:
            # Initialize noise reduction
            if self.config.noise_reduction_enabled:
                self._initialize_noise_reduction()

            # Initialize voice activity detection
            if self.config.voice_activity_detection:
                self._initialize_vad()

            # Initialize transcription
            self._initialize_transcription()

            # Initialize wake word detection
            self._initialize_wake_word_detection()

            self.logger.info("Enhanced voice processor initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize voice processor: {e}")

    def _initialize_noise_reduction(self):
        """Initialize noise reduction component."""
        try:
            # Try to use advanced noise reduction if available
            import noisereduce as nr

            self.noise_reducer = nr
            self.logger.info("Advanced noise reduction enabled")
        except ImportError:
            # Fallback to basic noise reduction
            self.noise_reducer = self._basic_noise_reduction
            self.logger.info("Basic noise reduction enabled")

    def _initialize_vad(self):
        """Initialize voice activity detection."""
        try:
            # Try to use webrtcvad if available
            import webrtcvad

            self.vad = webrtcvad.Vad(2)  # Aggressiveness level 2
            self.logger.info("WebRTC VAD enabled")
        except ImportError:
            # Fallback to energy-based VAD
            self.vad = self._energy_based_vad
            self.logger.info("Energy-based VAD enabled")

    def _initialize_transcription(self):
        """Initialize speech-to-text transcription."""
        try:
            # Try OpenAI Whisper first (best quality)
            import whisper

            self.transcriber = whisper.load_model("base")
            self.transcription_method = "whisper"
            self.logger.info("OpenAI Whisper transcription enabled")
        except ImportError:
            try:
                # Fallback to speech_recognition
                import speech_recognition as sr

                self.transcriber = sr.Recognizer()
                self.transcription_method = "speech_recognition"
                self.logger.info("SpeechRecognition transcription enabled")
            except ImportError:
                # Ultimate fallback
                self.transcriber = None
                self.transcription_method = "none"
                self.logger.warning("No transcription engine available")

    def _initialize_wake_word_detection(self):
        """Initialize wake word detection."""
        try:
            # Try to use porcupine for wake word detection
            import importlib.util

            if importlib.util.find_spec("pvporcupine") is not None:
                self.wake_word_detector = "porcupine"
                self.logger.info("Porcupine wake word detection enabled")
            else:
                raise ImportError("pvporcupine not available")
        except ImportError:
            # Fallback to simple keyword detection
            self.wake_word_detector = "simple"
            self.logger.info("Simple wake word detection enabled")

    def _basic_noise_reduction(self, audio_data: np.ndarray) -> np.ndarray:
        """Basic noise reduction using spectral subtraction."""
        # Simple high-pass filter to remove low-frequency noise
        from scipy import signal

        b, a = signal.butter(4, 300, btype="high", fs=self.config.sample_rate)
        return signal.filtfilt(b, a, audio_data)

    def _energy_based_vad(self, audio_chunk: bytes) -> bool:
        """Energy-based voice activity detection."""
        audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
        energy = np.sum(audio_data.astype(np.float32) ** 2) / len(audio_data)

        # Dynamic threshold based on recent energy levels
        threshold = 1000  # Adjust based on your environment
        return energy > threshold

    def _detect_wake_words(self, text: str) -> list[str]:
        """Detect wake words in transcribed text."""
        wake_words = ["hey chatty", "chatty", "hey computer", "computer"]
        detected = []

        text_lower = text.lower()
        for wake_word in wake_words:
            if wake_word in text_lower:
                detected.append(wake_word)

        return detected

    def _transcribe_audio(self, audio_data: np.ndarray) -> VoiceResult:
        """Transcribe audio data to text."""
        start_time = datetime.now()

        try:
            if self.transcription_method == "whisper" and self.transcriber:
                # Use Whisper for high-quality transcription
                result = self.transcriber.transcribe(audio_data)
                text = result["text"].strip()
                confidence = 0.9  # Whisper doesn't provide confidence scores
                language = result.get("language", "en")

            elif self.transcription_method == "speech_recognition" and self.transcriber:
                # Use SpeechRecognition with Google API
                import speech_recognition as sr

                audio = sr.AudioData(audio_data.tobytes(), self.config.sample_rate, 2)

                try:
                    text = self.transcriber.recognize_google(audio)
                    confidence = 0.8  # Estimate
                    language = "en"
                except sr.UnknownValueError:
                    text = ""
                    confidence = 0.0
                    language = None
                except sr.RequestError as e:
                    self.logger.error(f"Speech recognition error: {e}")
                    text = ""
                    confidence = 0.0
                    language = None
            else:
                # No transcription available
                text = "[Transcription not available]"
                confidence = 0.0
                language = None

            # Detect wake words
            wake_words = self._detect_wake_words(text)
            wake_word_detected = len(wake_words) > 0

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()

            return VoiceResult(
                text=text,
                confidence=confidence,
                duration=duration,
                timestamp=start_time,
                language=language,
                wake_word_detected=wake_word_detected,
            )

        except Exception as e:
            self.logger.error(f"Transcription error: {e}")
            return VoiceResult(
                text="", confidence=0.0, duration=0.0, timestamp=start_time
            )

    def _process_audio_chunk(self, audio_chunk: bytes) -> VoiceResult | None:
        """Process a single audio chunk."""
        try:
            # Convert to numpy array
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)

            # Apply noise reduction
            if self.noise_reducer and self.config.noise_reduction_enabled:
                if callable(self.noise_reducer):
                    audio_data = self.noise_reducer(audio_data)
                else:
                    # Using noisereduce library
                    audio_data = self.noise_reducer.reduce_noise(
                        y=audio_data, sr=self.config.sample_rate
                    )

            # Voice activity detection
            if self.vad_enabled:
                if callable(self.vad):
                    speech_detected = self.vad(audio_chunk)
                else:
                    # Using webrtcvad
                    speech_detected = self.vad.is_speech(
                        audio_chunk, self.config.sample_rate
                    )

                if speech_detected:
                    self.silence_counter = 0
                    if not self.speech_detected:
                        self.speech_detected = True
                        if self.on_speech_start:
                            self.on_speech_start()
                else:
                    self.silence_counter += 1
                    if (
                        self.silence_counter
                        > self.config.silence_timeout
                        * self.config.sample_rate
                        / self.config.chunk_size
                    ):
                        if self.speech_detected:
                            self.speech_detected = False
                            if self.on_speech_end:
                                self.on_speech_end()

                            # Transcribe accumulated audio
                            return self._transcribe_audio(audio_data)

            return None

        except Exception as e:
            self.logger.error(f"Audio processing error: {e}")
            return None

    def start_listening(self):
        """Start listening for voice input."""
        if self.is_listening:
            return

        self.is_listening = True
        self.processing_thread = threading.Thread(target=self._audio_processing_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()

        self.logger.info("Enhanced voice processing started")

    def stop_listening(self):
        """Stop listening for voice input."""
        self.is_listening = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)

        self.logger.info("Enhanced voice processing stopped")

    def _audio_processing_loop(self):
        """Main audio processing loop."""
        try:
            import pyaudio

            # Initialize audio stream
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.config.sample_rate,
                input=True,
                frames_per_buffer=self.config.chunk_size,
            )

            self.logger.info("Audio stream opened")

            while self.is_listening:
                try:
                    # Read audio chunk
                    audio_chunk = stream.read(
                        self.config.chunk_size, exception_on_overflow=False
                    )

                    # Process the chunk
                    result = self._process_audio_chunk(audio_chunk)

                    if result and result.confidence >= self.config.confidence_threshold:
                        # Call transcription callback
                        if self.on_transcription:
                            self.on_transcription(result)

                        # Call wake word callback if detected
                        if result.wake_word_detected and self.on_wake_word:
                            self.on_wake_word(result.text)

                except Exception as e:
                    self.logger.error(f"Audio processing error: {e}")
                    continue

            # Cleanup
            stream.stop_stream()
            stream.close()
            audio.terminate()

        except Exception as e:
            self.logger.error(f"Audio processing loop error: {e}")

    def process_audio_file(self, file_path: str) -> VoiceResult:
        """Process an audio file and return transcription."""
        try:
            # Load audio file
            import librosa

            audio_data, sr = librosa.load(file_path, sr=self.config.sample_rate)

            # Apply processing
            if self.noise_reducer and self.config.noise_reduction_enabled:
                if callable(self.noise_reducer):
                    audio_data = self.noise_reducer(audio_data)
                else:
                    audio_data = self.noise_reducer.reduce_noise(y=audio_data, sr=sr)

            # Transcribe
            return self._transcribe_audio(audio_data)

        except Exception as e:
            self.logger.error(f"File processing error: {e}")
            return VoiceResult(
                text="", confidence=0.0, duration=0.0, timestamp=datetime.now()
            )


def create_enhanced_voice_processor(config: dict[str, Any]) -> EnhancedVoiceProcessor:
    """Factory function to create an enhanced voice processor."""
    voice_config = VoiceProcessingConfig(
        sample_rate=config.get("sample_rate", 16000),
        chunk_size=config.get("chunk_size", 1024),
        noise_reduction_enabled=config.get("noise_reduction", True),
        voice_activity_detection=config.get("vad", True),
        echo_cancellation=config.get("echo_cancellation", True),
        auto_gain_control=config.get("auto_gain", True),
        confidence_threshold=config.get("confidence_threshold", 0.7),
        silence_timeout=config.get("silence_timeout", 2.0),
        max_recording_duration=config.get("max_duration", 30.0),
    )

    return EnhancedVoiceProcessor(voice_config)
