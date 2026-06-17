"""Dedicated unit tests for src/chatty_commander/voice/wakeword.py.

Covers WakeWordDetector initialization (including dep fallback to mock mode),
callback management, start/stop listening (mock and real paths), the listen loop
via trigger in mock, notification, and utility methods (get_available_models, is_listening).
Also covers the full MockWakeWordDetector API (used heavily by pipeline and tests).

Uses heavy mocking for optional deps (openwakeword, pyaudio, numpy) so tests run
in any environment (CI without audio hardware or voice group).

Follows AAA style, detailed docstrings, fixtures, and patterns from
tests/unit/test_pipeline.py and EXAMPLE_REFACTORED_TEST.py.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Ensure src is on path for "chatty_commander.*" imports (consistent with other unit tests)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Pre-populate sys.modules with mocks for heavy optional voice deps so the
# module under test can be imported without executing real audio/model code.
_mock_oww = Mock()
_mock_oww.Model = MagicMock
sys.modules.setdefault("openwakeword", _mock_oww)

_mock_pyaudio = Mock()
_mock_pyaudio.PyAudio = MagicMock
_mock_pyaudio.paInt16 = 0
_mock_pyaudio.Stream = MagicMock
sys.modules.setdefault("pyaudio", _mock_pyaudio)

_mock_np = Mock()
_mock_np.frombuffer = lambda *a, **k: MagicMock()
sys.modules.setdefault("numpy", _mock_np)

# Now safe to import the module under test
from chatty_commander.voice.wakeword import (
    VOICE_DEPS_AVAILABLE,
    MockWakeWordDetector,
    WakeWordDetector,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_callback() -> Mock:
    """A simple callback for wake word (wake_word, confidence)."""
    return Mock()


@pytest.fixture
def mock_detector() -> MockWakeWordDetector:
    """A fresh MockWakeWordDetector for tests that need the mock implementation."""
    return MockWakeWordDetector()


@pytest.fixture
def real_detector_mock_deps() -> WakeWordDetector:
    """
    A WakeWordDetector with deps mocked as available.
    We patch at class level so __init__ takes the happy path but we still control
    the model/stream objects.
    """
    with patch("chatty_commander.voice.wakeword.VOICE_DEPS_AVAILABLE", True), \
         patch("chatty_commander.voice.wakeword.openwakeword") as mock_oww, \
         patch("chatty_commander.voice.wakeword.pyaudio") as mock_pa, \
         patch("chatty_commander.voice.wakeword.np"):
        mock_model = MagicMock()
        mock_oww.Model.return_value = mock_model
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_pa.PyAudio.return_value = mock_audio
        mock_audio.open.return_value = mock_stream

        det = WakeWordDetector(wake_words=["hey_test", "alexa"], threshold=0.6)
        # Expose the internal mocks for assertions
        det._model = mock_model
        det._audio = mock_audio
        det._stream = mock_stream
        return det


# ============================================================================
# TESTS
# ============================================================================


class TestWakeWordDetectorInitialization:
    """Tests for WakeWordDetector __init__ and fallback logic."""

    def test_init_raises_when_deps_unavailable(self):
        """
        When VOICE_DEPS_AVAILABLE is False the constructor must raise ImportError
        with installation guidance (critical for clean error in non-voice envs).
        """
        with patch("chatty_commander.voice.wakeword.VOICE_DEPS_AVAILABLE", False):
            with pytest.raises(ImportError) as exc:
                WakeWordDetector()
            assert "uv sync --group voice" in str(exc.value) or "pip install" in str(exc.value)

    def test_init_falls_back_to_mock_mode_on_model_failure(self, mock_callback):
        """
        If openwakeword.Model() fails, detector should set _is_mock and continue
        (so higher layers like VoicePipeline can still use it in degraded mode).
        """
        with patch("chatty_commander.voice.wakeword.VOICE_DEPS_AVAILABLE", True), \
             patch("chatty_commander.voice.wakeword.openwakeword") as mock_oww:
            mock_oww.Model.side_effect = Exception("model load failed")
            det = WakeWordDetector(wake_words=["test"])
            assert getattr(det, "_is_mock", False) is True
            # Still usable
            det.add_callback(mock_callback)
            assert mock_callback in det._callbacks


class TestWakeWordDetectorCallbacks:
    """Callback add/remove/notify behavior."""

    def test_add_and_remove_callback(self, real_detector_mock_deps, mock_callback):
        # Arrange
        det = real_detector_mock_deps

        # Act
        det.add_callback(mock_callback)
        det.remove_callback(mock_callback)

        # Assert
        assert mock_callback not in det._callbacks

    def test_remove_nonexistent_callback_is_safe(self, real_detector_mock_deps, mock_callback):
        det = real_detector_mock_deps
        # Should not raise
        det.remove_callback(mock_callback)

    def test_notify_callbacks_swallows_exceptions(self, real_detector_mock_deps, mock_callback):
        det = real_detector_mock_deps
        bad_cb = Mock(side_effect=RuntimeError("boom"))
        det.add_callback(bad_cb)
        det.add_callback(mock_callback)

        # Should not propagate
        det._notify_callbacks("hey_test", 0.95)
        mock_callback.assert_called_once_with("hey_test", 0.95)


class TestWakeWordDetectorStartStopMock:
    """start/stop/is_listening in mock mode (no real audio)."""

    def test_start_stop_mock_mode(self, mock_detector):
        det = mock_detector
        assert not det.is_listening()

        det.start_listening()
        assert det.is_listening() is True

        det.stop_listening()
        assert det.is_listening() is False

    def test_start_is_idempotent(self, mock_detector):
        det = mock_detector
        det.start_listening()
        det.start_listening()  # should warn but not crash
        assert det.is_listening()


class TestMockWakeWordDetector:
    """Full coverage of the MockWakeWordDetector (the one used by most tests)."""

    def test_mock_init_and_callbacks(self, mock_callback):
        det = MockWakeWordDetector()
        det.add_callback(mock_callback)
        assert mock_callback in det._callbacks
        det.remove_callback(mock_callback)
        assert mock_callback not in det._callbacks

    def test_mock_trigger_calls_callbacks(self, mock_callback):
        det = MockWakeWordDetector()
        det.add_callback(mock_callback)
        det.start_listening()
        det.trigger_wake_word("hey_jarvis", 0.87)
        mock_callback.assert_called_once_with("hey_jarvis", 0.87)

    def test_mock_trigger_ignored_when_not_running(self, mock_callback):
        det = MockWakeWordDetector()
        det.add_callback(mock_callback)
        # not started
        det.trigger_wake_word()
        mock_callback.assert_not_called()

    def test_mock_get_available_models(self):
        det = MockWakeWordDetector()
        models = det.get_available_models()
        assert "hey_jarvis" in models
        assert "alexa" in models

    def test_mock_is_listening(self):
        det = MockWakeWordDetector()
        assert not det.is_listening()
        det.start_listening()
        assert det.is_listening()
        det.stop_listening()
        assert not det.is_listening()


class TestWakeWordDetectorUtilities:
    """get_available_models and is_listening on the real (mocked-dep) detector."""

    def test_get_available_models_returns_model_keys(self, real_detector_mock_deps):
        det = real_detector_mock_deps
        det._model.models = {"hey_test": object(), "alexa": object()}
        assert det.get_available_models() == ["hey_test", "alexa"]

    def test_is_listening_false_when_not_running(self, real_detector_mock_deps):
        det = real_detector_mock_deps
        assert not det.is_listening()

    def test_is_listening_true_only_when_thread_alive(self, real_detector_mock_deps):
        det = real_detector_mock_deps
        det._running = True
        fake_thread = Mock()
        fake_thread.is_alive.return_value = True
        det._thread = fake_thread
        assert det.is_listening() is True

        fake_thread.is_alive.return_value = False
        assert det.is_listening() is False