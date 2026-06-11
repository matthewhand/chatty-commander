# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction.

"""Coverage tests for ``chatty_commander.voice.wakeword``.

The runtime voice dependencies (``openwakeword``, ``pyaudio``, ``numpy``) are
not installed in the CI/test environment, so these tests patch the import
boundary -- the module-level globals ``VOICE_DEPS_AVAILABLE``, ``openwakeword``,
``pyaudio`` and ``np`` -- with fakes. This lets us exercise the real detector
code paths (model init, listen loop, scoring, lifecycle) without any audio
hardware or real ONNX models.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest

from chatty_commander.voice import wakeword
from chatty_commander.voice.wakeword import MockWakeWordDetector, WakeWordDetector

# ---------------------------------------------------------------------------
# Fakes for the import-guarded dependencies
# ---------------------------------------------------------------------------


class _FakeModel:
    """Stand-in for ``openwakeword.Model``."""

    def __init__(self, *args, **kwargs):
        self.models = {"hey_jarvis": object(), "alexa": object()}
        self.predictions = {}

    def predict(self, audio_array):
        return self.predictions


class _FakeOpenWakeWord:
    Model = _FakeModel


class _FakeNumpy:
    int16 = "int16"

    @staticmethod
    def frombuffer(data, dtype=None):
        # Return a recognizable sentinel; the fake model ignores it.
        return list(data) if data else []


@contextmanager
def patched_deps(
    monkeypatch,
    *,
    available: bool = True,
    oww=None,
    pyaudio_mod=None,
    numpy_mod=None,
):
    """Patch the import-guarded module globals so real branches run."""
    monkeypatch.setattr(wakeword, "VOICE_DEPS_AVAILABLE", available)
    monkeypatch.setattr(
        wakeword, "openwakeword", oww if oww is not None else _FakeOpenWakeWord
    )
    monkeypatch.setattr(
        wakeword,
        "pyaudio",
        pyaudio_mod if pyaudio_mod is not None else MagicMock(),
    )
    monkeypatch.setattr(
        wakeword, "np", numpy_mod if numpy_mod is not None else _FakeNumpy
    )
    yield


# ---------------------------------------------------------------------------
# Dependency-unavailable branch
# ---------------------------------------------------------------------------


def test_init_raises_when_deps_unavailable(monkeypatch):
    monkeypatch.setattr(wakeword, "VOICE_DEPS_AVAILABLE", False)
    with pytest.raises(ImportError) as exc:
        WakeWordDetector()
    assert "Voice dependencies not available" in str(exc.value)


# ---------------------------------------------------------------------------
# Init / defaults
# ---------------------------------------------------------------------------


def test_init_defaults(monkeypatch):
    with patched_deps(monkeypatch):
        det = WakeWordDetector()
    assert det.wake_words == ["hey_jarvis", "alexa"]
    assert det.threshold == 0.5
    assert det.chunk_size == 1280
    assert det.sample_rate == 16000
    assert det.channels == 1
    assert isinstance(det._model, _FakeModel)
    assert det._running is False
    assert det._callbacks == []


def test_init_custom_args(monkeypatch):
    with patched_deps(monkeypatch):
        det = WakeWordDetector(
            wake_words=["computer"],
            threshold=0.8,
            chunk_size=640,
            sample_rate=8000,
            channels=2,
        )
    assert det.wake_words == ["computer"]
    assert det.threshold == 0.8
    assert det.chunk_size == 640
    assert det.sample_rate == 8000
    assert det.channels == 2


def test_init_model_failure_falls_back_to_mock(monkeypatch):
    """If model construction raises, detector flips to mock mode."""

    class BoomOWW:
        class Model:
            def __init__(self, *a, **k):
                raise RuntimeError("no onnx for you")

    with patched_deps(monkeypatch, oww=BoomOWW):
        det = WakeWordDetector()
    assert det._model is None
    assert det._is_mock is True


# ---------------------------------------------------------------------------
# Callback management
# ---------------------------------------------------------------------------


def test_add_and_remove_callback(monkeypatch):
    with patched_deps(monkeypatch):
        det = WakeWordDetector()

    def cb(word, conf):
        pass

    det.add_callback(cb)
    assert cb in det._callbacks
    det.remove_callback(cb)
    assert cb not in det._callbacks
    # Removing again is a no-op (does not raise)
    det.remove_callback(cb)


def test_notify_callbacks_invokes_all(monkeypatch):
    with patched_deps(monkeypatch):
        det = WakeWordDetector()
    received = []
    det.add_callback(lambda w, c: received.append((w, c)))
    det.add_callback(lambda w, c: received.append(("second", c)))
    det._notify_callbacks("alexa", 0.77)
    assert ("alexa", 0.77) in received
    assert ("second", 0.77) in received


def test_notify_callbacks_swallows_exceptions(monkeypatch):
    with patched_deps(monkeypatch):
        det = WakeWordDetector()
    good = []

    def boom(w, c):
        raise ValueError("boom")

    det.add_callback(boom)
    det.add_callback(lambda w, c: good.append((w, c)))
    # Should not propagate the exception from the first callback.
    det._notify_callbacks("hey_jarvis", 0.9)
    assert good == [("hey_jarvis", 0.9)]


# ---------------------------------------------------------------------------
# Mock-mode lifecycle (model failed to load)
# ---------------------------------------------------------------------------


def _mock_mode_detector(monkeypatch):
    class BoomOWW:
        class Model:
            def __init__(self, *a, **k):
                raise RuntimeError("boom")

    with patched_deps(monkeypatch, oww=BoomOWW):
        return WakeWordDetector()


def test_mock_mode_start_listening(monkeypatch):
    det = _mock_mode_detector(monkeypatch)
    det.start_listening()
    assert det._running is True
    # No thread is started in mock mode.
    assert det._thread is None


def test_mock_mode_get_available_models(monkeypatch):
    det = _mock_mode_detector(monkeypatch)
    assert det.get_available_models() == ["hey_jarvis", "alexa", "hey_google"]


def test_start_listening_noop_when_already_running(monkeypatch):
    det = _mock_mode_detector(monkeypatch)
    det._running = True
    det.start_listening()  # Early return; should remain running.
    assert det._running is True
    assert det._thread is None


# ---------------------------------------------------------------------------
# Real-detector lifecycle with a fake PyAudio stream
# ---------------------------------------------------------------------------


def _real_detector_with_stream(monkeypatch, predictions=None):
    fake_stream = MagicMock()
    fake_stream.read.return_value = b"\x00\x01" * 10
    fake_audio = MagicMock()
    fake_audio.open.return_value = fake_stream

    fake_pyaudio = MagicMock()
    fake_pyaudio.PyAudio.return_value = fake_audio
    fake_pyaudio.paInt16 = 8

    with patched_deps(monkeypatch, pyaudio_mod=fake_pyaudio):
        det = WakeWordDetector(wake_words=["hey_jarvis"], threshold=0.5)
    if predictions is not None:
        det._model.predictions = predictions
    return det, fake_audio, fake_stream


def test_start_and_stop_listening_lifecycle(monkeypatch):
    det, fake_audio, fake_stream = _real_detector_with_stream(monkeypatch)
    det.start_listening()
    assert det._running is True
    assert det._thread is not None
    # is_listening reflects the live thread.
    assert det.is_listening() is True
    fake_audio.open.assert_called_once()

    det.stop_listening()
    assert det._running is False
    fake_stream.stop_stream.assert_called_once()
    fake_stream.close.assert_called_once()
    fake_audio.terminate.assert_called_once()
    assert det._stream is None
    assert det._audio is None
    assert det.is_listening() is False


def test_start_listening_failure_calls_stop_and_raises(monkeypatch):
    fake_audio = MagicMock()
    fake_audio.open.side_effect = OSError("device busy")
    fake_pyaudio = MagicMock()
    fake_pyaudio.PyAudio.return_value = fake_audio
    fake_pyaudio.paInt16 = 8

    with patched_deps(monkeypatch, pyaudio_mod=fake_pyaudio):
        det = WakeWordDetector()
    with pytest.raises(OSError):
        det.start_listening()
    # stop_listening was invoked during cleanup.
    assert det._running is False
    assert det._audio is None


def test_stop_listening_handles_stream_close_errors(monkeypatch):
    det, _, fake_stream = _real_detector_with_stream(monkeypatch)
    det._stream = fake_stream
    det._audio = MagicMock()
    fake_stream.stop_stream.side_effect = RuntimeError("close fail")
    det._audio.terminate.side_effect = RuntimeError("term fail")
    # Errors are swallowed; resources still cleared.
    det.stop_listening()
    assert det._stream is None
    assert det._audio is None


# ---------------------------------------------------------------------------
# Detection / scoring path (_listen_loop body via direct stepping)
# ---------------------------------------------------------------------------


def _run_one_loop_iteration(det, fake_stream):
    """Run a single iteration of the listen loop body, then stop.

    The real ``start_listening`` is what assigns ``_stream``; we drive the
    loop directly, so wire the fake stream in by hand and have the model's
    ``predict`` flip ``_running`` off so the ``while`` loop exits after one
    pass (the model is the last call in the loop body).
    """
    det._stream = fake_stream
    preds = det._model.predictions

    def stop_after(*_a, **_k):
        det._running = False
        return preds

    # Patch the model predict to also stop the loop after one call.
    det._model.predict = stop_after
    det._running = True
    det._listen_loop()


def test_listen_loop_detects_above_threshold(monkeypatch):
    det, _, stream = _real_detector_with_stream(
        monkeypatch, predictions={"hey_jarvis": 0.9}
    )
    hits = []
    det.add_callback(lambda w, c: hits.append((w, c)))
    _run_one_loop_iteration(det, stream)
    assert hits == [("hey_jarvis", 0.9)]


def test_listen_loop_ignores_below_threshold(monkeypatch):
    det, _, stream = _real_detector_with_stream(
        monkeypatch, predictions={"hey_jarvis": 0.2}
    )
    hits = []
    det.add_callback(lambda w, c: hits.append((w, c)))
    _run_one_loop_iteration(det, stream)
    assert hits == []


def test_listen_loop_at_exact_threshold_detects(monkeypatch):
    # confidence >= threshold, boundary inclusive.
    det, _, stream = _real_detector_with_stream(
        monkeypatch, predictions={"hey_jarvis": 0.5}
    )
    hits = []
    det.add_callback(lambda w, c: hits.append((w, c)))
    _run_one_loop_iteration(det, stream)
    assert hits == [("hey_jarvis", 0.5)]


def test_listen_loop_ignores_unconfigured_wake_word(monkeypatch):
    # Model reports a word the detector is not configured to listen for.
    det, _, stream = _real_detector_with_stream(
        monkeypatch, predictions={"alexa": 0.99}
    )
    hits = []
    det.add_callback(lambda w, c: hits.append((w, c)))
    _run_one_loop_iteration(det, stream)
    assert hits == []


def test_listen_loop_handles_read_exception(monkeypatch):
    det, _, fake_stream = _real_detector_with_stream(monkeypatch)
    det._stream = fake_stream
    # First read raises; loop logs, sleeps briefly, then we stop it.
    calls = {"n": 0}

    def read_raises(*_a, **_k):
        calls["n"] += 1
        # Stay running so the loop's ``if self._running`` error branch
        # (log + brief sleep) executes; the patched sleep below stops us.
        raise OSError("overflow")

    fake_stream.read = read_raises

    sleeps = {"n": 0}

    def fake_sleep(_secs):
        # Loop hit the error path and is pausing before retry; stop it now.
        sleeps["n"] += 1
        det._running = False

    monkeypatch.setattr(wakeword.time, "sleep", fake_sleep)
    det._running = True
    det._listen_loop()  # Should not raise.
    assert calls["n"] == 1
    assert sleeps["n"] == 1  # the error-branch sleep ran


def test_listen_loop_read_exception_while_stopped_is_silent(monkeypatch):
    """If a read fails after we've already stopped, no retry-sleep happens."""
    det, _, fake_stream = _real_detector_with_stream(monkeypatch)
    det._stream = fake_stream

    def read_then_stop(*_a, **_k):
        det._running = False  # simulate stop racing with the read
        raise OSError("overflow")

    fake_stream.read = read_then_stop
    slept = {"n": 0}
    monkeypatch.setattr(
        wakeword.time, "sleep", lambda *_: slept.__setitem__("n", slept["n"] + 1)
    )
    det._running = True
    det._listen_loop()
    # _running was False inside the except, so the error branch is skipped.
    assert slept["n"] == 0


