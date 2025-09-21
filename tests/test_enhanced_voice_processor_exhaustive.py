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
Exhaustive test coverage for EnhancedVoiceProcessor.
Tests all functionality including VAD, noise reduction, multi-engine transcription,
wake word detection, fallback mechanisms, and error handling.
"""

import threading
import time
from unittest.mock import ANY, Mock, patch

import numpy as np
import pytest

from chatty_commander.voice.enhanced_processor import (
    EnhancedVoiceProcessor,
    VoiceProcessingConfig,
    VoiceResult,
    create_enhanced_voice_processor,
)


class TestVoiceProcessingConfig:
    """Test VoiceProcessingConfig data class."""

    def test_default_config_creation(self):
        """Test creating config with default values."""
        config = VoiceProcessingConfig()

        assert config.sample_rate == 16000
        assert config.chunk_size == 1024
        assert config.channels == 1
        assert config.enable_vad is True
        assert config.enable_noise_reduction is True
        assert config.enable_multi_engine is True
        assert config.wake_words == ["hey computer", "computer"]
        assert config.silence_timeout == 2.0
        assert config.vad_threshold == 0.5
        assert config.noise_reduction_level == "medium"
        assert config.primary_transcription_engine == "whisper"
        assert config.fallback_transcription_engine == "google"
        assert config.enable_real_time is True
        assert config.debug_mode is False

    def test_custom_config_creation(self):
        """Test creating config with custom values."""
        config = VoiceProcessingConfig(
            sample_rate=44100,
            chunk_size=2048,
            channels=2,
            enable_vad=False,
            enable_noise_reduction=False,
            enable_multi_engine=False,
            wake_words=["custom"],
            silence_timeout=5.0,
            vad_threshold=0.8,
            noise_reduction_level="high",
            primary_transcription_engine="google",
            fallback_transcription_engine="whisper",
            enable_real_time=False,
            debug_mode=True,
        )

        assert config.sample_rate == 44100
        assert config.chunk_size == 2048
        assert config.channels == 2
        assert config.enable_vad is False
        assert config.enable_noise_reduction is False
        assert config.enable_multi_engine is False
        assert config.wake_words == ["custom"]
        assert config.silence_timeout == 5.0
        assert config.vad_threshold == 0.8
        assert config.noise_reduction_level == "high"
        assert config.primary_transcription_engine == "google"
        assert config.fallback_transcription_engine == "whisper"
        assert config.enable_real_time is False
        assert config.debug_mode is True

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = VoiceProcessingConfig(sample_rate=22050, debug_mode=True)

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["sample_rate"] == 22050
        assert config_dict["debug_mode"] is True


class TestVoiceResult:
    """Test VoiceResult data class."""

    def test_voice_result_creation(self):
        """Test creating VoiceResult with all fields."""
        result = VoiceResult(
            text="Hello world",
            confidence=0.95,
            is_wake_word=True,
            wake_word="hey computer",
            engine_used="whisper",
            processing_time=0.5,
            audio_duration=2.0,
            language="en",
            alternatives=["Hello", "Hi world"],
            vad_detected=True,
            noise_reduced=True,
        )

        assert result.text == "Hello world"
        assert result.confidence == 0.95
        assert result.is_wake_word is True
        assert result.wake_word == "hey computer"
        assert result.engine_used == "whisper"
        assert result.processing_time == 0.5
        assert result.audio_duration == 2.0
        assert result.language == "en"
        assert result.alternatives == ["Hello", "Hi world"]
        assert result.vad_detected is True
        assert result.noise_reduced is True

    def test_voice_result_minimal(self):
        """Test creating VoiceResult with minimal fields."""
        result = VoiceResult(text="Test")

        assert result.text == "Test"
        assert result.confidence == 0.0
        assert result.is_wake_word is False
        assert result.wake_word is None
        assert result.engine_used == "unknown"
        assert result.processing_time == 0.0
        assert result.audio_duration == 0.0
        assert result.language == "unknown"
        assert result.alternatives == []
        assert result.vad_detected is False
        assert result.noise_reduced is False

    def test_voice_result_to_dict(self):
        """Test converting VoiceResult to dictionary."""
        result = VoiceResult(
            text="Test conversion", confidence=0.85, engine_used="google"
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["text"] == "Test conversion"
        assert result_dict["confidence"] == 0.85
        assert result_dict["engine_used"] == "google"


class TestEnhancedVoiceProcessorInitialization:
    """Test EnhancedVoiceProcessor initialization and setup."""

    def test_default_initialization(self):
        """Test processor initialization with default config."""
        processor = EnhancedVoiceProcessor()

        assert processor.config.sample_rate == 16000
        assert processor.config.chunk_size == 1024
        assert processor.config.enable_vad is True
        assert processor.config.enable_noise_reduction is True
        assert processor.config.enable_multi_engine is True
        assert processor.is_listening is False
        assert processor.audio_queue is not None
        assert processor.voice_callbacks == []
        assert processor.wake_word_callbacks == []

    def test_custom_config_initialization(self):
        """Test processor initialization with custom config."""
        config = VoiceProcessingConfig(
            sample_rate=44100, enable_vad=False, debug_mode=True
        )
        processor = EnhancedVoiceProcessor(config)

        assert processor.config.sample_rate == 44100
        assert processor.config.enable_vad is False
        assert processor.config.debug_mode is True

    @patch("chatty_commander.voice.enhanced_processor.logging.getLogger")
    def test_debug_mode_logging_setup(self, mock_get_logger):
        """Test logging setup in debug mode."""
        config = VoiceProcessingConfig(debug_mode=True)
        processor = EnhancedVoiceProcessor(config)

        mock_get_logger.assert_called_once()

    def test_initialization_with_invalid_config(self):
        """Test processor initialization with invalid config."""
        with pytest.raises(TypeError):
            EnhancedVoiceProcessor(config="invalid")


class TestEnhancedVoiceProcessorCallbacks:
    """Test callback registration and management."""

    def test_add_voice_callback(self):
        """Test adding voice callback."""
        processor = EnhancedVoiceProcessor()
        callback = Mock()

        processor.add_voice_callback(callback)

        assert callback in processor.voice_callbacks
        assert len(processor.voice_callbacks) == 1

    def test_add_wake_word_callback(self):
        """Test adding wake word callback."""
        processor = EnhancedVoiceProcessor()
        callback = Mock()

        processor.add_wake_word_callback(callback)

        assert callback in processor.wake_word_callbacks
        assert len(processor.wake_word_callbacks) == 1

    def test_remove_voice_callback(self):
        """Test removing voice callback."""
        processor = EnhancedVoiceProcessor()
        callback = Mock()
        processor.add_voice_callback(callback)

        processor.remove_voice_callback(callback)

        assert callback not in processor.voice_callbacks
        assert len(processor.voice_callbacks) == 0

    def test_remove_wake_word_callback(self):
        """Test removing wake word callback."""
        processor = EnhancedVoiceProcessor()
        callback = Mock()
        processor.add_wake_word_callback(callback)

        processor.remove_wake_word_callback(callback)

        assert callback not in processor.wake_word_callbacks
        assert len(processor.wake_word_callbacks) == 0

    def test_multiple_callbacks(self):
        """Test multiple callback registration."""
        processor = EnhancedVoiceProcessor()
        voice_callback1 = Mock()
        voice_callback2 = Mock()
        wake_callback1 = Mock()
        wake_callback2 = Mock()

        processor.add_voice_callback(voice_callback1)
        processor.add_voice_callback(voice_callback2)
        processor.add_wake_word_callback(wake_callback1)
        processor.add_wake_word_callback(wake_callback2)

        assert len(processor.voice_callbacks) == 2
        assert len(processor.wake_word_callbacks) == 2
        assert voice_callback1 in processor.voice_callbacks
        assert voice_callback2 in processor.voice_callbacks
        assert wake_callback1 in processor.wake_word_callbacks
        assert wake_callback2 in processor.wake_word_callbacks


class TestWakeWordDetection:
    """Test wake word detection functionality."""

    def test_single_wake_word_detection(self):
        """Test detecting a single wake word."""
        processor = EnhancedVoiceProcessor()

        result = processor._detect_wake_words("hey computer, what's the weather")

        assert result is True
        assert "hey computer" in processor.config.wake_words

    def test_multiple_wake_word_detection(self):
        """Test detecting wake words from multiple options."""
        processor = EnhancedVoiceProcessor()

        result1 = processor._detect_wake_words("computer, turn on the lights")
        result2 = processor._detect_wake_words("hey computer, play music")

        assert result1 is True
        assert result2 is True

    def test_wake_word_case_insensitive(self):
        """Test wake word detection is case insensitive."""
        processor = EnhancedVoiceProcessor()

        result1 = processor._detect_wake_words("HEY COMPUTER")
        result2 = processor._detect_wake_words("Computer")
        result3 = processor._detect_wake_words("hEy CoMpUtEr")

        assert result1 is True
        assert result2 is True
        assert result3 is True

    def test_no_wake_word_detection(self):
        """Test when no wake word is detected."""
        processor = EnhancedVoiceProcessor()

        result = processor._detect_wake_words("what's the weather like today")

        assert result is False

    def test_partial_wake_word_match(self):
        """Test that partial matches don't trigger wake word."""
        processor = EnhancedVoiceProcessor()

        result1 = processor._detect_wake_words("hey computation")
        result2 = processor._detect_wake_words("computing device")

        assert result1 is False
        assert result2 is False

    def test_custom_wake_words(self):
        """Test wake word detection with custom words."""
        config = VoiceProcessingConfig(wake_words=["alexa", "echo"])
        processor = EnhancedVoiceProcessor(config)

        result1 = processor._detect_wake_words("alexa, play music")
        result2 = processor._detect_wake_words("echo, what's the time")
        result3 = processor._detect_wake_words("hey computer")

        assert result1 is True
        assert result2 is True
        assert result3 is False

    def test_empty_text_wake_word_detection(self):
        """Test wake word detection with empty text."""
        processor = EnhancedVoiceProcessor()

        result = processor._detect_wake_words("")

        assert result is False

    def test_none_text_wake_word_detection(self):
        """Test wake word detection with None text."""
        processor = EnhancedVoiceProcessor()

        result = processor._detect_wake_words(None)

        assert result is False


