"""Comprehensive tests for TTS backends and TextToSpeech facade."""

from unittest.mock import patch

import pytest

import chatty_commander.voice.tts as tts


class TestMockTTSBackend:
    """Tests for MockTTSBackend."""

    def test_speak_records_text(self) -> None:
        """Test that speak records text in spoken list."""
        backend = tts.MockTTSBackend()
        backend.speak("hello")
        assert backend.spoken == ["hello"]

    def test_speak_multiple(self) -> None:
        """Test multiple speak calls accumulate."""
        backend = tts.MockTTSBackend()
        backend.speak("first")
        backend.speak("second")
        backend.speak("third")
        assert backend.spoken == ["first", "second", "third"]

    def test_is_available(self) -> None:
        """Test that mock backend is always available."""
        backend = tts.MockTTSBackend()
        assert backend.is_available() is True

    def test_empty_speak(self) -> None:
        """Test that empty string is recorded."""
        backend = tts.MockTTSBackend()
        backend.speak("")
        assert backend.spoken == [""]


class TestPyttsx3Backend:
    """Tests for Pyttsx3Backend."""

    def test_missing_dependency(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing pyttsx3 results in unavailable backend."""
        monkeypatch.setattr(tts, "pyttsx3", None)
        backend = tts.Pyttsx3Backend()
        assert backend.is_available() is False

    def test_init_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that init failure results in unavailable backend."""

        class DummyPyttsx3:
            def init(self) -> None:
                raise RuntimeError("init failed")

        monkeypatch.setattr(tts, "pyttsx3", DummyPyttsx3())
        backend = tts.Pyttsx3Backend()
        assert backend.is_available() is False

    def test_speak_raises_when_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that speak raises RuntimeError when engine not available."""
        monkeypatch.setattr(tts, "pyttsx3", None)
        backend = tts.Pyttsx3Backend()
        assert backend.is_available() is False
        # speak should raise RuntimeError when no engine
        try:
            backend.speak("test")
            assert False, "Expected RuntimeError"
        except RuntimeError:
            pass


class TestTextToSpeech:
    """Tests for TextToSpeech facade."""

    def test_mock_backend(self) -> None:
        """Test creating TextToSpeech with mock backend."""
        engine = tts.TextToSpeech(backend="mock")
        assert isinstance(engine.backend, tts.MockTTSBackend)
        assert engine.is_available() is True

    def test_pyttsx3_falls_back_to_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that pyttsx3 falls back to mock when unavailable."""
        monkeypatch.setattr(tts, "pyttsx3", None)
        engine = tts.TextToSpeech(backend="pyttsx3")
        assert isinstance(engine.backend, tts.MockTTSBackend)

    def test_unknown_backend_raises(self) -> None:
        """Test that unknown backend raises ValueError."""
        try:
            tts.TextToSpeech(backend="nonexistent")
            assert False, "Expected ValueError"
        except ValueError as e:
            assert "nonexistent" in str(e)

    def test_speak_delegates_to_backend(self) -> None:
        """Test that speak delegates to backend."""
        engine = tts.TextToSpeech(backend="mock")
        engine.speak("test message")
        assert engine.backend.spoken == ["test message"]

    def test_speak_logs_error_on_failure(self) -> None:
        """Test that speak logs error when backend raises."""
        engine = tts.TextToSpeech(backend="mock")
        with patch.object(engine.backend, "speak", side_effect=RuntimeError("boom")):
            with patch.object(tts, "logger") as logger_mock:
                engine.speak("hello")
                logger_mock.error.assert_called_once()

    def test_get_backend_info(self) -> None:
        """Test backend info returns correct type and availability."""
        engine = tts.TextToSpeech(backend="mock")
        info = engine.get_backend_info()
        assert info == {
            "backend_type": "MockTTSBackend",
            "is_available": True,
        }

    def test_is_available_delegates(self) -> None:
        """Test that is_available delegates to backend."""
        engine = tts.TextToSpeech(backend="mock")
        assert engine.is_available() is True