def test_listen_loop_mock_mode_sleeps_and_continues(monkeypatch):
    det = _mock_mode_detector(monkeypatch)
    sleeps = {"n": 0}

    def fake_sleep(_secs):
        sleeps["n"] += 1
        det._running = False  # break out after first sleep

    monkeypatch.setattr(wakeword.time, "sleep", fake_sleep)
    det._running = True
    det._listen_loop()
    assert sleeps["n"] == 1


# ---------------------------------------------------------------------------
# get_available_models / is_listening on real detector
# ---------------------------------------------------------------------------


def test_get_available_models_from_model(monkeypatch):
    det, _, _ = _real_detector_with_stream(monkeypatch)
    models = det.get_available_models()
    assert set(models) == {"hey_jarvis", "alexa"}


def test_get_available_models_no_model_returns_empty(monkeypatch):
    det, _, _ = _real_detector_with_stream(monkeypatch)
    det._model = None
    assert det.get_available_models() == []


def test_get_available_models_handles_error(monkeypatch):
    det, _, _ = _real_detector_with_stream(monkeypatch)

    class BadModel:
        @property
        def models(self):
            raise RuntimeError("kaboom")

    det._model = BadModel()
    assert det.get_available_models() == []


def test_is_listening_false_without_thread(monkeypatch):
    det, _, _ = _real_detector_with_stream(monkeypatch)
    assert det.is_listening() is False
    det._running = True
    # Still no live thread.
    assert det.is_listening() is False