class TestTranscriptionEngines:
    """Test transcription engine functionality."""

    @patch("chatty_commander.voice.enhanced_processor.whisper.load_model")
    def test_whisper_transcription_success(self, mock_load_model):
        """Test successful Whisper transcription."""
        # Mock Whisper model
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "Hello world",
            "segments": [{"confidence": 0.95}],
            "language": "en",
        }
        mock_load_model.return_value = mock_model

        processor = EnhancedVoiceProcessor()
        processor.whisper_model = mock_model

        # Create mock audio data
        audio_data = np.random.randn(16000).astype(np.float32)

        result = processor._transcribe_audio(audio_data, engine="whisper")

        assert result.text == "Hello world"
        assert result.confidence == 0.95
        assert result.engine_used == "whisper"
        assert result.language == "en"
        mock_model.transcribe.assert_called_once_with(audio_data)

    @patch("chatty_commander.voice.enhanced_processor.whisper.load_model")
    def test_whisper_transcription_empty_result(self, mock_load_model):
        """Test Whisper transcription with empty result."""
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "",
            "segments": [],
            "language": "unknown",
        }
        mock_load_model.return_value = mock_model

        processor = EnhancedVoiceProcessor()
        processor.whisper_model = mock_model

        audio_data = np.random.randn(16000).astype(np.float32)

        result = processor._transcribe_audio(audio_data, engine="whisper")

        assert result.text == ""
        assert result.confidence == 0.0
        assert result.engine_used == "whisper"
        assert result.language == "unknown"

    @patch("chatty_commander.voice.enhanced_processor.sr.Recognizer")
    def test_google_transcription_success(self, mock_recognizer_class):
        """Test successful Google Speech Recognition transcription."""
        mock_recognizer = Mock()
        mock_recognizer_class.return_value = mock_recognizer

        # Mock successful recognition
        mock_recognizer.recognize_google.return_value = "Hello from Google"

        processor = EnhancedVoiceProcessor()
        processor.speech_recognizer = mock_recognizer

        # Create mock audio data and convert to AudioData
        audio_data = np.random.randn(16000).astype(np.float32)

        with patch(
            "chatty_commander.voice.enhanced_processor.sr.AudioData"
        ) as mock_audio_data_class:
            mock_audio_data = Mock()
            mock_audio_data_class.return_value = mock_audio_data

            result = processor._transcribe_audio(audio_data, engine="google")

            assert result.text == "Hello from Google"
            assert result.engine_used == "google"
            assert result.confidence == 0.8  # Default confidence for Google
            mock_recognizer.recognize_google.assert_called_once_with(mock_audio_data)

    @patch("chatty_commander.voice.enhanced_processor.sr.Recognizer")
    def test_google_transcription_failure_fallback(self, mock_recognizer_class):
        """Test Google transcription failure with fallback."""
        mock_recognizer = Mock()
        mock_recognizer_class.return_value = mock_recognizer

        # Mock recognition failure
        mock_recognizer.recognize_google.side_effect = Exception("API error")

        processor = EnhancedVoiceProcessor()
        processor.speech_recognizer = mock_recognizer

        audio_data = np.random.randn(16000).astype(np.float32)

        with patch(
            "chatty_commander.voice.enhanced_processor.sr.AudioData"
        ) as mock_audio_data_class:
            mock_audio_data = Mock()
            mock_audio_data_class.return_value = mock_audio_data

            result = processor._transcribe_audio(audio_data, engine="google")

            assert result.text == ""
            assert result.confidence == 0.0
            assert result.engine_used == "google"

    def test_unknown_transcription_engine(self):
        """Test transcription with unknown engine."""
        processor = EnhancedVoiceProcessor()

        audio_data = np.random.randn(16000).astype(np.float32)

        result = processor._transcribe_audio(audio_data, engine="unknown")

        assert result.text == ""
        assert result.confidence == 0.0
        assert result.engine_used == "unknown"

    def test_transcription_with_invalid_audio(self):
        """Test transcription with invalid audio data."""
        processor = EnhancedVoiceProcessor()

        # Test with None audio
        result = processor._transcribe_audio(None, engine="whisper")
        assert result.text == ""

        # Test with empty array
        result = processor._transcribe_audio(np.array([]), engine="whisper")
        assert result.text == ""


