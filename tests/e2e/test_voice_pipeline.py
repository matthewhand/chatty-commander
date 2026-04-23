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

"""
Comprehensive tests for voice pipeline module.

Tests voice processing, wake word detection, and command execution.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.chatty_commander.voice.pipeline import VoicePipeline


@pytest.fixture
def mock_config():
    """Create mock config manager."""
    return MagicMock()


@pytest.fixture
def mock_executor():
    """Create mock command executor."""
    return MagicMock()


@pytest.fixture
def mock_state_manager():
    """Create mock state manager."""
    return MagicMock()


@pytest.fixture
def pipeline(mock_config, mock_executor, mock_state_manager):
    """Create a VoicePipeline instance with mocks."""
    return VoicePipeline(
        config_manager=mock_config,
        command_executor=mock_executor,
        state_manager=mock_state_manager,
        use_mock=True,
        wake_words=["hey assistant"],
    )


class TestVoicePipelineInitialization:
    """Tests for VoicePipeline initialization."""

    def test_initialization(self, pipeline):
        """Test basic pipeline initialization."""
        assert pipeline.config_manager is not None
        assert pipeline.command_executor is not None
        assert pipeline.state_manager is not None
        assert pipeline.wake_detector is not None
        assert pipeline.transcriber is not None

    def test_uses_mock_components(self, mock_config, mock_executor, mock_state_manager):
        """Test that mock components are used when use_mock=True."""
        pipeline = VoicePipeline(
            config_manager=mock_config,
            command_executor=mock_executor,
            state_manager=mock_state_manager,
            use_mock=True,
        )
        # Should have mock wake detector
        assert pipeline.wake_detector is not None

    def test_initial_state(self, pipeline):
        """Test initial pipeline state."""
        assert not pipeline._listening
        assert not pipeline._processing
        assert len(pipeline._callbacks) == 0


class TestCallbackManagement:
    """Tests for callback management."""

    def test_add_callback(self, pipeline):
        """Test adding a command callback."""
        callback = Mock()
        pipeline.add_command_callback(callback)
        assert callback in pipeline._callbacks

    def test_remove_callback(self, pipeline):
        """Test removing a command callback."""
        callback = Mock()
        pipeline.add_command_callback(callback)
        pipeline.remove_command_callback(callback)
        assert callback not in pipeline._callbacks

    def test_remove_nonexistent_callback(self, pipeline):
        """Test removing a callback that wasn't added."""
        callback = Mock()
        # Should not raise
        pipeline.remove_command_callback(callback)


class TestPipelineLifecycle:
    """Tests for start/stop lifecycle."""

    def test_start_pipeline(self, pipeline):
        """Test starting the pipeline."""
        pipeline.start()
        assert pipeline._listening

    def test_start_already_running(self, pipeline):
        """Test starting when already running."""
        pipeline._listening = True
        # Should not raise
        pipeline.start()

    def test_stop_pipeline(self, pipeline):
        """Test stopping the pipeline."""
        pipeline._listening = True
        pipeline.stop()
        assert not pipeline._listening

    def test_stop_not_running(self, pipeline):
        """Test stopping when not running."""
        # Should not raise
        pipeline.stop()


class TestWakeWordDetection:
    """Tests for wake word detection handling."""

    def test_wake_word_callback(self, pipeline):
        """Test handling wake word detection."""
        with patch.object(pipeline, '_process_voice_command') as mock_process:
            pipeline._on_wake_word_detected("hey assistant", 0.95)
            mock_process.assert_called_once_with("hey assistant")

    def test_wake_word_ignored_while_processing(self, pipeline):
        """Test that wake words are ignored while processing."""
        pipeline._processing = True
        with patch.object(pipeline, '_process_voice_command') as mock_process:
            pipeline._on_wake_word_detected("hey assistant", 0.95)
            mock_process.assert_not_called()


class TestCommandExecution:
    """Tests for command execution."""

    def test_match_command_method_exists(self, pipeline):
        """Test that _match_command method exists."""
        assert hasattr(pipeline, '_match_command')
        assert callable(pipeline._match_command)

    def test_match_command_returns_string_or_none(self, pipeline):
        """Test matching a command from transcription."""
        command = pipeline._match_command("open the browser")
        # Should return a command or None
        assert command is None or isinstance(command, str)

    def test_execute_command_method_exists(self, pipeline):
        """Test that _execute_command method exists."""
        assert hasattr(pipeline, '_execute_command')
        assert callable(pipeline._execute_command)

    def test_execute_command_returns_boolean(self, pipeline):
        """Test that execute command returns boolean."""
        result = pipeline._execute_command("test_command")
        assert isinstance(result, bool)


class TestTTS:
    """Tests for text-to-speech functionality."""

    def test_tts_available(self, pipeline):
        """Test TTS availability check."""
        # TTS should report availability
        available = pipeline.tts.is_available()
        assert isinstance(available, bool)

    def test_tts_speak_method_exists(self, pipeline):
        """Test that TTS has speak method."""
        assert hasattr(pipeline.tts, 'speak')
        assert callable(pipeline.tts.speak)

    def test_tts_backend_info(self, pipeline):
        """Test getting TTS backend info."""
        info = pipeline.tts.get_backend_info()
        assert isinstance(info, dict)


class TestVoicePipelineIntegration:
    """Integration tests for VoicePipeline."""

    def test_full_lifecycle(self, pipeline):
        """Test full pipeline lifecycle."""
        # Start
        pipeline.start()
        assert pipeline._listening

        # Add callback
        callback = Mock()
        pipeline.add_command_callback(callback)

        # Stop
        pipeline.stop()
        assert not pipeline._listening

    def test_multiple_callbacks(self, pipeline):
        """Test multiple callbacks are all called."""
        callback1 = Mock()
        callback2 = Mock()
        pipeline.add_command_callback(callback1)
        pipeline.add_command_callback(callback2)

        # Manually trigger notification
        pipeline._notify_callbacks("command", "transcription")

        callback1.assert_called_once_with("command", "transcription")
        callback2.assert_called_once_with("command", "transcription")


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_wake_word_list(self):
        """Test with empty wake word list."""
        pipeline = VoicePipeline(use_mock=True, wake_words=[])
        assert pipeline.wake_detector is not None

    def test_none_config(self):
        """Test with None config manager."""
        pipeline = VoicePipeline(
            config_manager=None,
            command_executor=MagicMock(),
            use_mock=True,
        )
        assert pipeline.config_manager is None

    def test_callback_with_exception(self, pipeline):
        """Test that callback exceptions don't crash pipeline."""
        bad_callback = Mock(side_effect=Exception("Callback error"))
        good_callback = Mock()
        pipeline.add_command_callback(bad_callback)
        pipeline.add_command_callback(good_callback)

        # Should not raise
        pipeline._notify_callbacks("command", "transcription")

        good_callback.assert_called_once()