# ---------------------------------------------------------------------------
# MockWakeWordDetector
# ---------------------------------------------------------------------------


def test_mock_detector_full_flow():
    det = MockWakeWordDetector("ignored", foo="bar")
    assert det.is_listening() is False
    assert det.get_available_models() == ["hey_jarvis", "alexa", "hey_google"]

    hits = []
    cb = lambda w, c: hits.append((w, c))  # noqa: E731
    det.add_callback(cb)

    # Triggering before start does nothing.
    det.trigger_wake_word()
    assert hits == []

    det.start_listening()
    assert det.is_listening() is True
    det.trigger_wake_word("alexa", 0.42)
    assert hits == [("alexa", 0.42)]

    det.remove_callback(cb)
    assert cb not in det._callbacks
    det.remove_callback(cb)  # no-op

    det.stop_listening()
    assert det.is_listening() is False


def test_mock_detector_trigger_default_args():
    det = MockWakeWordDetector()
    hits = []
    det.add_callback(lambda w, c: hits.append((w, c)))
    det.start_listening()
    det.trigger_wake_word()
    assert hits == [("hey_jarvis", 0.9)]


def test_mock_detector_trigger_swallows_callback_errors():
    det = MockWakeWordDetector()

    def boom(w, c):
        raise ValueError("boom")

    det.add_callback(boom)
    det.start_listening()
    # Should not raise even though the callback throws.
    det.trigger_wake_word()


# ---------------------------------------------------------------------------
# Threaded integration: start, detect via real loop, stop
# ---------------------------------------------------------------------------


def test_threaded_detection_end_to_end(monkeypatch):
    det, _, fake_stream = _real_detector_with_stream(
        monkeypatch, predictions={"hey_jarvis": 0.95}
    )
    event = threading.Event()
    det.add_callback(lambda w, c: event.set())
    # Keep numpy.frombuffer cheap; default fake handles it.
    det.start_listening()
    try:
        assert event.wait(timeout=2.0), "callback was not invoked"
    finally:
        det.stop_listening()
    assert det._running is False