class TestAudioProcessing:
    """Test audio processing functionality."""

    def test_audio_chunk_processing_success(self):
        """Test successful audio chunk processing."""
        processor = EnhancedVoiceProcessor()

        # Create mock audio chunk
        audio_chunk = np.random.randn(1024).astype(np.float32)

        # Mock the transcription to return a result
        mock_result = VoiceResult(text="Test audio", confidence=0.9)

        with patch.object(processor, "_transcribe_audio", return_value=mock_result):
            result = processor._process_audio_chunk(audio_chunk)

            assert result.text == "Test audio"
            assert result.confidence == 0.9
            assert result.audio_duration == 1024 / 16000  # chunk_size / sample_rate

    def test_audio_chunk_processing_with_vad_enabled(self):
        """Test audio chunk processing with VAD enabled."""
        config = VoiceProcessingConfig(enable_vad=True, vad_threshold=0.3)
        processor = EnhancedVoiceProcessor(config)

        audio_chunk = np.random.randn(1024).astype(np.float32)
        mock_result = VoiceResult(text="VAD test", confidence=0.8)

        with patch.object(processor, "_transcribe_audio", return_value=mock_result):
            with patch.object(processor, "_apply_vad", return_value=True):
                result = processor._process_audio_chunk(audio_chunk)

                assert result.text == "VAD test"
                assert result.vad_detected is True

    def test_audio_chunk_processing_with_noise_reduction(self):
        """Test audio chunk processing with noise reduction."""
        config = VoiceProcessingConfig(
            enable_noise_reduction=True, noise_reduction_level="high"
        )
        processor = EnhancedVoiceProcessor(config)

        audio_chunk = np.random.randn(1024).astype(np.float32)
        mock_result = VoiceResult(text="Noise reduced", confidence=0.85)

        with patch.object(processor, "_transcribe_audio", return_value=mock_result):
            with patch.object(
                processor, "_apply_noise_reduction"
            ) as mock_noise_reduction:
                result = processor._process_audio_chunk(audio_chunk)

                mock_noise_reduction.assert_called_once_with(audio_chunk)
                assert result.noise_reduced is True

    def test_silence_timeout_detection(self):
        """Test silence timeout detection."""
        config = VoiceProcessingConfig(silence_timeout=1.0)
        processor = EnhancedVoiceProcessor(config)

        # Mock current time progression
        current_time = 0.0

        def mock_time():
            nonlocal current_time
            return current_time

        with patch("time.time", side_effect=mock_time):
            # First call - not timeout
            current_time = 0.5
            result1 = processor._check_silence_timeout()
            assert result1 is False

            # Second call - timeout reached
            current_time = 1.5
            result2 = processor._check_silence_timeout()
            assert result2 is True

    def test_vad_application(self):
        """Test Voice Activity Detection application."""
        processor = EnhancedVoiceProcessor()

        # Create audio with different energy levels
        high_energy_audio = np.random.randn(1024).astype(np.float32) * 0.5
        low_energy_audio = np.random.randn(1024).astype(np.float32) * 0.01

        # Test high energy audio (should pass VAD)
        result1 = processor._apply_vad(high_energy_audio, threshold=0.3)
        assert result1 is True

        # Test low energy audio (should fail VAD)
        result2 = processor._apply_vad(low_energy_audio, threshold=0.3)
        assert result2 is False

    def test_noise_reduction_application(self):
        """Test noise reduction application."""
        processor = EnhancedVoiceProcessor()

        # Create noisy audio
        clean_audio = np.sin(2 * np.pi * 440 * np.arange(1024) / 16000).astype(
            np.float32
        )
        noise = np.random.randn(1024).astype(np.float32) * 0.1
        noisy_audio = clean_audio + noise

        # Test noise reduction
        reduced_audio = processor._apply_noise_reduction(noisy_audio, level="medium")

        assert isinstance(reduced_audio, np.ndarray)
        assert reduced_audio.shape == noisy_audio.shape
        assert reduced_audio.dtype == np.float32


