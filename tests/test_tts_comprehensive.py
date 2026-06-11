"""Comprehensive tests for TTS backends and TextToSpeech facade."""

from unittest.mock import AsyncMock, MagicMock, patch

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


def _make_fake_edge_tts():
    """Return a fake ``edge_tts`` module whose Communicate records args.

    ``Communicate(text, voice)`` records the call; the instance's ``save`` is an
    :class:`AsyncMock` so it can be awaited without any network.
    """
    fake = MagicMock(name="edge_tts")
    instances: list[MagicMock] = []

    def _communicate(text, voice):
        inst = MagicMock(name="Communicate")
        inst.text = text
        inst.voice = voice
        inst.save = AsyncMock()
        instances.append(inst)
        return inst

    fake.Communicate.side_effect = _communicate
    fake._instances = instances
    return fake


class TestEdgeTTSBackend:
    """Tests for EdgeTTSBackend."""

    def test_is_available_true_when_imported(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(tts, "edge_tts", _make_fake_edge_tts())
        assert tts.EdgeTTSBackend().is_available() is True

    def test_is_available_false_when_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(tts, "edge_tts", None)
        assert tts.EdgeTTSBackend().is_available() is False

    def test_speak_raises_when_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(tts, "edge_tts", None)
        backend = tts.EdgeTTSBackend()
        with pytest.raises(RuntimeError):
            backend.speak("hello")

    def test_speak_synthesizes_and_plays(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake = _make_fake_edge_tts()
        monkeypatch.setattr(tts, "edge_tts", fake)
        backend = tts.EdgeTTSBackend(voice="en-GB-RyanNeural")
        play_mock = MagicMock()
        monkeypatch.setattr(backend, "_play_file", play_mock)

        backend.speak("hello world")

        fake.Communicate.assert_called_once_with("hello world", "en-GB-RyanNeural")
        inst = fake._instances[0]
        inst.save.assert_awaited_once()
        play_mock.assert_called_once()

    def test_play_file_degrades_gracefully(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No playsound, no player on PATH -> warns instead of raising."""
        # Force the optional ``playsound`` import to fail.
        import builtins

        real_import = builtins.__import__

        def _fake_import(name, *args, **kwargs):
            if name == "playsound":
                raise ImportError("no playsound")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _fake_import)
        monkeypatch.setattr(tts.shutil, "which", lambda _exe: None)
        monkeypatch.setattr(tts, "edge_tts", _make_fake_edge_tts())
        backend = tts.EdgeTTSBackend()
        with patch.object(tts, "logger") as logger_mock:
            backend._play_file("/tmp/does-not-exist.mp3")
            logger_mock.warning.assert_called_once()


class TestSynthesizeToFile:
    """Tests for the playback-free synthesize_to_file helper."""

    def test_raises_when_edge_tts_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(tts, "edge_tts", None)
        with pytest.raises(RuntimeError):
            tts.synthesize_to_file("hi", "/tmp/out.mp3")

    def test_writes_via_mocked_save(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        fake = _make_fake_edge_tts()
        monkeypatch.setattr(tts, "edge_tts", fake)
        out = tmp_path / "out.mp3"

        result = tts.synthesize_to_file("hello", out)

        assert result == out
        fake.Communicate.assert_called_once_with("hello", tts.DEFAULT_EDGE_VOICE)
        fake._instances[0].save.assert_awaited_once_with(str(out))

    def test_custom_voice(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        fake = _make_fake_edge_tts()
        monkeypatch.setattr(tts, "edge_tts", fake)
        out = tmp_path / "out.mp3"

        tts.synthesize_to_file("hello", out, voice="en-GB-RyanNeural")

        fake.Communicate.assert_called_once_with("hello", "en-GB-RyanNeural")


class TestTextToSpeech:
    """Tests for TextToSpeech facade."""

    def test_edge_backend_selected_when_available(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(tts, "edge_tts", _make_fake_edge_tts())
        engine = tts.TextToSpeech(backend="edge")
        assert isinstance(engine.backend, tts.EdgeTTSBackend)
        # alias accepted too
        engine2 = tts.TextToSpeech(backend="edge-tts")
        assert isinstance(engine2.backend, tts.EdgeTTSBackend)

    def test_edge_voice_passed_through(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(tts, "edge_tts", _make_fake_edge_tts())
        engine = tts.TextToSpeech(backend="edge", voice="en-GB-RyanNeural")
        assert isinstance(engine.backend, tts.EdgeTTSBackend)
        assert engine.backend.voice == "en-GB-RyanNeural"

    def test_edge_falls_back_to_mock_when_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(tts, "edge_tts", None)
        engine = tts.TextToSpeech(backend="edge")
        assert isinstance(engine.backend, tts.MockTTSBackend)


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
