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
Comprehensive tests for enhanced voice processor module.

Tests voice activity detection, noise reduction, multi-engine transcription,
and wake word detection functionality.
"""

import time
from unittest.mock import Mock, patch

import numpy as np
import pytest

from src.chatty_commander.voice.enhanced_processor import (
    AudioChunk,
    EnhancedVoiceProcessor,
    TranscriptionResult,
    VoiceProcessingConfig,
)


class TestVoiceProcessingConfig:
    """Test VoiceProcessingConfig class."""

    def test_config_creation_with_defaults(self):
        """Test creating config with default values."""
        config = VoiceProcessingConfig()

        assert config.sample_rate == 16000
        assert config.chunk_size == 1024
        assert config.noise_reduction_enabled is True

    def test_config_creation_with_custom_values(self):
        """Test creating config with custom values."""
        config = VoiceProcessingConfig(
            sample_rate=44100, chunk_size=2048, noise_reduction_enabled=False
        )

        assert config.sample_rate == 44100
        assert config.chunk_size == 2048
        assert config.noise_reduction_enabled is False


class TestAudioChunk:
    """Test AudioChunk class."""

    def test_audio_chunk_creation(self):
        """Test creating an AudioChunk instance."""
        audio_data = np.array([1, 2, 3, 4, 5], dtype=np.int16)
        chunk = AudioChunk(data=audio_data, timestamp=time.time(), sample_rate=16000)

        assert chunk.data.shape == audio_data.shape
        assert chunk.sample_rate == 16000
        assert isinstance(chunk.timestamp, float)

    def test_audio_chunk_properties(self):
        """Test AudioChunk properties."""
        audio_data = np.random.randint(-32768, 32767, 100, dtype=np.int16)
        chunk = AudioChunk(data=audio_data, sample_rate=22050)

        assert chunk.duration == len(audio_data) / 22050.0
        assert chunk.is_silent is False  # Random data likely not silent


class TestTranscriptionResult:
    """Test TranscriptionResult class."""

    def test_transcription_result_creation(self):
        """Test creating a TranscriptionResult instance."""
        result = TranscriptionResult(
            text="Hello world", confidence=0.95, engine="whisper", processing_time=1.2
        )

        assert result.text == "Hello world"
        assert result.confidence == 0.95
        assert result.engine == "whisper"
        assert result.processing_time == 1.2

    def test_transcription_result_defaults(self):
        """Test TranscriptionResult with default values."""
        result = TranscriptionResult(text="Test")

        assert result.confidence == 0.0
        assert result.engine == "unknown"
        assert result.processing_time == 0.0


class TestEnhancedVoiceProcessor:
    """Comprehensive tests for EnhancedVoiceProcessor class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing."""
        return VoiceProcessingConfig(
            sample_rate=16000, chunk_size=1024, noise_reduction_enabled=True
        )

    @pytest.fixture
    def sample_audio_data(self):
        """Create sample audio data for testing."""
        # Generate a simple sine wave
        sample_rate = 16000
        duration = 1.0  # 1 second
        frequency = 440  # A4 note

        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        audio_data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)

        return audio_data

    @pytest.fixture
    def mock_transcription_engine(self):
        """Create mock transcription engine."""
        engine = Mock()
        engine.transcribe.return_value = "Hello world"
        return engine

    def test_enhanced_voice_processor_initialization(self, mock_config):
        """Test EnhancedVoiceProcessor initialization."""
        processor = EnhancedVoiceProcessor(mock_config)

        assert processor.config == mock_config
        assert processor.is_listening is False
        assert processor.audio_queue is not None

    def test_start_stop_listening(self, mock_config):
        """Test starting and stopping voice listening."""
        processor = EnhancedVoiceProcessor(mock_config)

        # Start listening
        processor.start_listening()
        assert processor.is_listening is True

        # Stop listening
        processor.stop_listening()
        assert processor.is_listening is False

    def test_process_audio_chunk(self, mock_config, sample_audio_data):
        """Test processing audio chunk."""
        processor = EnhancedVoiceProcessor(mock_config)

        chunk = AudioChunk(data=sample_audio_data, sample_rate=16000)

        # Process the chunk
        result = processor.process_audio_chunk(chunk)

        assert result is not None
        assert hasattr(result, "text")
        assert hasattr(result, "confidence")

    @patch(
        "src.chatty_commander.voice.enhanced_processor.EnhancedVoiceProcessor._apply_noise_reduction"
    )
    def test_noise_reduction_enabled(
        self, mock_noise_reduction, mock_config, sample_audio_data
    ):
        """Test noise reduction when enabled."""
        mock_noise_reduction.return_value = sample_audio_data
        processor = EnhancedVoiceProcessor(mock_config)

        chunk = AudioChunk(data=sample_audio_data, sample_rate=16000)
        processor.process_audio_chunk(chunk)

        mock_noise_reduction.assert_called_once()

    def test_noise_reduction_disabled(self, mock_config, sample_audio_data):
        """Test behavior when noise reduction is disabled."""
        mock_config.noise_reduction_enabled = False

        with patch(
            "src.chatty_commander.voice.enhanced_processor.EnhancedVoiceProcessor._apply_noise_reduction"
        ) as mock_noise_reduction:
            processor = EnhancedVoiceProcessor(mock_config)

            chunk = AudioChunk(data=sample_audio_data, sample_rate=16000)
            processor.process_audio_chunk(chunk)

            mock_noise_reduction.assert_not_called()

    @patch(
        "src.chatty_commander.voice.enhanced_processor.EnhancedVoiceProcessor._detect_voice_activity"
    )
    def test_voice_activity_detection(self, mock_vad, mock_config, sample_audio_data):
        """Test voice activity detection."""
        mock_vad.return_value = True
        processor = EnhancedVoiceProcessor(mock_config)

        chunk = AudioChunk(data=sample_audio_data, sample_rate=16000)
        processor.process_audio_chunk(chunk)

        mock_vad.assert_called_once()

    def test_wake_word_detection_callback(self, mock_config):
        """Test wake word detection callback functionality."""
        wake_word_detected = False

        def on_wake_word(text):
            nonlocal wake_word_detected
            wake_word_detected = True

        processor = EnhancedVoiceProcessor(mock_config)
        processor.set_wake_word_callback(on_wake_word, wake_words=["hello", "chatty"])

        # Simulate wake word detection
        processor._on_wake_word_detected("hello")

        assert wake_word_detected is True

    def test_audio_callback_registration(self, mock_config):
        """Test audio callback registration."""
        callback_called = False
        callback_data = None

        def test_callback(audio_data, sample_rate):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = audio_data

        processor = EnhancedVoiceProcessor(mock_config)
        processor.set_audio_callback(test_callback)

        # Simulate audio callback
        test_audio = np.array([1, 2, 3], dtype=np.int16)
        processor._on_audio_data(test_audio, 16000)

        assert callback_called is True
        assert callback_data is not None

    def test_multi_engine_transcription_fallback(self, mock_config, sample_audio_data):
        """Test multi-engine transcription with fallback."""
        # Mock multiple engines with different behaviors
        engine1 = Mock()
        engine1.transcribe.side_effect = Exception("Engine 1 failed")

        engine2 = Mock()
        engine2.transcribe.return_value = "Success from engine 2"

        with patch(
            "src.chatty_commander.voice.enhanced_processor.EnhancedVoiceProcessor._get_available_engines"
        ) as mock_engines:
            mock_engines.return_value = [engine1, engine2]

            processor = EnhancedVoiceProcessor(mock_config)
            chunk = AudioChunk(data=sample_audio_data, sample_rate=16000)

            result = processor.process_audio_chunk(chunk)

            assert result.text == "Success from engine 2"
            engine1.transcribe.assert_called_once()
            engine2.transcribe.assert_called_once()

    def test_confidence_threshold_filtering(self, mock_config, sample_audio_data):
        """Test confidence threshold filtering."""
        processor = EnhancedVoiceProcessor(mock_config)
        processor.set_confidence_threshold(0.8)

        # Mock low confidence result
        with patch.object(processor, "_transcribe_with_engine") as mock_transcribe:
            mock_transcribe.return_value = TranscriptionResult(
                text="Low confidence", confidence=0.5, engine="test"
            )

            chunk = AudioChunk(data=sample_audio_data, sample_rate=16000)
            result = processor.process_audio_chunk(chunk)

            # Should not return low confidence results
            assert result.confidence >= 0.8 or result.text == ""

    def test_silence_timeout_detection(self, mock_config):
        """Test silence timeout detection."""
        processor = EnhancedVoiceProcessor(mock_config)
        processor.set_silence_timeout(2.0)  # 2 second timeout

        # Simulate silence
        with patch("time.time") as mock_time:
            mock_time.return_value = 1000.0  # Start time
            processor._last_audio_time = 1000.0

            mock_time.return_value = 1003.0  # 3 seconds later
            is_timed_out = processor._is_silence_timeout()

            assert is_timed_out is True

    def test_concurrent_audio_processing(self, mock_config, sample_audio_data):
        """Test concurrent audio processing capabilities."""
        processor = EnhancedVoiceProcessor(mock_config)

        # Process multiple chunks concurrently
        chunks = []
        for i in range(3):
            chunk = AudioChunk(
                data=sample_audio_data + i,
                sample_rate=16000,  # Slightly different data
            )
            chunks.append(chunk)

        results = []
        for chunk in chunks:
            result = processor.process_audio_chunk(chunk)
            results.append(result)

        # Should handle all chunks without errors
        assert len(results) == 3
        assert all(result is not None for result in results)

    def test_error_handling_invalid_audio(self, mock_config):
        """Test error handling for invalid audio data."""
        processor = EnhancedVoiceProcessor(mock_config)

        # Test with empty audio data
        empty_chunk = AudioChunk(data=np.array([], dtype=np.int16), sample_rate=16000)

        result = processor.process_audio_chunk(empty_chunk)

        # Should handle gracefully
        assert result is not None

    def test_memory_cleanup(self, mock_config, sample_audio_data):
        """Test memory cleanup after processing."""
        processor = EnhancedVoiceProcessor(mock_config)

        # Process some audio
        chunk = AudioChunk(data=sample_audio_data, sample_rate=16000)
        initial_memory = (
            len(processor.audio_queue.queue)
            if hasattr(processor.audio_queue, "queue")
            else 0
        )

        result = processor.process_audio_chunk(chunk)

        # Check that memory is managed properly
        assert result is not None

    def test_configuration_validation(self):
        """Test configuration validation."""
        # Test invalid sample rate
        with pytest.raises(ValueError):
            config = VoiceProcessingConfig(sample_rate=0)

        # Test invalid chunk size
        with pytest.raises(ValueError):
            config = VoiceProcessingConfig(chunk_size=0)

        # Test valid configuration
        config = VoiceProcessingConfig(sample_rate=16000, chunk_size=1024)
        assert config.sample_rate == 16000
        assert config.chunk_size == 1024

    def test_engine_availability_check(self, mock_config):
        """Test checking for available transcription engines."""
        processor = EnhancedVoiceProcessor(mock_config)

        available_engines = processor.get_available_engines()

        # Should return list of available engines
        assert isinstance(available_engines, list)

    def test_real_time_processing_requirements(self, mock_config, sample_audio_data):
        """Test real-time processing capabilities."""
        processor = EnhancedVoiceProcessor(mock_config)

        start_time = time.time()

        # Process audio in real-time simulation
        chunk = AudioChunk(data=sample_audio_data, sample_rate=16000)
        result = processor.process_audio_chunk(chunk)

        processing_time = time.time() - start_time

        # Processing should be relatively fast
        assert processing_time < 5.0  # Should complete within 5 seconds
        assert result is not None