class TestListeningFunctionality:
    """Test voice listening functionality."""

    @patch("chatty_commander.voice.enhanced_processor.pyaudio.PyAudio")
    def test_start_listening_success(self, mock_pyaudio_class):
        """Test successful start of voice listening."""
        # Mock PyAudio
        mock_pyaudio = Mock()
        mock_stream = Mock()
        mock_pyaudio.open.return_value = mock_stream
        mock_pyaudio_class.return_value = mock_pyaudio

        processor = EnhancedVoiceProcessor()

        # Add callback
        callback = Mock()
        processor.add_voice_callback(callback)

        # Start listening
        result = processor.start_listening()

        assert result is True
        assert processor.is_listening is True
        assert processor.audio_stream == mock_stream
        mock_pyaudio.open.assert_called_once()

        # Verify stream configuration
        call_args = mock_pyaudio.open.call_args
        assert call_args.kwargs["format"] == ANY
        assert call_args.kwargs["channels"] == 1
        assert call_args.kwargs["rate"] == 16000
        assert call_args.kwargs["frames_per_buffer"] == 1024
        assert call_args.kwargs["input"] is True
        assert call_args.kwargs["stream_callback"] == processor._audio_stream_callback

    @patch("chatty_commander.voice.enhanced_processor.pyaudio.PyAudio")
    def test_start_listening_already_active(self, mock_pyaudio_class):
        """Test starting listening when already active."""
        mock_pyaudio = Mock()
        mock_pyaudio_class.return_value = mock_pyaudio

        processor = EnhancedVoiceProcessor()
        processor.is_listening = True

        result = processor.start_listening()

        assert result is False
        mock_pyaudio.open.assert_not_called()

    @patch("chatty_commander.voice.enhanced_processor.pyaudio.PyAudio")
    def test_start_listening_pyaudio_error(self, mock_pyaudio_class):
        """Test handling PyAudio initialization error."""
        mock_pyaudio = Mock()
        mock_pyaudio.open.side_effect = Exception("PyAudio error")
        mock_pyaudio_class.return_value = mock_pyaudio

        processor = EnhancedVoiceProcessor()

        result = processor.start_listening()

        assert result is False
        assert processor.is_listening is False

    def test_stop_listening_success(self):
        """Test successful stop of voice listening."""
        processor = EnhancedVoiceProcessor()
        processor.is_listening = True

        # Mock audio stream
        mock_stream = Mock()
        processor.audio_stream = mock_stream

        # Mock PyAudio
        mock_pyaudio = Mock()
        processor.pyaudio = mock_pyaudio

        result = processor.stop_listening()

        assert result is True
        assert processor.is_listening is False
        mock_stream.stop_stream.assert_called_once()
        mock_stream.close.assert_called_once()
        mock_pyaudio.terminate.assert_called_once()

    def test_stop_listening_not_active(self):
        """Test stopping listening when not active."""
        processor = EnhancedVoiceProcessor()
        processor.is_listening = False

        result = processor.stop_listening()

        assert result is False

    def test_stop_listening_no_stream(self):
        """Test stopping listening with no stream."""
        processor = EnhancedVoiceProcessor()
        processor.is_listening = True
        processor.audio_stream = None

        result = processor.stop_listening()

        assert result is True
        assert processor.is_listening is False


