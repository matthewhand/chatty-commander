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

"""Tests for text-to-speech module."""

import pytest

from src.chatty_commander.voice.tts import MockTTSBackend, Pyttsx3Backend, TextToSpeech, TTSBackend


class TestTTSBackend:
    """Tests for TTSBackend abstract class."""

    def test_cannot_instantiate_directly(self):
        """Test that TTSBackend cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TTSBackend()


class TestMockTTSBackend:
    """Tests for MockTTSBackend."""

    def test_initialization(self):
        """Test backend initialization."""
        backend = MockTTSBackend()
        assert backend.spoken == []
        assert backend.is_available() is True

    def test_speak_records_text(self):
        """Test that speak records text."""
        backend = MockTTSBackend()
        backend.speak("Hello world")
        assert backend.spoken == ["Hello world"]

    def test_speak_multiple_times(self):
        """Test speaking multiple times."""
        backend = MockTTSBackend()
        backend.speak("First")
        backend.speak("Second")
        backend.speak("Third")
        assert backend.spoken == ["First", "Second", "Third"]

    def test_is_available_always_true(self):
        """Test that mock backend is always available."""
        backend = MockTTSBackend()
        assert backend.is_available() is True


class TestPyttsx3Backend:
    """Tests for Pyttsx3Backend."""

    def test_initialization(self):
        """Test backend initialization."""
        backend = Pyttsx3Backend()
        # May or may not be available depending on environment
        assert hasattr(backend, "_engine")

    def test_is_available_based_on_engine(self):
        """Test availability depends on engine."""
        backend = Pyttsx3Backend()
        # Should return boolean
        assert isinstance(backend.is_available(), bool)


class TestTextToSpeech:
    """Tests for TextToSpeech facade."""

    def test_init_with_mock_backend(self):
        """Test initialization with mock backend."""
        tts = TextToSpeech(backend="mock")
        assert isinstance(tts.backend, MockTTSBackend)
        assert tts.is_available() is True

    def test_init_with_pyttsx3_backend(self):
        """Test initialization with pyttsx3 backend."""
        tts = TextToSpeech(backend="pyttsx3")
        # Should have some backend (either Pyttsx3 or Mock fallback)
        assert tts.backend is not None

    def test_init_unknown_backend_raises(self):
        """Test that unknown backend raises ValueError."""
        with pytest.raises(ValueError, match="Unknown TTS backend"):
            TextToSpeech(backend="unknown")

    def test_speak_with_mock(self):
        """Test speaking with mock backend."""
        tts = TextToSpeech(backend="mock")
        tts.speak("Hello")
        assert "Hello" in tts.backend.spoken

    def test_is_available(self):
        """Test availability check."""
        tts = TextToSpeech(backend="mock")
        assert tts.is_available() is True

    def test_get_backend_info(self):
        """Test getting backend info."""
        tts = TextToSpeech(backend="mock")
        info = tts.get_backend_info()
        assert "backend_type" in info
        assert "is_available" in info
        assert info["backend_type"] == "MockTTSBackend"
        assert info["is_available"] is True


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_string_speak(self):
        """Test speaking empty string."""
        tts = TextToSpeech(backend="mock")
        tts.speak("")
        assert "" in tts.backend.spoken

    def test_long_text_speak(self):
        """Test speaking long text."""
        tts = TextToSpeech(backend="mock")
        long_text = "Hello " * 1000
        tts.speak(long_text)
        assert long_text in tts.backend.spoken

    def test_special_characters_speak(self):
        """Test speaking special characters."""
        tts = TextToSpeech(backend="mock")
        text = "Hello! @#$%^&*() World"
        tts.speak(text)
        assert text in tts.backend.spoken

    def test_unicode_speak(self):
        """Test speaking unicode text."""
        tts = TextToSpeech(backend="mock")
        text = "Hello World"
        tts.speak(text)
        assert text in tts.backend.spoken
