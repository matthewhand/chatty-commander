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

"""Tests for wakeword module."""

from unittest.mock import MagicMock

import pytest

from src.chatty_commander.voice.wakeword import MockWakeWordDetector


class TestMockWakeWordDetector:
    """Tests for MockWakeWordDetector."""

    def test_initialization(self):
        """Test detector initialization."""
        detector = MockWakeWordDetector()
        assert detector._callbacks == []
        assert detector._running is False

    def test_add_callback(self):
        """Test adding callback."""
        detector = MockWakeWordDetector()
        callback = MagicMock()
        detector.add_callback(callback)
        assert callback in detector._callbacks

    def test_remove_callback(self):
        """Test removing callback."""
        detector = MockWakeWordDetector()
        callback = MagicMock()
        detector.add_callback(callback)
        detector.remove_callback(callback)
        assert callback not in detector._callbacks

    def test_start_listening(self):
        """Test starting listening."""
        detector = MockWakeWordDetector()
        detector.start_listening()
        assert detector._running is True

    def test_stop_listening(self):
        """Test stopping listening."""
        detector = MockWakeWordDetector()
        detector.start_listening()
        detector.stop_listening()
        assert detector._running is False

    def test_is_listening_when_running(self):
        """Test is_listening when running."""
        detector = MockWakeWordDetector()
        detector.start_listening()
        assert detector.is_listening() is True

    def test_is_listening_when_stopped(self):
        """Test is_listening when stopped."""
        detector = MockWakeWordDetector()
        detector.start_listening()
        detector.stop_listening()
        assert detector.is_listening() is False

    def test_is_listening_never_started(self):
        """Test is_listening when never started."""
        detector = MockWakeWordDetector()
        assert detector.is_listening() is False

    def test_trigger_wake_word_when_running(self):
        """Test triggering wake word when running."""
        detector = MockWakeWordDetector()
        callback = MagicMock()
        detector.add_callback(callback)
        detector.start_listening()
        detector.trigger_wake_word("hey_jarvis", 0.95)
        callback.assert_called_once_with("hey_jarvis", 0.95)

    def test_trigger_wake_word_when_not_running(self):
        """Test triggering wake word when not running."""
        detector = MockWakeWordDetector()
        callback = MagicMock()
        detector.add_callback(callback)
        # Don't start listening
        detector.trigger_wake_word("hey_jarvis", 0.95)
        callback.assert_not_called()

    def test_trigger_wake_word_default_values(self):
        """Test triggering wake word with default values."""
        detector = MockWakeWordDetector()
        callback = MagicMock()
        detector.add_callback(callback)
        detector.start_listening()
        detector.trigger_wake_word()
        callback.assert_called_once_with("hey_jarvis", 0.9)

    def test_trigger_wake_word_custom_values(self):
        """Test triggering wake word with custom values."""
        detector = MockWakeWordDetector()
        callback = MagicMock()
        detector.add_callback(callback)
        detector.start_listening()
        detector.trigger_wake_word("alexa", 0.85)
        callback.assert_called_once_with("alexa", 0.85)

    def test_get_available_models(self):
        """Test getting available models."""
        detector = MockWakeWordDetector()
        models = detector.get_available_models()
        assert "hey_jarvis" in models
        assert "alexa" in models
        assert "hey_google" in models

    def test_multiple_callbacks(self):
        """Test multiple callbacks are all called."""
        detector = MockWakeWordDetector()
        callback1 = MagicMock()
        callback2 = MagicMock()
        detector.add_callback(callback1)
        detector.add_callback(callback2)
        detector.start_listening()
        detector.trigger_wake_word()
        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_callback_error_handling(self):
        """Test that one failing callback doesn't stop others."""
        detector = MockWakeWordDetector()
        failing_callback = MagicMock(side_effect=Exception("Test error"))
        good_callback = MagicMock()
        detector.add_callback(failing_callback)
        detector.add_callback(good_callback)
        detector.start_listening()
        # Should not raise
        detector.trigger_wake_word()
        good_callback.assert_called_once()


class TestMockWakeWordDetectorEdgeCases:
    """Edge case tests."""

    def test_remove_nonexistent_callback(self):
        """Test removing callback that was never added."""
        detector = MockWakeWordDetector()
        callback = MagicMock()
        # Should not raise
        detector.remove_callback(callback)

    def test_start_already_running(self):
        """Test starting when already running."""
        detector = MockWakeWordDetector()
        detector.start_listening()
        # Should not raise
        detector.start_listening()
        assert detector._running is True

    def test_trigger_multiple_wake_words(self):
        """Test triggering multiple wake words sequentially."""
        detector = MockWakeWordDetector()
        callback = MagicMock()
        detector.add_callback(callback)
        detector.start_listening()
        detector.trigger_wake_word("hey_jarvis", 0.9)
        detector.trigger_wake_word("alexa", 0.8)
        detector.trigger_wake_word("hey_google", 0.95)
        assert callback.call_count == 3

    def test_zero_confidence(self):
        """Test with zero confidence."""
        detector = MockWakeWordDetector()
        callback = MagicMock()
        detector.add_callback(callback)
        detector.start_listening()
        detector.trigger_wake_word("hey_jarvis", 0.0)
        callback.assert_called_once_with("hey_jarvis", 0.0)