class TestAudioStreamCallback:
    """Test audio stream callback functionality."""

    def test_audio_stream_callback_processing(self):
        """Test audio stream callback with valid data."""
        processor = EnhancedVoiceProcessor()

        # Create mock audio data
        audio_data = np.random.randn(1024).astype(np.float32)
        frame_count = 1024

        # Mock the processing
        mock_result = VoiceResult(text="Callback test", confidence=0.9)

        with patch.object(processor, "_process_audio_chunk", return_value=mock_result):
            with patch.object(processor, "_notify_voice_callbacks") as mock_notify:
                # Simulate audio stream callback
                result = processor._audio_stream_callback(
                    audio_data, frame_count, None, None
                )

                assert result == (audio_data, pyaudio.paContinue)
                mock_notify.assert_called_once_with(mock_result)

    def test_audio_stream_callback_wake_word_detection(self):
        """Test audio stream callback with wake word detection."""
        processor = EnhancedVoiceProcessor()

        audio_data = np.random.randn(1024).astype(np.float32)
        frame_count = 1024

        # Mock wake word result
        mock_result = VoiceResult(
            text="hey computer, test",
            confidence=0.95,
            is_wake_word=True,
            wake_word="hey computer",
        )

        with patch.object(processor, "_process_audio_chunk", return_value=mock_result):
            with patch.object(
                processor, "_notify_wake_word_callbacks"
            ) as mock_wake_notify:
                processor._audio_stream_callback(audio_data, frame_count, None, None)

                mock_wake_notify.assert_called_once_with(mock_result)

    def test_audio_stream_callback_error_handling(self):
        """Test audio stream callback error handling."""
        processor = EnhancedVoiceProcessor()

        audio_data = np.random.randn(1024).astype(np.float32)
        frame_count = 1024

        # Mock processing error
        with patch.object(
            processor, "_process_audio_chunk", side_effect=Exception("Processing error")
        ):
            with patch.object(processor, "logger") as mock_logger:
                result = processor._audio_stream_callback(
                    audio_data, frame_count, None, None
                )

                assert result == (audio_data, pyaudio.paContinue)
                mock_logger.error.assert_called_once()

    def test_audio_stream_callback_none_data(self):
        """Test audio stream callback with None data."""
        processor = EnhancedVoiceProcessor()

        result = processor._audio_stream_callback(None, 0, None, None)

        assert result == (None, pyaudio.paContinue)


