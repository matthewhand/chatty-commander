# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction.

"""Coverage-focused tests for chatty_commander.voice.transcription.

These tests target uncovered error/branch/lifecycle paths not exercised by
tests/test_transcription_comprehensive.py. External dependencies (whisper,
openai, pyaudio, numpy) are mocked at the import boundary so the suite is
hermetic and fast. In this environment ``AUDIO_DEPS_AVAILABLE`` is False
(pyaudio/numpy not installed), so the module-level globals ``np`` and
``pyaudio`` are ``None`` and must be patched where exercised.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

import chatty_commander.voice.transcription as tmod
from chatty_commander.voice.transcription import (
    MockTranscriptionBackend,
    VoiceTranscriber,
    WhisperAPIBackend,
    WhisperLocalBackend,
)


# ---------------------------------------------------------------------------
# WhisperLocalBackend: init + transcribe error/availability branches
# ---------------------------------------------------------------------------
class TestWhisperLocalBranches:
    def test_initialize_model_import_error(self):
        """ImportError during model load leaves _model as None (line 85-88)."""
        # Ensure 'whisper' is absent so `import whisper` raises ImportError.
        with patch.dict(sys.modules, {"whisper": None}):
            backend = WhisperLocalBackend()
        assert backend._model is None
        assert backend.is_available() is False

    def test_initialize_model_generic_exception(self):
        """A non-import error from load_model is caught (lines 89-90)."""
        fake_whisper = MagicMock()
        fake_whisper.load_model.side_effect = RuntimeError("gpu boom")
        with patch.dict(sys.modules, {"whisper": fake_whisper}):
            backend = WhisperLocalBackend(model_size="small")
        # Exception swallowed; model never set.
        assert backend._model is None
        assert backend.is_available() is False

    def test_transcribe_internal_exception_returns_empty(self):
        """If transcription raises, returns '' (lines 110-112)."""
        backend = WhisperLocalBackend.__new__(WhisperLocalBackend)
        backend.model_size = "base"
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = RuntimeError("decode fail")
        backend._model = mock_model

        mock_np = MagicMock()
        mock_np.frombuffer.return_value.astype.return_value.__truediv__ = MagicMock(
            return_value=MagicMock()
        )
        with patch.object(tmod, "np", mock_np):
            result = backend.transcribe(b"\x00\x01")
        assert result == ""

    def test_transcribe_strips_and_returns_text(self):
        """Happy path strips whitespace from result text (lines 99-108)."""
        backend = WhisperLocalBackend.__new__(WhisperLocalBackend)
        backend.model_size = "base"
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "  spoken words  "}
        backend._model = mock_model

        mock_np = MagicMock()
        arr = MagicMock()
        mock_np.frombuffer.return_value = arr
        arr.astype.return_value = arr
        arr.__truediv__ = MagicMock(return_value=arr)
        with patch.object(tmod, "np", mock_np):
            result = backend.transcribe(b"\x00\x01", sample_rate=8000)
        assert result == "spoken words"

    def test_transcribe_missing_text_key(self):
        """result.get('text') default '' when key absent (line 105)."""
        backend = WhisperLocalBackend.__new__(WhisperLocalBackend)
        backend.model_size = "base"
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {}
        backend._model = mock_model

        mock_np = MagicMock()
        arr = MagicMock()
        mock_np.frombuffer.return_value = arr
        arr.astype.return_value = arr
        arr.__truediv__ = MagicMock(return_value=arr)
        with patch.object(tmod, "np", mock_np):
            result = backend.transcribe(b"\x00\x01")
        assert result == ""


# ---------------------------------------------------------------------------
# WhisperAPIBackend: init error branches + full transcribe path
# ---------------------------------------------------------------------------
class TestWhisperAPIBranches:
    def test_initialize_client_import_error(self):
        """ImportError -> client stays None (lines 133-136)."""
        with patch.dict(sys.modules, {"openai": None}):
            backend = WhisperAPIBackend(api_key="k")
        assert backend._client is None
        assert backend.is_available() is False

    def test_initialize_client_generic_exception(self):
        """Non-import error from OpenAI() is caught (lines 137-138)."""
        fake_openai = MagicMock()
        fake_openai.OpenAI.side_effect = RuntimeError("bad creds")
        with patch.dict(sys.modules, {"openai": fake_openai}):
            backend = WhisperAPIBackend(api_key="k")
        assert backend._client is None

    def test_transcribe_happy_path_writes_wav_and_cleans_up(self, tmp_path):
        """Full transcribe path: writes temp wav, calls API, strips, unlinks.

        Covers lines 145-166 and the finally-block cleanup (171-177).
        """
        backend = WhisperAPIBackend.__new__(WhisperAPIBackend)
        backend.api_key = None
        mock_client = MagicMock()
        transcript = MagicMock()
        transcript.text = "  api result  "
        mock_client.audio.transcriptions.create.return_value = transcript
        backend._client = mock_client

        captured = {}
        real_unlink = tmod.os.unlink

        def spy_unlink(path):
            captured["unlinked"] = path
            return real_unlink(path)

        # Provide valid 16-bit PCM frames so wave.writeframes succeeds.
        audio = b"\x00\x01" * 10
        with patch.object(tmod.os, "unlink", side_effect=spy_unlink):
            result = backend.transcribe(audio, sample_rate=16000)

        assert result == "api result"
        mock_client.audio.transcriptions.create.assert_called_once()
        _, kwargs = mock_client.audio.transcriptions.create.call_args
        assert kwargs["model"] == "whisper-1"
        # Temp file was cleaned up.
        assert "unlinked" in captured
        assert not tmod.os.path.exists(captured["unlinked"])

    def test_transcribe_api_error_returns_empty_and_cleans_up(self):
        """API exception -> returns '' and still unlinks temp file (168-177)."""
        backend = WhisperAPIBackend.__new__(WhisperAPIBackend)
        backend.api_key = None
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.side_effect = RuntimeError("503")
        backend._client = mock_client

        captured = {}

        def spy_unlink(path):
            captured["unlinked"] = path
            return tmod.os.path.exists(path) and None

        with patch.object(tmod.os, "unlink", side_effect=spy_unlink):
            result = backend.transcribe(b"\x00\x01" * 5)
        assert result == ""
        assert "unlinked" in captured

    def test_transcribe_unlink_oserror_swallowed(self):
        """OSError during cleanup is swallowed (lines 176-177)."""
        backend = WhisperAPIBackend.__new__(WhisperAPIBackend)
        backend.api_key = None
        mock_client = MagicMock()
        transcript = MagicMock()
        transcript.text = "ok"
        mock_client.audio.transcriptions.create.return_value = transcript
        backend._client = mock_client

        with patch.object(tmod.os, "unlink", side_effect=OSError("gone")):
            result = backend.transcribe(b"\x00\x01" * 5)
        assert result == "ok"


# ---------------------------------------------------------------------------
# VoiceTranscriber: record_and_transcribe and _record_audio branches
# ---------------------------------------------------------------------------
class TestRecordAndTranscribe:
    def test_record_and_transcribe_no_audio_deps(self):
        """When AUDIO_DEPS_AVAILABLE is False, falls back to backend transcribe
        on empty bytes (lines 260-262)."""
        with patch.object(tmod, "AUDIO_DEPS_AVAILABLE", False):
            t = VoiceTranscriber(backend="mock")
            result = t.record_and_transcribe()
        # Mock backend returns its first canned response.
        assert result == "hello world"

    def test_record_and_transcribe_happy_path(self):
        """audio_data present -> transcribe_audio_data invoked (lines 266-267)."""
        with patch.object(tmod, "AUDIO_DEPS_AVAILABLE", True):
            t = VoiceTranscriber(backend="mock")
            with patch.object(t, "_record_audio", return_value=b"frames"):
                result = t.record_and_transcribe()
        assert result == "hello world"

    def test_record_and_transcribe_empty_recording_returns_empty(self):
        """Empty recorded bytes -> returns '' (line 268)."""
        with patch.object(tmod, "AUDIO_DEPS_AVAILABLE", True):
            t = VoiceTranscriber(backend="mock")
            with patch.object(t, "_record_audio", return_value=b""):
                result = t.record_and_transcribe()
        assert result == ""

    def test_record_audio_no_audio_deps_returns_empty(self):
        """_record_audio short-circuits to b'' without deps (line 276)."""
        with patch.object(tmod, "AUDIO_DEPS_AVAILABLE", False):
            t = VoiceTranscriber(backend="mock")
        with patch.object(tmod, "AUDIO_DEPS_AVAILABLE", False):
            assert t._record_audio() == b""

    def test_record_audio_silence_timeout_break(self):
        """Loud chunk resets silence, then quiet chunks trip silence timeout
        and break the loop (lines 301-309, 311)."""
        mock_pyaudio = MagicMock()
        mock_audio_instance = MagicMock()
        mock_stream = MagicMock()
        mock_audio_instance.open.return_value = mock_stream
        mock_pyaudio.PyAudio.return_value = mock_audio_instance
        mock_pyaudio.paInt16 = 8
        mock_stream.read.return_value = b"\x00\x01\x02\x03"

        mock_np = MagicMock()
        # astype() result must support len() for the volume divisor.
        audio_array = MagicMock()
        audio_array.__len__ = MagicMock(return_value=4)
        mock_np.frombuffer.return_value.astype.return_value = audio_array
        mock_np.dot.return_value = 1.0
        # First chunk loud (else branch line 311 resets silence_start),
        # then a quiet chunk below threshold sets silence_start, then another
        # quiet chunk trips the silence timeout (lines 304-309).
        mock_np.sqrt.side_effect = [1000.0, 10.0, 10.0, 10.0]

        # Drive time.time() with a list + clamped index so the loop can call it
        # a variable number of times without raising StopIteration.
        seq = [0.0, 0.1, 0.2, 0.3, 0.5, 0.6, 5.0, 5.1, 5.2, 5.3]
        state = {"i": 0}

        def fake_time():
            i = state["i"]
            state["i"] = min(i + 1, len(seq) - 1)
            return seq[i]

        with (
            patch.object(tmod, "AUDIO_DEPS_AVAILABLE", True),
            patch.object(tmod, "pyaudio", mock_pyaudio),
            patch.object(tmod, "np", mock_np),
            patch.object(tmod.time, "time", fake_time),
        ):
            t = VoiceTranscriber(backend="mock")
            t.silence_timeout = 0.0  # any elapsed silence triggers break
            t.silence_threshold = 500.0
            t.record_timeout = 100.0
            result = t._record_audio()

        assert isinstance(result, bytes)
        mock_stream.read.assert_called()

    def test_record_audio_record_timeout_break(self):
        """Loud audio that never goes silent breaks on record_timeout
        (lines 304/311 else + 314-316)."""
        mock_pyaudio = MagicMock()
        mock_audio_instance = MagicMock()
        mock_stream = MagicMock()
        mock_audio_instance.open.return_value = mock_stream
        mock_pyaudio.PyAudio.return_value = mock_audio_instance
        mock_pyaudio.paInt16 = 8
        mock_stream.read.return_value = b"\x00\x01\x02\x03"

        mock_np = MagicMock()
        audio_array = MagicMock()
        audio_array.__len__ = MagicMock(return_value=4)
        mock_np.frombuffer.return_value.astype.return_value = audio_array
        mock_np.sqrt.return_value = 99999.0  # always loud
        mock_np.dot.return_value = 1.0

        # Monotonic-ish clock: starts at 0, jumps past record_timeout after a
        # couple of calls. A list + index avoids StopIteration if the loop body
        # calls time.time() a varying number of times.
        seq = [0.0, 0.1, 0.2, 999.0]
        state = {"i": 0}

        def fake_time():
            i = state["i"]
            state["i"] = min(i + 1, len(seq) - 1)
            return seq[i]

        with (
            patch.object(tmod, "AUDIO_DEPS_AVAILABLE", True),
            patch.object(tmod, "pyaudio", mock_pyaudio),
            patch.object(tmod, "np", mock_np),
            patch.object(tmod.time, "time", fake_time),
        ):
            t = VoiceTranscriber(backend="mock")
            t.silence_timeout = 100.0
            t.record_timeout = 1.0
            result = t._record_audio()

        assert isinstance(result, bytes)

    def test_record_audio_inner_read_exception_breaks(self):
        """Exception inside loop is caught and breaks (lines 318-320), then
        cleanup runs in finally."""
        mock_pyaudio = MagicMock()
        mock_audio_instance = MagicMock()
        mock_stream = MagicMock()
        mock_audio_instance.open.return_value = mock_stream
        mock_pyaudio.PyAudio.return_value = mock_audio_instance
        mock_pyaudio.paInt16 = 8
        mock_stream.read.side_effect = RuntimeError("overflow")

        with (
            patch.object(tmod, "AUDIO_DEPS_AVAILABLE", True),
            patch.object(tmod, "pyaudio", mock_pyaudio),
            patch.object(tmod, "np", MagicMock()),
            patch.object(tmod.time, "time", lambda: 0.0),
        ):
            t = VoiceTranscriber(backend="mock")
            result = t._record_audio()

        assert result == b""
        mock_stream.stop_stream.assert_called_once()
        mock_audio_instance.terminate.assert_called_once()


# ---------------------------------------------------------------------------
# VoiceTranscriber._cleanup_audio: exception handling branches
# ---------------------------------------------------------------------------
class TestCleanupAudio:
    def test_cleanup_stream_close_exception_swallowed(self):
        """Stream close raising is logged and swallowed (lines 336-337)."""
        t = VoiceTranscriber(backend="mock")
        mock_stream = MagicMock()
        mock_stream.stop_stream.side_effect = RuntimeError("dead")
        t._stream = mock_stream
        t._audio = None

        t._cleanup_audio()  # should not raise
        assert t._stream is None

    def test_cleanup_audio_terminate_exception_swallowed(self):
        """Audio terminate raising is logged and swallowed (lines 344-345)."""
        t = VoiceTranscriber(backend="mock")
        mock_audio = MagicMock()
        mock_audio.terminate.side_effect = RuntimeError("dead")
        t._stream = None
        t._audio = mock_audio

        t._cleanup_audio()  # should not raise
        assert t._audio is None

    def test_cleanup_audio_noop_when_nothing_setup(self):
        """No stream/audio -> cleanup is a harmless no-op."""
        t = VoiceTranscriber(backend="mock")
        t._stream = None
        t._audio = None
        t._cleanup_audio()
        assert t._stream is None and t._audio is None


# ---------------------------------------------------------------------------
# Backend selection / availability dispatch
# ---------------------------------------------------------------------------
class TestBackendSelection:
    def test_unknown_backend_raises(self):
        t = VoiceTranscriber(backend="mock")
        with pytest.raises(ValueError, match="Unknown transcription backend: bogus"):
            t._create_backend("bogus")

    def test_audio_deps_unavailable_forces_mock(self):
        """Requesting whisper_local without deps coerces to mock backend."""
        with patch.object(tmod, "AUDIO_DEPS_AVAILABLE", False):
            t = VoiceTranscriber(backend="whisper_api")
        assert isinstance(t._backend, MockTranscriptionBackend)

    def test_mock_backend_is_always_available(self):
        assert MockTranscriptionBackend().is_available() is True
