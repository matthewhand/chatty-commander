"""
Tests for wakeword module to improve coverage.
Focuses on MockWakeWordDetector and basic functionality.
"""

import sys
import types
from unittest.mock import MagicMock, patch

import pytest


def _build_voice_stubs() -> dict[str, types.ModuleType]:
    """Return fake ``openwakeword``/``pyaudio`` modules for stubbing.

    NOTE: do NOT mock numpy here. numpy is installed, and replacing it with an
    empty module at import time leaked globally (never restored), breaking
    pytest.approx's numpy detection in any later test under random ordering.
    """
    ow = types.ModuleType("openwakeword")
    ow_model = types.ModuleType("openwakeword.model")
    ow_model.Model = MagicMock()
    return {
        "openwakeword": ow,
        "openwakeword.model": ow_model,
        "pyaudio": types.ModuleType("pyaudio"),
    }


# Install the stubs just long enough to import the module under test, then
# remove them so they never leak into later-collected tests. The autouse
# fixture below re-installs them per-test via monkeypatch.setitem (auto-cleaned)
# for any test that touches sys.modules at runtime.
_stub_modules = _build_voice_stubs()
_added_stub_keys: list[str] = []
for _name, _mod in _stub_modules.items():
    if _name not in sys.modules:
        sys.modules[_name] = _mod
        _added_stub_keys.append(_name)

# Force-enable voice deps for this module's tests WITHOUT importlib.reload.
# reload() re-executes the module and creates new class objects, which desyncs
# already-imported consumers (e.g. voice.pipeline holds the pre-reload
# MockWakeWordDetector), breaking isinstance checks under full-suite ordering.
# Mutating attributes in place keeps class identity stable.
import numpy as _np_real  # noqa: E402

import chatty_commander.voice.wakeword as _ww  # noqa: E402

_ww.VOICE_DEPS_AVAILABLE = True
if _ww.openwakeword is None:
    _ww.openwakeword = _stub_modules["openwakeword"]
if _ww.pyaudio is None:
    _ww.pyaudio = _stub_modules["pyaudio"]
if _ww.np is None:
    _ww.np = _np_real

for _name in _added_stub_keys:
    sys.modules.pop(_name, None)


@pytest.fixture(autouse=True)
def _stub_voice_modules(monkeypatch):
    """Provide fake ``openwakeword``/``pyaudio`` modules during each test,
    auto-cleaned by ``monkeypatch.setitem`` so they never leak into
    later-collected tests."""
    for name, mod in _build_voice_stubs().items():
        monkeypatch.setitem(sys.modules, name, mod)
    yield


from chatty_commander.voice.wakeword import (  # noqa: E402 - imported after sys.modules patching
    VOICE_DEPS_AVAILABLE,
    MockWakeWordDetector,
    WakeWordDetector,
    logger,
)


class TestVoiceDependencies:
    """Test voice dependency detection."""

    def test_voice_deps_available(self):
        """Test that voice dependencies are detected as available."""
        assert VOICE_DEPS_AVAILABLE is True


class TestMockWakeWordDetector:
    """Test the MockWakeWordDetector class - this is the working implementation."""

    def test_init(self):
        """Test MockWakeWordDetector initialization."""
        detector = MockWakeWordDetector()
        assert detector._callbacks == []
        assert detector._running is False

    def test_add_remove_callback(self):
        """Test adding and removing callbacks."""
        detector = MockWakeWordDetector()
        callback = MagicMock()

        detector.add_callback(callback)
        assert callback in detector._callbacks

        detector.remove_callback(callback)
        assert callback not in detector._callbacks

    def test_start_stop_listening(self):
        """Test starting and stopping listening."""
        detector = MockWakeWordDetector()

        detector.start_listening()
        assert detector._running is True

        detector.stop_listening()
        assert detector._running is False

    def test_trigger_wake_word(self):
        """Test manually triggering wake word detection."""
        detector = MockWakeWordDetector()
        callback = MagicMock()

        detector.add_callback(callback)
        detector.start_listening()

        detector.trigger_wake_word("hey_jarvis", 0.9)

        callback.assert_called_once_with("hey_jarvis", 0.9)

    def test_trigger_wake_word_not_running(self):
        """Test triggering wake word when not running."""
        detector = MockWakeWordDetector()
        callback = MagicMock()

        detector.add_callback(callback)
        # Don't start listening

        detector.trigger_wake_word("hey_jarvis", 0.9)

        callback.assert_not_called()

    def test_get_available_models(self):
        """Test getting available models from mock detector."""
        detector = MockWakeWordDetector()
        models = detector.get_available_models()
        assert models == ["hey_jarvis", "alexa", "hey_google"]

    def test_is_listening(self):
        """Test checking if mock detector is listening."""
        detector = MockWakeWordDetector()

        assert detector.is_listening() is False

        detector.start_listening()
        assert detector.is_listening() is True

        detector.stop_listening()
        assert detector.is_listening() is False


class TestWakeWordDetectorBasic:
    """Test basic WakeWordDetector functionality without complex mocking."""

    def test_init_no_voice_deps(self):
        """Test initialization fails when voice dependencies not available."""
        with patch("chatty_commander.voice.wakeword.VOICE_DEPS_AVAILABLE", False):
            with pytest.raises(ImportError, match="Voice dependencies not available"):
                WakeWordDetector()




class TestLogger:
    """Test logger configuration."""

    def test_logger_exists(self):
        """Test that logger is properly configured."""
        import logging

        assert isinstance(logger, logging.Logger)
        assert logger.name == "chatty_commander.voice.wakeword"


if __name__ == "__main__":
    pytest.main([__file__])