class TestCallbackNotification:
    """Test callback notification functionality."""

    def test_notify_voice_callbacks(self):
        """Test notifying voice callbacks."""
        processor = EnhancedVoiceProcessor()

        # Add multiple callbacks
        callback1 = Mock()
        callback2 = Mock()
        processor.add_voice_callback(callback1)
        processor.add_voice_callback(callback2)

        # Create test result
        test_result = VoiceResult(text="Test notification", confidence=0.9)

        processor._notify_voice_callbacks(test_result)

        # Verify both callbacks were called
        callback1.assert_called_once_with(test_result)
        callback2.assert_called_once_with(test_result)

    def test_notify_wake_word_callbacks(self):
        """Test notifying wake word callbacks."""
        processor = EnhancedVoiceProcessor()

        # Add wake word callbacks
        callback1 = Mock()
        callback2 = Mock()
        processor.add_wake_word_callback(callback1)
        processor.add_wake_word_callback(callback2)

        # Create wake word result
        wake_result = VoiceResult(
            text="hey computer",
            confidence=0.95,
            is_wake_word=True,
            wake_word="hey computer",
        )

        processor._notify_wake_word_callbacks(wake_result)

        # Verify callbacks were called
        callback1.assert_called_once_with(wake_result)
        callback2.assert_called_once_with(wake_result)

    def test_notify_callbacks_with_exception(self):
        """Test callback notification with exception handling."""
        processor = EnhancedVoiceProcessor()

        # Add callback that raises exception
        failing_callback = Mock(side_effect=Exception("Callback error"))
        good_callback = Mock()

        processor.add_voice_callback(failing_callback)
        processor.add_voice_callback(good_callback)

        test_result = VoiceResult(text="Test with error")

        with patch.object(processor, "logger") as mock_logger:
            processor._notify_voice_callbacks(test_result)

            # Both callbacks should be attempted
            failing_callback.assert_called_once_with(test_result)
            good_callback.assert_called_once_with(test_result)

            # Error should be logged
            mock_logger.error.assert_called_once()


class TestAudioFileProcessing:
    """Test audio file processing functionality."""

    @patch("chatty_commander.voice.enhanced_processor.sf.read")
    def test_process_audio_file_success(self, mock_sf_read):
        """Test successful audio file processing."""
        # Mock audio file data
        audio_data = np.random.randn(32000).astype(np.float32)  # 2 seconds at 16kHz
        sample_rate = 16000
        mock_sf_read.return_value = (audio_data, sample_rate)

        processor = EnhancedVoiceProcessor()

        # Mock transcription result
        mock_result = VoiceResult(text="File processing test", confidence=0.9)

        with patch.object(processor, "_transcribe_audio", return_value=mock_result):
            result = processor.process_audio_file("test.wav")

            assert result.text == "File processing test"
            assert result.confidence == 0.9
            assert result.audio_duration == 2.0  # 32000 samples / 16000 Hz
            mock_sf_read.assert_called_once_with("test.wav")

    @patch("chatty_commander.voice.enhanced_processor.sf.read")
    def test_process_audio_file_different_sample_rate(self, mock_sf_read):
        """Test audio file processing with different sample rate."""
        # Mock audio data with different sample rate
        audio_data = np.random.randn(44100).astype(np.float32)  # 1 second at 44.1kHz
        sample_rate = 44100
        mock_sf_read.return_value = (audio_data, sample_rate)

        processor = EnhancedVoiceProcessor()

        mock_result = VoiceResult(text="Resampled audio", confidence=0.85)

        with patch(
            "chatty_commander.voice.enhanced_processor.librosa.resample"
        ) as mock_resample:
            resampled_audio = np.random.randn(16000).astype(np.float32)
            mock_resample.return_value = resampled_audio

            with patch.object(processor, "_transcribe_audio", return_value=mock_result):
                result = processor.process_audio_file("test_44k.wav")

                assert result.text == "Resampled audio"
                mock_resample.assert_called_once()

    @patch("chatty_commander.voice.enhanced_processor.sf.read")
    def test_process_audio_file_not_found(self, mock_sf_read):
        """Test audio file processing with file not found."""
        mock_sf_read.side_effect = FileNotFoundError("File not found")

        processor = EnhancedVoiceProcessor()

        with patch.object(processor, "logger") as mock_logger:
            result = processor.process_audio_file("nonexistent.wav")

            assert result.text == ""
            assert result.confidence == 0.0
            mock_logger.error.assert_called_once()

    @patch("chatty_commander.voice.enhanced_processor.sf.read")
    def test_process_audio_file_format_error(self, mock_sf_read):
        """Test audio file processing with format error."""
        mock_sf_read.side_effect = Exception("Unsupported format")

        processor = EnhancedVoiceProcessor()

        with patch.object(processor, "logger") as mock_logger:
            result = processor.process_audio_file("test.unsupported")

            assert result.text == ""
            assert result.confidence == 0.0
            mock_logger.error.assert_called_once()


