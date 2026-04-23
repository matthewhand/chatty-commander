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

"""Tests for transcription module."""

from unittest.mock import patch

import pytest

from src.chatty_commander.voice.transcription import (
    MockTranscriptionBackend,
    TranscriptionBackend,
    VoiceTranscriber,
)


class TestTranscriptionBackend:
    """Tests for TranscriptionBackend abstract class."""

    def test_cannot_instantiate_directly(self):
        """Test that TranscriptionBackend cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TranscriptionBackend()


class TestMockTranscriptionBackend:
    """Tests for MockTranscriptionBackend."""

    def test_default_responses(self):
        """Test default mock responses."""
        backend = MockTranscriptionBackend()
        assert len(backend.responses) > 0
        assert "hello world" in backend.responses

    def test_custom_responses(self):
        """Test custom mock responses."""
        custom = ["response 1", "response 2"]
        backend = MockTranscriptionBackend(responses=custom)
        assert backend.responses == custom

    def test_transcribe_returns_response(self):
        """Test transcribe returns a response."""
        backend = MockTranscriptionBackend()
        result = backend.transcribe(b"dummy audio")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_transcribe_cycles_through_responses(self):
        """Test transcribe cycles through responses."""
        backend = MockTranscriptionBackend(responses=["a", "b", "c"])
        results = [backend.transcribe(b"") for _ in range(5)]
        assert results[0] == "a"
        assert results[1] == "b"
        assert results[2] == "c"
        assert results[3] == "a"  # Cycles back

    def test_call_count_increments(self):
        """Test call count increments."""
        backend = MockTranscriptionBackend()
        assert backend.call_count == 0
        backend.transcribe(b"")
        assert backend.call_count == 1
        backend.transcribe(b"")
        assert backend.call_count == 2

    def test_is_available(self):
        """Test mock backend is always available."""
        backend = MockTranscriptionBackend()
        assert backend.is_available() is True

    def test_transcribe_ignores_audio_data(self):
        """Test transcribe ignores audio data content."""
        backend = MockTranscriptionBackend(responses=["fixed"])
        result1 = backend.transcribe(b"audio1")
        result2 = backend.transcribe(b"completely different audio")
        # Both should return the same response with single item list
        assert result1 == "fixed"
        assert result2 == "fixed"


class TestVoiceTranscriber:
    """Tests for VoiceTranscriber."""

    def test_init_with_mock_backend(self):
        """Test initialization with mock backend."""
        transcriber = VoiceTranscriber(backend="mock")
        assert transcriber.is_available() is True

    def test_init_with_whisper_local(self):
        """Test initialization with whisper local backend."""
        # May fall back to mock if whisper not available
        transcriber = VoiceTranscriber(backend="whisper_local")
        assert transcriber is not None

    def test_default_chunk_size(self):
        """Test default chunk size."""
        transcriber = VoiceTranscriber(backend="mock")
        assert transcriber.chunk_size == 1024

    def test_custom_chunk_size(self):
        """Test custom chunk size."""
        transcriber = VoiceTranscriber(backend="mock", chunk_size=2048)
        assert transcriber.chunk_size == 2048

    def test_default_sample_rate(self):
        """Test default sample rate."""
        transcriber = VoiceTranscriber(backend="mock")
        assert transcriber.sample_rate == 16000

    def test_custom_sample_rate(self):
        """Test custom sample rate."""
        transcriber = VoiceTranscriber(backend="mock", sample_rate=44100)
        assert transcriber.sample_rate == 44100

    def test_default_channels(self):
        """Test default channels."""
        transcriber = VoiceTranscriber(backend="mock")
        assert transcriber.channels == 1

    def test_custom_channels(self):
        """Test custom channels."""
        transcriber = VoiceTranscriber(backend="mock", channels=2)
        assert transcriber.channels == 2

    def test_default_record_timeout(self):
        """Test default record timeout."""
        transcriber = VoiceTranscriber(backend="mock")
        assert transcriber.record_timeout == 5.0

    def test_custom_record_timeout(self):
        """Test custom record timeout."""
        transcriber = VoiceTranscriber(backend="mock", record_timeout=10.0)
        assert transcriber.record_timeout == 10.0

    def test_default_silence_timeout(self):
        """Test default silence timeout."""
        transcriber = VoiceTranscriber(backend="mock")
        assert transcriber.silence_timeout == 1.0

    def test_transcribe_audio_data(self):
        """Test transcribing audio data."""
        transcriber = VoiceTranscriber(backend="mock")
        result = transcriber.transcribe_audio_data(b"test audio")
        assert isinstance(result, str)

    def test_record_and_transcribe_mock(self):
        """Test record and transcribe with mock backend."""
        transcriber = VoiceTranscriber(backend="mock")
        result = transcriber.record_and_transcribe()
        assert isinstance(result, str)


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_audio_data(self):
        """Test transcribing empty audio data."""
        backend = MockTranscriptionBackend()
        result = backend.transcribe(b"")
        assert isinstance(result, str)

    def test_large_audio_data(self):
        """Test transcribing large audio data."""
        backend = MockTranscriptionBackend()
        large_audio = b"x" * 100000
        result = backend.transcribe(large_audio)
        assert isinstance(result, str)

    def test_single_response_list(self):
        """Test with single response in list."""
        backend = MockTranscriptionBackend(responses=["only"])
        for _ in range(3):
            assert backend.transcribe(b"") == "only"
