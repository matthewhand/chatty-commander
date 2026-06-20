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

"""Coverage tests for src/chatty_commander/voice/enhanced_processor.py.

All external deps (whisper, speech_recognition, webrtcvad, noisereduce,
pvporcupine, pyaudio, librosa, scipy) are imported lazily inside methods,
so we mock them at the import boundary via sys.modules and by overriding
component attributes after construction. No real models/devices are used.
"""

from __future__ import annotations

import sys
import types
from datetime import datetime
from unittest import mock

import numpy as np
import pytest

from chatty_commander.voice.enhanced_processor import (
    EnhancedVoiceProcessor,
    VoiceProcessingConfig,
    VoiceResult,
    create_enhanced_voice_processor,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bare_processor(**config_kwargs) -> EnhancedVoiceProcessor:
    """Construct a processor while neutralising the import-heavy init steps.

    Each test that exercises a specific init branch patches it explicitly;
    here we stub _initialize_components so the object is cheap to build.
    """
    config = VoiceProcessingConfig(**config_kwargs)
    with mock.patch.object(EnhancedVoiceProcessor, "_initialize_components"):
        return EnhancedVoiceProcessor(config)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


def test_config_defaults():
    cfg = VoiceProcessingConfig()
    assert cfg.sample_rate == 16000
    assert cfg.chunk_size == 1024
    assert cfg.confidence_threshold == 0.7
    assert cfg.voice_activity_detection is True


def test_voice_result_optional_fields():
    r = VoiceResult(text="hi", confidence=0.5, duration=1.0, timestamp=datetime.now())
    assert r.language is None
    assert r.intent is None
    assert r.wake_word_detected is False


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def test_factory_maps_config_keys():
    with mock.patch.object(EnhancedVoiceProcessor, "_initialize_components"):
        proc = create_enhanced_voice_processor(
            {
                "sample_rate": 8000,
                "chunk_size": 512,
                "noise_reduction": False,
                "vad": False,
                "confidence_threshold": 0.4,
                "silence_timeout": 1.5,
                "max_duration": 10.0,
            }
        )
    assert proc.config.sample_rate == 8000
    assert proc.config.chunk_size == 512
    assert proc.config.noise_reduction_enabled is False
    assert proc.config.voice_activity_detection is False
    assert proc.config.confidence_threshold == 0.4
    assert proc.config.silence_timeout == 1.5
    assert proc.config.max_recording_duration == 10.0


def test_factory_uses_defaults_for_empty_config():
    with mock.patch.object(EnhancedVoiceProcessor, "_initialize_components"):
        proc = create_enhanced_voice_processor({})
    assert proc.config.sample_rate == 16000
    assert proc.config.noise_reduction_enabled is True


# ---------------------------------------------------------------------------
# _initialize_components orchestration
# ---------------------------------------------------------------------------


def test_initialize_components_calls_enabled_subinits():
    cfg = VoiceProcessingConfig(
        noise_reduction_enabled=True, voice_activity_detection=True
    )
    with (
        mock.patch.object(EnhancedVoiceProcessor, "_initialize_noise_reduction") as nr,
        mock.patch.object(EnhancedVoiceProcessor, "_initialize_vad") as vad,
        mock.patch.object(EnhancedVoiceProcessor, "_initialize_transcription") as tr,
        mock.patch.object(
            EnhancedVoiceProcessor, "_initialize_wake_word_detection"
        ) as ww,
    ):
        EnhancedVoiceProcessor(cfg)
    nr.assert_called_once()
    vad.assert_called_once()
    tr.assert_called_once()
    ww.assert_called_once()


def test_initialize_components_skips_disabled_features():
    cfg = VoiceProcessingConfig(
        noise_reduction_enabled=False, voice_activity_detection=False
    )
    with (
        mock.patch.object(EnhancedVoiceProcessor, "_initialize_noise_reduction") as nr,
        mock.patch.object(EnhancedVoiceProcessor, "_initialize_vad") as vad,
        mock.patch.object(EnhancedVoiceProcessor, "_initialize_transcription"),
        mock.patch.object(EnhancedVoiceProcessor, "_initialize_wake_word_detection"),
    ):
        EnhancedVoiceProcessor(cfg)
    nr.assert_not_called()
    vad.assert_not_called()


def test_initialize_components_swallows_exceptions():
    cfg = VoiceProcessingConfig()
    with mock.patch.object(
        EnhancedVoiceProcessor,
        "_initialize_noise_reduction",
        side_effect=RuntimeError("boom"),
    ):
        # Should not raise; error path logs and returns.
        proc = EnhancedVoiceProcessor(cfg)
    assert isinstance(proc, EnhancedVoiceProcessor)


# ---------------------------------------------------------------------------
# _initialize_noise_reduction
# ---------------------------------------------------------------------------


def test_noise_reduction_uses_noisereduce_when_available():
    proc = _bare_processor()
    fake_nr = types.ModuleType("noisereduce")
    with mock.patch.dict(sys.modules, {"noisereduce": fake_nr}):
        proc._initialize_noise_reduction()
    assert proc.noise_reducer is fake_nr


def test_noise_reduction_falls_back_on_import_error():
    proc = _bare_processor()
    with mock.patch.dict(sys.modules, {"noisereduce": None}):
        proc._initialize_noise_reduction()
    assert proc.noise_reducer == proc._basic_noise_reduction


# ---------------------------------------------------------------------------
# _initialize_vad
# ---------------------------------------------------------------------------


def test_vad_uses_webrtcvad_when_available():
    proc = _bare_processor()
    fake_mod = types.ModuleType("webrtcvad")
    sentinel = object()
    fake_mod.Vad = mock.Mock(return_value=sentinel)
    with mock.patch.dict(sys.modules, {"webrtcvad": fake_mod}):
        proc._initialize_vad()
    assert proc.vad is sentinel
    fake_mod.Vad.assert_called_once_with(2)


def test_vad_falls_back_on_import_error():
    proc = _bare_processor()
    with mock.patch.dict(sys.modules, {"webrtcvad": None}):
        proc._initialize_vad()
    assert proc.vad == proc._energy_based_vad


def test_vad_falls_back_on_generic_exception():
    proc = _bare_processor()
    fake_mod = types.ModuleType("webrtcvad")
    fake_mod.Vad = mock.Mock(side_effect=RuntimeError("device error"))
    with mock.patch.dict(sys.modules, {"webrtcvad": fake_mod}):
        proc._initialize_vad()
    assert proc.vad == proc._energy_based_vad


# ---------------------------------------------------------------------------
# _initialize_transcription
# ---------------------------------------------------------------------------


def test_transcription_prefers_whisper():
    proc = _bare_processor()
    fake_whisper = types.ModuleType("whisper")
    model = object()
    fake_whisper.load_model = mock.Mock(return_value=model)
    with mock.patch.dict(sys.modules, {"whisper": fake_whisper}):
        proc._initialize_transcription()
    assert proc.transcription_method == "whisper"
    assert proc.transcriber is model
    fake_whisper.load_model.assert_called_once_with("base")


def test_transcription_falls_back_to_speech_recognition():
    proc = _bare_processor()
    fake_sr = types.ModuleType("speech_recognition")
    rec = object()
    fake_sr.Recognizer = mock.Mock(return_value=rec)
    with mock.patch.dict(
        sys.modules, {"whisper": None, "speech_recognition": fake_sr}
    ):
        proc._initialize_transcription()
    assert proc.transcription_method == "speech_recognition"
    assert proc.transcriber is rec


def test_transcription_ultimate_fallback_none():
    proc = _bare_processor()
    with mock.patch.dict(
        sys.modules, {"whisper": None, "speech_recognition": None}
    ):
        proc._initialize_transcription()
    assert proc.transcription_method == "none"
    assert proc.transcriber is None


# ---------------------------------------------------------------------------
# _initialize_wake_word_detection
# ---------------------------------------------------------------------------


def test_wake_word_uses_porcupine_when_spec_found():
    proc = _bare_processor()
    with mock.patch("importlib.util.find_spec", return_value=object()):
        proc._initialize_wake_word_detection()
    assert proc.wake_word_detector == "porcupine"


def test_wake_word_falls_back_to_simple_when_spec_missing():
    proc = _bare_processor()
    with mock.patch("importlib.util.find_spec", return_value=None):
        proc._initialize_wake_word_detection()
    assert proc.wake_word_detector == "simple"


# ---------------------------------------------------------------------------
# _basic_noise_reduction
# ---------------------------------------------------------------------------


def test_basic_noise_reduction_filters_audio():
    # scipy.signal is imported lazily inside the method. Mock it at the import
    # boundary so this test is hermetic and independent of the real scipy/numpy
    # module state (which sibling test files may patch in sys.modules).
    proc = _bare_processor(sample_rate=16000)
    audio = np.zeros(2048, dtype=np.float64)

    fake_scipy = types.ModuleType("scipy")
    fake_signal = types.ModuleType("scipy.signal")
    fake_signal.butter = mock.Mock(return_value=("b", "a"))
    fake_signal.filtfilt = mock.Mock(return_value=audio)
    fake_scipy.signal = fake_signal
    with mock.patch.dict(
        sys.modules, {"scipy": fake_scipy, "scipy.signal": fake_signal}
    ):
        out = proc._basic_noise_reduction(audio)

    fake_signal.butter.assert_called_once_with(
        4, 300, btype="high", fs=proc.config.sample_rate
    )
    fake_signal.filtfilt.assert_called_once()
    assert out.shape == audio.shape


# ---------------------------------------------------------------------------
# _energy_based_vad
# ---------------------------------------------------------------------------


def test_energy_based_vad_detects_speech_above_threshold():
    proc = _bare_processor()
    loud = (np.ones(320, dtype=np.int16) * 5000).tobytes()
    assert proc._energy_based_vad(loud) is True


def test_energy_based_vad_silence_below_threshold():
    proc = _bare_processor()
    quiet = np.zeros(320, dtype=np.int16).tobytes()
    assert proc._energy_based_vad(quiet) is False


def test_energy_based_vad_empty_chunk_returns_false_no_zero_division():
    """An empty chunk (b"", as PyAudio may return on overflow/close) makes
    len(audio_data) == 0; the VAD must treat it as no-speech rather than
    raising ZeroDivisionError."""
    proc = _bare_processor()
    assert proc._energy_based_vad(b"") is False


# ---------------------------------------------------------------------------
# numpy import safety: module must import even when numpy is absent
# ---------------------------------------------------------------------------


def test_module_imports_with_numpy_absent():
    """Re-importing enhanced_processor with numpy mocked-absent must not crash
    (the top-level ``import numpy`` is wrapped in try/except). The reloaded
    module exposes ``np is None`` and ``NUMPY_AVAILABLE is False``, and an
    instance can still be constructed (it degrades instead of raising)."""
    import importlib

    import chatty_commander.voice.enhanced_processor as epmod

    try:
        # Simulate numpy being uninstalled: setting sys.modules["numpy"] = None
        # makes ``import numpy`` raise ImportError on reload.
        with mock.patch.dict(sys.modules, {"numpy": None}):
            reloaded = importlib.reload(epmod)
            assert reloaded.np is None
            assert reloaded.NUMPY_AVAILABLE is False
            # Construction must not crash even without numpy.
            cfg = reloaded.VoiceProcessingConfig()
            with mock.patch.object(
                reloaded.EnhancedVoiceProcessor, "_initialize_components"
            ):
                proc = reloaded.EnhancedVoiceProcessor(cfg)
            # Energy VAD degrades to "no speech" without numpy.
            assert proc._energy_based_vad(b"\x00\x00") is False
    finally:
        # Restore the real module *after* the numpy patch is lifted, so the
        # reloaded module re-imports the genuine numpy for the rest of the suite.
        importlib.reload(epmod)


# ---------------------------------------------------------------------------
# _detect_wake_words
# ---------------------------------------------------------------------------


def test_detect_wake_words_matches_multiple():
    proc = _bare_processor()
    detected = proc._detect_wake_words("Hey Chatty, wake the COMPUTER")
    assert "hey chatty" in detected
    assert "chatty" in detected
    assert "computer" in detected


def test_detect_wake_words_none_present():
    proc = _bare_processor()
    assert proc._detect_wake_words("just some unrelated words") == []


# ---------------------------------------------------------------------------
# _transcribe_audio
# ---------------------------------------------------------------------------


def test_transcribe_audio_whisper_path():
    proc = _bare_processor()
    proc.transcription_method = "whisper"
    proc.transcriber = mock.Mock()
    proc.transcriber.transcribe.return_value = {
        "text": "  hey chatty  ",
        "language": "en",
    }
    result = proc._transcribe_audio(np.zeros(16000, dtype=np.float32))
    assert result.text == "hey chatty"
    assert result.confidence == 0.9
    assert result.language == "en"
    assert result.wake_word_detected is True


def test_transcribe_audio_whisper_missing_language_defaults_en():
    proc = _bare_processor()
    proc.transcription_method = "whisper"
    proc.transcriber = mock.Mock()
    proc.transcriber.transcribe.return_value = {"text": "nothing special"}
    result = proc._transcribe_audio(np.zeros(10, dtype=np.float32))
    assert result.language == "en"
    assert result.wake_word_detected is False


def test_transcribe_audio_speech_recognition_success():
    proc = _bare_processor()
    proc.transcription_method = "speech_recognition"
    recognizer = mock.Mock()
    recognizer.recognize_google.return_value = "computer listen"
    proc.transcriber = recognizer

    fake_sr = types.ModuleType("speech_recognition")
    fake_sr.AudioData = mock.Mock(return_value="audio-obj")
    fake_sr.UnknownValueError = type("UnknownValueError", (Exception,), {})
    fake_sr.RequestError = type("RequestError", (Exception,), {})
    with mock.patch.dict(sys.modules, {"speech_recognition": fake_sr}):
        result = proc._transcribe_audio(np.zeros(10, dtype=np.int16))
    assert result.text == "computer listen"
    assert result.confidence == 0.8
    assert result.wake_word_detected is True


def test_transcribe_audio_speech_recognition_unknown_value():
    proc = _bare_processor()
    proc.transcription_method = "speech_recognition"
    fake_sr = types.ModuleType("speech_recognition")
    fake_sr.AudioData = mock.Mock(return_value="audio-obj")
    fake_sr.UnknownValueError = type("UnknownValueError", (Exception,), {})
    fake_sr.RequestError = type("RequestError", (Exception,), {})
    recognizer = mock.Mock()
    recognizer.recognize_google.side_effect = fake_sr.UnknownValueError()
    proc.transcriber = recognizer
    with mock.patch.dict(sys.modules, {"speech_recognition": fake_sr}):
        result = proc._transcribe_audio(np.zeros(10, dtype=np.int16))
    assert result.text == ""
    assert result.confidence == 0.0
    assert result.language is None


def test_transcribe_audio_speech_recognition_request_error():
    proc = _bare_processor()
    proc.transcription_method = "speech_recognition"
    fake_sr = types.ModuleType("speech_recognition")
    fake_sr.AudioData = mock.Mock(return_value="audio-obj")
    fake_sr.UnknownValueError = type("UnknownValueError", (Exception,), {})
    fake_sr.RequestError = type("RequestError", (Exception,), {})
    recognizer = mock.Mock()
    recognizer.recognize_google.side_effect = fake_sr.RequestError("api down")
    proc.transcriber = recognizer
    with mock.patch.dict(sys.modules, {"speech_recognition": fake_sr}):
        result = proc._transcribe_audio(np.zeros(10, dtype=np.int16))
    assert result.text == ""
    assert result.confidence == 0.0


def test_transcribe_audio_no_engine():
    proc = _bare_processor()
    proc.transcription_method = "none"
    proc.transcriber = None
    result = proc._transcribe_audio(np.zeros(10, dtype=np.float32))
    assert result.text == "[Transcription not available]"
    assert result.confidence == 0.0


def test_transcribe_audio_exception_returns_empty_result():
    proc = _bare_processor()
    proc.transcription_method = "whisper"
    proc.transcriber = mock.Mock()
    proc.transcriber.transcribe.side_effect = RuntimeError("model blew up")
    result = proc._transcribe_audio(np.zeros(10, dtype=np.float32))
    assert result.text == ""
    assert result.confidence == 0.0
    assert result.duration == 0.0


# ---------------------------------------------------------------------------
# _process_audio_chunk
# ---------------------------------------------------------------------------


def _chunk(value: int = 0, n: int = 32) -> bytes:
    return (np.ones(n, dtype=np.int16) * value).tobytes()


def test_process_chunk_callable_noise_reducer_and_speech_start():
    proc = _bare_processor()
    proc.noise_reducer = lambda a: a
    proc.config.noise_reduction_enabled = True
    proc.vad_enabled = True
    proc.vad = lambda chunk: True  # speech detected
    started = []
    proc.on_speech_start = lambda: started.append(True)

    result = proc._process_audio_chunk(_chunk(100))
    assert result is None  # speech started, no transcription yet
    assert proc.speech_detected is True
    assert proc.silence_counter == 0
    assert started == [True]


def test_process_chunk_noisereduce_library_object_branch():
    proc = _bare_processor()
    nr_lib = mock.Mock()  # not callable as a plain func -> use .reduce_noise
    nr_lib.reduce_noise.return_value = np.zeros(32, dtype=np.float32)
    # Force the non-callable branch: a Mock is callable, so simulate a
    # library object by making callable() return False via a real object.

    class FakeNR:
        def reduce_noise(self, y, sr):
            return y

    proc.noise_reducer = FakeNR()
    proc.config.noise_reduction_enabled = True
    proc.vad_enabled = False
    result = proc._process_audio_chunk(_chunk(0))
    assert result is None


def test_process_chunk_webrtcvad_object_branch_silence_triggers_transcription():
    proc = _bare_processor(silence_timeout=0.0)  # threshold becomes 0
    proc.noise_reducer = None
    proc.config.noise_reduction_enabled = False
    proc.vad_enabled = True

    class FakeVad:
        def is_speech(self, chunk, rate):
            return False  # silence

    proc.vad = FakeVad()
    proc.speech_detected = True  # was speaking, now silence ends it
    ended = []
    proc.on_speech_end = lambda: ended.append(True)
    proc._transcribe_audio = mock.Mock(
        return_value=VoiceResult(
            text="done", confidence=0.9, duration=0.1, timestamp=datetime.now()
        )
    )
    result = proc._process_audio_chunk(_chunk(0))
    assert ended == [True]
    assert proc.speech_detected is False
    assert result is not None and result.text == "done"


def test_process_chunk_silence_below_timeout_no_transcription():
    proc = _bare_processor(silence_timeout=100.0)  # very high threshold
    proc.noise_reducer = None
    proc.config.noise_reduction_enabled = False
    proc.vad_enabled = True
    proc.vad = lambda chunk: False  # silence
    proc.speech_detected = True
    result = proc._process_audio_chunk(_chunk(0))
    assert result is None
    assert proc.silence_counter == 1
    assert proc.speech_detected is True  # not enough silence yet


def test_process_chunk_vad_disabled_returns_none():
    proc = _bare_processor()
    proc.noise_reducer = None
    proc.config.noise_reduction_enabled = False
    proc.vad_enabled = False
    assert proc._process_audio_chunk(_chunk(50)) is None


def test_process_chunk_exception_returns_none():
    proc = _bare_processor()
    proc.noise_reducer = mock.Mock(side_effect=RuntimeError("nr fail"))
    proc.config.noise_reduction_enabled = True
    proc.vad_enabled = False
    assert proc._process_audio_chunk(_chunk(10)) is None


# ---------------------------------------------------------------------------
# start_listening / stop_listening lifecycle
# ---------------------------------------------------------------------------


def test_start_listening_spawns_thread_and_is_idempotent():
    proc = _bare_processor()
    with mock.patch.object(proc, "_audio_processing_loop"):
        proc.start_listening()
        assert proc.is_listening is True
        thread = proc.processing_thread
        assert thread is not None
        # Second call is a no-op (already listening).
        proc.start_listening()
        assert proc.processing_thread is thread
    proc.is_listening = False
    if proc.processing_thread:
        proc.processing_thread.join(timeout=1.0)


def test_stop_listening_joins_thread():
    proc = _bare_processor()
    fake_thread = mock.Mock()
    proc.processing_thread = fake_thread
    proc.is_listening = True
    proc.stop_listening()
    assert proc.is_listening is False
    fake_thread.join.assert_called_once_with(timeout=1.0)


def test_stop_listening_without_thread():
    proc = _bare_processor()
    proc.processing_thread = None
    proc.is_listening = True
    proc.stop_listening()  # should not raise
    assert proc.is_listening is False


# ---------------------------------------------------------------------------
# _audio_processing_loop
# ---------------------------------------------------------------------------


def _install_fake_pyaudio(chunks, read_side_effect=None):
    fake_pyaudio = types.ModuleType("pyaudio")
    fake_pyaudio.paInt16 = 8
    stream = mock.Mock()
    if read_side_effect is not None:
        stream.read.side_effect = read_side_effect
    else:
        stream.read.side_effect = chunks
    pa_instance = mock.Mock()
    pa_instance.open.return_value = stream
    fake_pyaudio.PyAudio = mock.Mock(return_value=pa_instance)
    return fake_pyaudio, pa_instance, stream


def test_audio_loop_dispatches_callbacks_and_cleans_up():
    proc = _bare_processor(confidence_threshold=0.5)

    result = VoiceResult(
        text="hey chatty",
        confidence=0.9,
        duration=0.1,
        timestamp=datetime.now(),
        wake_word_detected=True,
    )

    def fake_process(chunk):
        proc.is_listening = False  # exit loop after one iteration
        return result

    proc._process_audio_chunk = fake_process
    transcriptions = []
    wake_words = []
    proc.on_transcription = transcriptions.append
    proc.on_wake_word = wake_words.append
    proc.is_listening = True

    fake_pyaudio, pa_instance, stream = _install_fake_pyaudio([b"\x00\x00"])
    with mock.patch.dict(sys.modules, {"pyaudio": fake_pyaudio}):
        proc._audio_processing_loop()

    assert transcriptions == [result]
    assert wake_words == ["hey chatty"]
    stream.stop_stream.assert_called_once()
    stream.close.assert_called_once()
    pa_instance.terminate.assert_called_once()


def test_audio_loop_skips_low_confidence_results():
    proc = _bare_processor(confidence_threshold=0.9)
    low = VoiceResult(
        text="meh", confidence=0.1, duration=0.1, timestamp=datetime.now()
    )

    def fake_process(chunk):
        proc.is_listening = False
        return low

    proc._process_audio_chunk = fake_process
    transcriptions = []
    proc.on_transcription = transcriptions.append
    proc.is_listening = True

    fake_pyaudio, _, _ = _install_fake_pyaudio([b"\x00\x00"])
    with mock.patch.dict(sys.modules, {"pyaudio": fake_pyaudio}):
        proc._audio_processing_loop()
    assert transcriptions == []


def test_audio_loop_inner_exception_continues_then_exits():
    proc = _bare_processor()
    calls = {"n": 0}

    def read(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("overflow")
        proc.is_listening = False
        return b"\x00\x00"

    proc._process_audio_chunk = mock.Mock(return_value=None)
    proc.is_listening = True
    fake_pyaudio, _, stream = _install_fake_pyaudio(None, read_side_effect=read)
    with mock.patch.dict(sys.modules, {"pyaudio": fake_pyaudio}):
        proc._audio_processing_loop()
    assert calls["n"] >= 2
    stream.close.assert_called_once()


def test_audio_loop_outer_exception_swallowed():
    proc = _bare_processor()
    proc.is_listening = True
    fake_pyaudio = types.ModuleType("pyaudio")
    fake_pyaudio.paInt16 = 8
    fake_pyaudio.PyAudio = mock.Mock(side_effect=RuntimeError("no audio device"))
    with mock.patch.dict(sys.modules, {"pyaudio": fake_pyaudio}):
        proc._audio_processing_loop()  # should not raise


# ---------------------------------------------------------------------------
# process_audio_file
# ---------------------------------------------------------------------------


def test_process_audio_file_callable_noise_reducer():
    proc = _bare_processor()
    proc.noise_reducer = lambda a: a
    proc.config.noise_reduction_enabled = True
    proc._transcribe_audio = mock.Mock(
        return_value=VoiceResult(
            text="file text", confidence=0.9, duration=0.2, timestamp=datetime.now()
        )
    )
    fake_librosa = types.ModuleType("librosa")
    fake_librosa.load = mock.Mock(
        return_value=(np.zeros(16000, dtype=np.float32), 16000)
    )
    with mock.patch.dict(sys.modules, {"librosa": fake_librosa}):
        result = proc.process_audio_file("/tmp/whatever.wav")
    assert result.text == "file text"
    fake_librosa.load.assert_called_once()


def test_process_audio_file_library_noise_reducer():
    proc = _bare_processor()

    class FakeNR:
        def __init__(self):
            self.called = False

        def reduce_noise(self, y, sr):
            self.called = True
            return y

    nr = FakeNR()
    proc.noise_reducer = nr
    proc.config.noise_reduction_enabled = True
    proc._transcribe_audio = mock.Mock(
        return_value=VoiceResult(
            text="ok", confidence=0.9, duration=0.2, timestamp=datetime.now()
        )
    )
    fake_librosa = types.ModuleType("librosa")
    fake_librosa.load = mock.Mock(
        return_value=(np.zeros(100, dtype=np.float32), 16000)
    )
    with mock.patch.dict(sys.modules, {"librosa": fake_librosa}):
        result = proc.process_audio_file("/tmp/x.wav")
    assert nr.called is True
    assert result.text == "ok"


def test_process_audio_file_error_returns_empty_result():
    proc = _bare_processor()
    fake_librosa = types.ModuleType("librosa")
    fake_librosa.load = mock.Mock(side_effect=FileNotFoundError("missing"))
    with mock.patch.dict(sys.modules, {"librosa": fake_librosa}):
        result = proc.process_audio_file("/does/not/exist.wav")
    assert result.text == ""
    assert result.confidence == 0.0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-v"]))