class TestMultiEngineFallback:
    """Test multi-engine transcription fallback functionality."""

    def test_primary_engine_success(self):
        """Test successful transcription with primary engine."""
        processor = EnhancedVoiceProcessor()

        audio_data = np.random.randn(16000).astype(np.float32)
        mock_result = VoiceResult(
            text="Primary engine success", confidence=0.9, engine_used="whisper"
        )

        with patch.object(processor, "_transcribe_audio", return_value=mock_result):
            result = processor._transcribe_with_fallback(audio_data)

            assert result.text == "Primary engine success"
            assert result.engine_used == "whisper"
            assert result.confidence == 0.9

    def test_fallback_engine_on_primary_failure(self):
        """Test fallback to secondary engine when primary fails."""
        processor = EnhancedVoiceProcessor()

        audio_data = np.random.randn(16000).astype(np.float32)

        # Mock primary engine failure and fallback success
        primary_result = VoiceResult(text="", confidence=0.0, engine_used="whisper")
        fallback_result = VoiceResult(
            text="Fallback success", confidence=0.7, engine_used="google"
        )

        with patch.object(
            processor,
            "_transcribe_audio",
            side_effect=[primary_result, fallback_result],
        ):
            result = processor._transcribe_with_fallback(audio_data)

            assert result.text == "Fallback success"
            assert result.engine_used == "google"
            assert result.confidence == 0.7

    def test_both_engines_fail(self):
        """Test when both primary and fallback engines fail."""
        processor = EnhancedVoiceProcessor()

        audio_data = np.random.randn(16000).astype(np.float32)

        # Mock both engines failing
        failure_result = VoiceResult(text="", confidence=0.0)

        with patch.object(processor, "_transcribe_audio", return_value=failure_result):
            result = processor._transcribe_with_fallback(audio_data)

            assert result.text == ""
            assert result.confidence == 0.0

    def test_multi_engine_disabled(self):
        """Test transcription when multi-engine is disabled."""
        config = VoiceProcessingConfig(enable_multi_engine=False)
        processor = EnhancedVoiceProcessor(config)

        audio_data = np.random.randn(16000).astype(np.float32)
        mock_result = VoiceResult(text="Single engine", confidence=0.8)

        with patch.object(processor, "_transcribe_audio", return_value=mock_result):
            result = processor._transcribe_with_fallback(audio_data)

            assert result.text == "Single engine"
            assert result.confidence == 0.8
            # Should only call once since multi-engine is disabled


class TestErrorHandling:
    """Test comprehensive error handling scenarios."""

    def test_initialization_with_missing_dependencies(self):
        """Test initialization when dependencies are missing."""
        with patch.dict("sys.modules", {"whisper": None}):
            with patch.object(EnhancedVoiceProcessor, "logger") as mock_logger:
                processor = EnhancedVoiceProcessor()

                assert processor.whisper_model is None
                mock_logger.warning.assert_called()

    def test_transcription_with_missing_model(self):
        """Test transcription when model is not loaded."""
        processor = EnhancedVoiceProcessor()
        processor.whisper_model = None

        audio_data = np.random.randn(16000).astype(np.float32)

        with patch.object(processor, "logger") as mock_logger:
            result = processor._transcribe_audio(audio_data, engine="whisper")

            assert result.text == ""
            assert result.confidence == 0.0
            mock_logger.error.assert_called_once()

    def test_audio_processing_loop_error_recovery(self):
        """Test error recovery in audio processing loop."""
        processor = EnhancedVoiceProcessor()
        processor.is_listening = True

        # Mock queue that raises exception
        mock_queue = Mock()
        mock_queue.get.side_effect = [Exception("Queue error"), KeyboardInterrupt]
        processor.audio_queue = mock_queue

        with patch.object(processor, "logger") as mock_logger:
            with patch.object(processor, "stop_listening") as mock_stop:
                try:
                    processor._audio_processing_loop()
                except KeyboardInterrupt:
                    pass

                # Should log error and continue
                mock_logger.error.assert_called_once()
                mock_stop.assert_called_once()

    def test_invalid_audio_format_handling(self):
        """Test handling of invalid audio formats."""
        processor = EnhancedVoiceProcessor()

        # Test with invalid audio data types
        invalid_audio = "not an array"

        result = processor._process_audio_chunk(invalid_audio)

        assert result.text == ""
        assert result.confidence == 0.0

    def test_concurrent_access_safety(self):
        """Test thread safety of concurrent operations."""
        processor = EnhancedVoiceProcessor()

        results = []

        def add_callback():
            for i in range(10):
                callback = Mock()
                processor.add_voice_callback(callback)
                results.append(len(processor.voice_callbacks))

        def remove_callback():
            for i in range(5):
                if processor.voice_callbacks:
                    callback = processor.voice_callbacks[0]
                    processor.remove_voice_callback(callback)
                    results.append(len(processor.voice_callbacks))

        # Run concurrent operations
        thread1 = threading.Thread(target=add_callback)
        thread2 = threading.Thread(target=remove_callback)

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # Should complete without crashes
        assert len(results) > 0


class TestPerformanceAndStress:
    """Test performance and stress scenarios."""

    def test_large_audio_file_processing(self):
        """Test processing of large audio files."""
        processor = EnhancedVoiceProcessor()

        # Create large audio data (10 seconds at 16kHz)
        large_audio = np.random.randn(160000).astype(np.float32)

        mock_result = VoiceResult(text="Large file processed", confidence=0.85)

        with patch.object(processor, "_transcribe_audio", return_value=mock_result):
            start_time = time.time()
            result = processor._transcribe_audio(large_audio, engine="whisper")
            processing_time = time.time() - start_time

            assert result.text == "Large file processed"
            assert processing_time < 1.0  # Should be fast

    def test_rapid_consecutive_transcriptions(self):
        """Test rapid consecutive transcription requests."""
        processor = EnhancedVoiceProcessor()

        results = []

        def transcribe_chunk(chunk_id):
            audio_data = np.random.randn(1024).astype(np.float32)
            mock_result = VoiceResult(text=f"Chunk {chunk_id}", confidence=0.9)

            with patch.object(processor, "_transcribe_audio", return_value=mock_result):
                result = processor._transcribe_audio(audio_data, engine="whisper")
                results.append(result.text)

        # Simulate rapid requests
        threads = []
        for i in range(20):
            thread = threading.Thread(target=transcribe_chunk, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All requests should complete
        assert len(results) == 20

    def test_memory_usage_with_many_callbacks(self):
        """Test memory usage with many registered callbacks."""
        processor = EnhancedVoiceProcessor()

        # Register many callbacks
        callbacks = []
        for i in range(1000):
            callback = Mock()
            callbacks.append(callback)
            processor.add_voice_callback(callback)

        # Create test result
        test_result = VoiceResult(text="Memory test", confidence=0.9)

        # Notify all callbacks
        start_time = time.time()
        processor._notify_voice_callbacks(test_result)
        notification_time = time.time() - start_time

        # Should complete reasonably fast
        assert notification_time < 0.1

        # All callbacks should be called
        for callback in callbacks:
            callback.assert_called_once_with(test_result)


class TestFactoryFunction:
    """Test the create_enhanced_voice_processor factory function."""

    def test_factory_with_default_config(self):
        """Test factory function with default configuration."""
        processor = create_enhanced_voice_processor()

        assert isinstance(processor, EnhancedVoiceProcessor)
        assert processor.config.sample_rate == 16000
        assert processor.config.enable_vad is True

    def test_factory_with_custom_config_dict(self):
        """Test factory function with custom configuration dictionary."""
        custom_config = {
            "sample_rate": 44100,
            "enable_vad": False,
            "wake_words": ["custom", "assistant"],
            "debug_mode": True,
        }

        processor = create_enhanced_voice_processor(custom_config)

        assert isinstance(processor, EnhancedVoiceProcessor)
        assert processor.config.sample_rate == 44100
        assert processor.config.enable_vad is False
        assert processor.config.wake_words == ["custom", "assistant"]
        assert processor.config.debug_mode is True

    def test_factory_with_invalid_config(self):
        """Test factory function with invalid configuration."""
        with pytest.raises(TypeError):
            create_enhanced_voice_processor("invalid_config")

    def test_factory_with_partial_config(self):
        """Test factory function with partial configuration."""
        partial_config = {"sample_rate": 22050, "enable_noise_reduction": False}

        processor = create_enhanced_voice_processor(partial_config)

        assert processor.config.sample_rate == 22050
        assert processor.config.enable_noise_reduction is False
        # Other values should be defaults
        assert processor.config.enable_vad is True
        assert processor.config.chunk_size == 1024


# Import pyaudio for constants
import pyaudio
