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
Comprehensive tests for voice/pipeline.py module.

Tests the VoicePipeline class and its voice processing functionality.
"""

from unittest.mock import Mock, patch

import pytest

from chatty_commander.voice.pipeline import VoicePipeline


class TestVoicePipelineInitialization:
    """Test VoicePipeline initialization."""

    def test_init_with_mock_components(self):
        """Test initialization with mock components."""
        pipeline = VoicePipeline(use_mock=True)

        assert pipeline._listening is False
        assert pipeline._processing is False
        assert len(pipeline._callbacks) == 0
        assert pipeline.voice_only is False

    def test_init_with_real_components(self):
        """Test initialization with real components when available."""
        with patch('chatty_commander.voice.pipeline.VOICE_DEPS_AVAILABLE', True):
            with patch('chatty_commander.voice.pipeline.WakeWordDetector') as mock_detector:
                with patch('chatty_commander.voice.pipeline.VoiceTranscriber') as mock_transcriber:
                    with patch('chatty_commander.voice.pipeline.TextToSpeech') as mock_tts:
                        pipeline = VoicePipeline(use_mock=False)

                        assert pipeline.wake_detector is not None
                        assert pipeline.transcriber is not None
                        assert pipeline.tts is not None

    def test_init_with_config_and_executors(self):
        """Test initialization with config manager and command executor."""
        mock_config = Mock()
        mock_executor = Mock()

        pipeline = VoicePipeline(
            config_manager=mock_config,
            command_executor=mock_executor,
            use_mock=True
        )

        assert pipeline.config_manager is mock_config
        assert pipeline.command_executor is mock_executor

    def test_init_wake_word_callback_setup(self):
        """Test that wake word callback is properly set up."""
        with patch('chatty_commander.voice.pipeline.MockWakeWordDetector') as mock_detector:
            mock_detector_instance = Mock()
            mock_detector.return_value = mock_detector_instance

            pipeline = VoicePipeline(use_mock=True)

            # Verify callback was added
            mock_detector_instance.add_callback.assert_called_once()
            callback = mock_detector_instance.add_callback.call_args[0][0]
            assert callable(callback)
            assert callback.__name__ == '_on_wake_word_detected'

    def test_init_with_custom_wake_words(self):
        """Test initialization with custom wake words."""
        custom_wake_words = ["hey_assistant", "ok_computer"]

        with patch('chatty_commander.voice.pipeline.MockWakeWordDetector') as mock_detector:
            mock_detector_instance = Mock()
            mock_detector.return_value = mock_detector_instance

            pipeline = VoicePipeline(wake_words=custom_wake_words, use_mock=True)

            mock_detector.assert_called_once_with(
                wake_words=custom_wake_words,
                use_mock=True
            )


class TestCallbackManagement:
    """Test callback management functionality."""

    def test_add_command_callback(self):
        """Test adding command callbacks."""
        pipeline = VoicePipeline(use_mock=True)

        def mock_callback(command, transcription):
            return f"processed: {command} -> {transcription}"

        pipeline.add_command_callback(mock_callback)

        assert len(pipeline._callbacks) == 1
        assert mock_callback in pipeline._callbacks

    def test_remove_command_callback(self):
        """Test removing command callbacks."""
        pipeline = VoicePipeline(use_mock=True)

        def mock_callback1(command, transcription):
            pass

        def mock_callback2(command, transcription):
            pass

        pipeline.add_command_callback(mock_callback1)
        pipeline.add_command_callback(mock_callback2)

        assert len(pipeline._callbacks) == 2

        pipeline.remove_command_callback(mock_callback1)
        assert len(pipeline._callbacks) == 1
        assert mock_callback2 in pipeline._callbacks
        assert mock_callback1 not in pipeline._callbacks

    def test_remove_nonexistent_callback(self):
        """Test removing a callback that doesn't exist."""
        pipeline = VoicePipeline(use_mock=True)

        def mock_callback(command, transcription):
            pass

        # Should not raise an error
        pipeline.remove_command_callback(mock_callback)
        assert len(pipeline._callbacks) == 0

    def test_notify_callbacks(self):
        """Test notifying all registered callbacks."""
        pipeline = VoicePipeline(use_mock=True)

        callback_results = []

        def callback1(command, transcription):
            callback_results.append(("callback1", command, transcription))

        def callback2(command, transcription):
            callback_results.append(("callback2", command, transcription))

        pipeline.add_command_callback(callback1)
        pipeline.add_command_callback(callback2)

        # Notify callbacks
        pipeline._notify_callbacks("test_command", "test transcription")

        assert len(callback_results) == 2
        assert ("callback1", "test_command", "test transcription") in callback_results
        assert ("callback2", "test_command", "test transcription") in callback_results

    def test_notify_callbacks_with_exception(self):
        """Test that exceptions in callbacks don't break other callbacks."""
        pipeline = VoicePipeline(use_mock=True)

        def failing_callback(command, transcription):
            raise Exception("Test exception")

        def working_callback(command, transcription):
            pass

        pipeline.add_command_callback(failing_callback)
        pipeline.add_command_callback(working_callback)

        # Should not raise an error
        with patch('chatty_commander.voice.pipeline.logger') as mock_logger:
            pipeline._notify_callbacks("test_command", "test transcription")

            # Should log the error
            mock_logger.error.assert_called_once()


class TestPipelineLifecycle:
    """Test pipeline start/stop functionality."""

    def test_start_pipeline(self):
        """Test starting the pipeline."""
        with patch('chatty_commander.voice.pipeline.MockWakeWordDetector') as mock_detector:
            mock_detector_instance = Mock()
            mock_detector.return_value = mock_detector_instance

            pipeline = VoicePipeline(use_mock=True)

            pipeline.start()

            assert pipeline._listening is True
            mock_detector_instance.start_listening.assert_called_once()

    def test_start_already_running(self):
        """Test starting an already running pipeline."""
        with patch('chatty_commander.voice.pipeline.MockWakeWordDetector') as mock_detector:
            mock_detector_instance = Mock()
            mock_detector.return_value = mock_detector_instance

            pipeline = VoicePipeline(use_mock=True)
            pipeline._listening = True

            with patch('chatty_commander.voice.pipeline.logger') as mock_logger:
                pipeline.start()

                mock_logger.warning.assert_called_once_with("Voice pipeline already running")

    def test_stop_pipeline(self):
        """Test stopping the pipeline."""
        with patch('chatty_commander.voice.pipeline.MockWakeWordDetector') as mock_detector:
            mock_detector_instance = Mock()
            mock_detector.return_value = mock_detector_instance

            pipeline = VoicePipeline(use_mock=True)
            pipeline._listening = True

            pipeline.stop()

            assert pipeline._listening is False
            mock_detector_instance.stop_listening.assert_called_once()

    def test_start_with_state_manager(self):
        """Test starting pipeline with state manager."""
        with patch('chatty_commander.voice.pipeline.MockWakeWordDetector') as mock_detector:
            mock_detector_instance = Mock()
            mock_detector.return_value = mock_detector_instance

            mock_state_manager = Mock()
            pipeline = VoicePipeline(state_manager=mock_state_manager, use_mock=True)

            pipeline.start()

            mock_state_manager.change_state.assert_called_once_with("voice_listening")

    def test_stop_with_state_manager(self):
        """Test stopping pipeline with state manager."""
        with patch('chatty_commander.voice.pipeline.MockWakeWordDetector') as mock_detector:
            mock_detector_instance = Mock()
            mock_detector.return_value = mock_detector_instance

            mock_state_manager = Mock()
            pipeline = VoicePipeline(state_manager=mock_state_manager, use_mock=True)
            pipeline._listening = True

            pipeline.stop()

            mock_state_manager.change_state.assert_called_once_with("idle")

    def test_start_failure_handling(self):
        """Test handling of start failures."""
        with patch('chatty_commander.voice.pipeline.MockWakeWordDetector') as mock_detector:
            mock_detector_instance = Mock()
            mock_detector_instance.start_listening.side_effect = Exception("Start failed")
            mock_detector.return_value = mock_detector_instance

            pipeline = VoicePipeline(use_mock=True)

            with pytest.raises(Exception, match="Start failed"):
                pipeline.start()

    def test_stop_failure_handling(self):
        """Test handling of stop failures."""
        with patch('chatty_commander.voice.pipeline.MockWakeWordDetector') as mock_detector:
            mock_detector_instance = Mock()
            mock_detector_instance.stop_listening.side_effect = Exception("Stop failed")
            mock_detector.return_value = mock_detector_instance

            pipeline = VoicePipeline(use_mock=True)
            pipeline._listening = True

            with patch('chatty_commander.voice.pipeline.logger') as mock_logger:
                pipeline.stop()

                mock_logger.error.assert_called_once_with("Error stopping voice pipeline: Stop failed")


class TestWakeWordProcessing:
    """Test wake word detection and processing."""

    def test_on_wake_word_detected(self):
        """Test wake word detection callback."""
        with patch('chatty_commander.voice.pipeline.MockWakeWordDetector') as mock_detector:
            with patch('chatty_commander.voice.pipeline.VoiceTranscriber') as mock_transcriber:
                with patch('chatty_commander.voice.pipeline.TextToSpeech') as mock_tts:
                    mock_detector_instance = Mock()
                    mock_detector.return_value = mock_detector_instance

                    mock_transcriber_instance = Mock()
                    mock_transcriber.return_value = mock_transcriber_instance

                    mock_tts_instance = Mock()
                    mock_tts.return_value = mock_tts_instance

                    pipeline = VoicePipeline(use_mock=True)
                    pipeline._processing = False  # Ensure not already processing

                    # Mock the processing method
                    with patch.object(pipeline, '_process_voice_command') as mock_process:
                        pipeline._on_wake_word_detected("hey_assistant", 0.95)

                        # Verify thread was created
                        assert mock_process.called
                        call_args = mock_process.call_args[0]
                        assert call_args[0] == "hey_assistant"

    def test_on_wake_word_ignored_when_processing(self):
        """Test that wake words are ignored when already processing."""
        pipeline = VoicePipeline(use_mock=True)
        pipeline._processing = True  # Already processing

        with patch.object(pipeline, '_process_voice_command') as mock_process:
            pipeline._on_wake_word_detected("hey_assistant", 0.95)

            # Should not start new processing
            mock_process.assert_not_called()

    def test_process_voice_command_success(self):
        """Test successful voice command processing."""
        with patch('chatty_commander.voice.pipeline.VoiceTranscriber') as mock_transcriber:
            mock_transcriber_instance = Mock()
            mock_transcriber_instance.record_and_transcribe.return_value = "turn on lights"
            mock_transcriber.return_value = mock_transcriber_instance

            mock_config = Mock()
            mock_config.model_actions = {"lights": {"keypress": "ctrl+l"}}
            mock_executor = Mock()
            mock_executor.execute_command.return_value = True

            pipeline = VoicePipeline(
                config_manager=mock_config,
                command_executor=mock_executor,
                use_mock=True
            )

            # Mock state management
            with patch.object(pipeline, 'state_manager') as mock_state_manager:
                with patch('chatty_commander.voice.pipeline.threading') as mock_threading:
                    # Mock callbacks
                    callback_results = []
                    def mock_callback(command, transcription):
                        callback_results.append((command, transcription))

                    pipeline.add_command_callback(mock_callback)

                    # Process command
                    pipeline._process_voice_command("hey_assistant")

                    # Verify interactions
                    mock_transcriber_instance.record_and_transcribe.assert_called_once()
                    mock_executor.execute_command.assert_called_once_with("lights")
                    assert len(callback_results) == 1
                    assert callback_results[0] == ("lights", "turn on lights")

    def test_process_voice_command_no_transcription(self):
        """Test processing when no transcription is received."""
        with patch('chatty_commander.voice.pipeline.VoiceTranscriber') as mock_transcriber:
            mock_transcriber_instance = Mock()
            mock_transcriber_instance.record_and_transcribe.return_value = None
            mock_transcriber.return_value = mock_transcriber_instance

            pipeline = VoicePipeline(use_mock=True)

            with patch.object(pipeline, 'state_manager'):
                pipeline._process_voice_command("hey_assistant")

                # Should not attempt command execution
                mock_transcriber_instance.record_and_transcribe.assert_called_once()

    def test_process_voice_command_no_match(self):
        """Test processing when no command matches."""
        with patch('chatty_commander.voice.pipeline.VoiceTranscriber') as mock_transcriber:
            mock_transcriber_instance = Mock()
            mock_transcriber_instance.record_and_transcribe.return_value = "random text"
            mock_transcriber.return_value = mock_transcriber_instance

            pipeline = VoicePipeline(use_mock=True)

            with patch.object(pipeline, 'state_manager'):
                # Mock callbacks
                callback_results = []
                def mock_callback(command, transcription):
                    callback_results.append((command, transcription))

                pipeline.add_command_callback(mock_callback)

                pipeline._process_voice_command("hey_assistant")

                # Should notify callbacks with empty command
                assert len(callback_results) == 1
                assert callback_results[0] == ("", "random text")

    def test_process_voice_command_execution_failure(self):
        """Test processing when command execution fails."""
        with patch('chatty_commander.voice.pipeline.VoiceTranscriber') as mock_transcriber:
            mock_transcriber_instance = Mock()
            mock_transcriber_instance.record_and_transcribe.return_value = "turn on lights"
            mock_transcriber.return_value = mock_transcriber_instance

            mock_config = Mock()
            mock_config.model_actions = {"lights": {"keypress": "ctrl+l"}}
            mock_executor = Mock()
            mock_executor.execute_command.return_value = False

            pipeline = VoicePipeline(
                config_manager=mock_config,
                command_executor=mock_executor,
                use_mock=True
            )

            with patch.object(pipeline, 'state_manager'):
                # Mock callbacks
                callback_results = []
                def mock_callback(command, transcription):
                    callback_results.append((command, transcription))

                pipeline.add_command_callback(mock_callback)

                pipeline._process_voice_command("hey_assistant")

                # Should still notify callbacks
                assert len(callback_results) == 1
                assert callback_results[0] == ("lights", "turn on lights")


class TestCommandMatching:
    """Test command matching functionality."""

    def test_match_command_direct_name_match(self):
        """Test matching command by direct name."""
        mock_config = Mock()
        mock_config.model_actions = {
            "lights_on": {"keypress": "ctrl+l"},
            "music_play": {"url": "http://music.example.com"},
            "weather": {"url": "http://weather.example.com"}
        }

        pipeline = VoicePipeline(config_manager=mock_config, use_mock=True)

        # Should match direct command name
        assert pipeline._match_command("turn on lights_on") == "lights_on"
        assert pipeline._match_command("play music_play") == "music_play"

    def test_match_command_keyword_match(self):
        """Test matching command by keywords."""
        mock_config = Mock()
        mock_config.model_actions = {
            "lights": {"keypress": "ctrl+l"},
            "music": {"url": "http://music.example.com"},
            "weather": {"url": "http://weather.example.com"}
        }

        pipeline = VoicePipeline(config_manager=mock_config, use_mock=True)

        # Should match by keywords
        assert pipeline._match_command("please turn on the lights") == "lights"
        assert pipeline._match_command("play some music") == "music"
        assert pipeline._match_command("what's the weather like") == "weather"

    def test_match_command_case_insensitive(self):
        """Test that command matching is case insensitive."""
        mock_config = Mock()
        mock_config.model_actions = {"lights": {"keypress": "ctrl+l"}}

        pipeline = VoicePipeline(config_manager=mock_config, use_mock=True)

        assert pipeline._match_command("TURN ON LIGHTS") == "lights"
        assert pipeline._match_command("Lights On") == "lights"

    def test_match_command_no_config(self):
        """Test matching when no config manager is available."""
        pipeline = VoicePipeline(use_mock=True)  # No config_manager

        assert pipeline._match_command("some text") is None

    def test_match_command_no_actions(self):
        """Test matching when no model actions are available."""
        mock_config = Mock()
        mock_config.model_actions = {}

        pipeline = VoicePipeline(config_manager=mock_config, use_mock=True)

        assert pipeline._match_command("some text") is None

    def test_match_command_exception_handling(self):
        """Test handling of exceptions during command matching."""
        mock_config = Mock()
        mock_config.model_actions = {"lights": {"keypress": "ctrl+l"}}
        # Make the config raise an exception
        mock_config.model_actions.__getitem__.side_effect = Exception("Config error")

        pipeline = VoicePipeline(config_manager=mock_config, use_mock=True)

        assert pipeline._match_command("some text") is None


class TestCommandExecution:
    """Test command execution functionality."""

    def test_execute_command_success(self):
        """Test successful command execution."""
        mock_executor = Mock()
        mock_executor.execute_command.return_value = True

        pipeline = VoicePipeline(command_executor=mock_executor, use_mock=True)

        assert pipeline._execute_command("test_command") is True
        mock_executor.execute_command.assert_called_once_with("test_command")

    def test_execute_command_failure(self):
        """Test failed command execution."""
        mock_executor = Mock()
        mock_executor.execute_command.return_value = False

        pipeline = VoicePipeline(command_executor=mock_executor, use_mock=True)

        assert pipeline._execute_command("test_command") is False
        mock_executor.execute_command.assert_called_once_with("test_command")

    def test_execute_command_none_result(self):
        """Test command execution returning None (treated as success)."""
        mock_executor = Mock()
        mock_executor.execute_command.return_value = None

        pipeline = VoicePipeline(command_executor=mock_executor, use_mock=True)

        assert pipeline._execute_command("test_command") is True

    def test_execute_command_no_executor(self):
        """Test execution when no command executor is available."""
        pipeline = VoicePipeline(use_mock=True)  # No command_executor

        assert pipeline._execute_command("test_command") is False

    def test_execute_command_exception_handling(self):
        """Test handling of exceptions during command execution."""
        mock_executor = Mock()
        mock_executor.execute_command.side_effect = Exception("Execution failed")

        pipeline = VoicePipeline(command_executor=mock_executor, use_mock=True)

        assert pipeline._execute_command("test_command") is False


class TestTextCommandProcessing:
    """Test text command processing functionality."""

    def test_process_text_command_success(self):
        """Test successful text command processing."""
        mock_config = Mock()
        mock_config.model_actions = {"lights": {"keypress": "ctrl+l"}}
        mock_executor = Mock()
        mock_executor.execute_command.return_value = True

        pipeline = VoicePipeline(
            config_manager=mock_config,
            command_executor=mock_executor,
            use_mock=True
        )

        result = pipeline.process_text_command("turn on lights")

        assert result == "lights"
        mock_executor.execute_command.assert_called_once_with("lights")

    def test_process_text_command_failure(self):
        """Test failed text command processing."""
        mock_config = Mock()
        mock_config.model_actions = {"lights": {"keypress": "ctrl+l"}}
        mock_executor = Mock()
        mock_executor.execute_command.return_value = False

        pipeline = VoicePipeline(
            config_manager=mock_config,
            command_executor=mock_executor,
            use_mock=True
        )

        result = pipeline.process_text_command("turn on lights")

        assert result == "lights"  # Still returns command name even on failure

    def test_process_text_command_no_match(self):
        """Test text command processing with no match."""
        pipeline = VoicePipeline(use_mock=True)

        result = pipeline.process_text_command("random text")

        assert result is None

    def test_process_text_command_with_tts(self):
        """Test text command processing with TTS feedback."""
        mock_config = Mock()
        mock_config.model_actions = {"lights": {"keypress": "ctrl+l"}}
        mock_executor = Mock()
        mock_executor.execute_command.return_value = True

        mock_tts = Mock()
        mock_tts.is_available.return_value = True

        with patch('chatty_commander.voice.pipeline.TextToSpeech') as mock_tts_class:
            mock_tts_class.return_value = mock_tts

            pipeline = VoicePipeline(
                config_manager=mock_config,
                command_executor=mock_executor,
                voice_only=True,
                use_mock=True
            )

            result = pipeline.process_text_command("turn on lights")

            mock_tts.speak.assert_called_once_with("lights")


class TestStatusAndMonitoring:
    """Test status and monitoring functionality."""

    def test_get_status_basic(self):
        """Test basic status reporting."""
        with patch('chatty_commander.voice.pipeline.VoiceTranscriber') as mock_transcriber:
            mock_transcriber_instance = Mock()
            mock_transcriber_instance.is_available.return_value = True
            mock_transcriber_instance.get_backend_info.return_value = {"backend": "mock"}
            mock_transcriber.return_value = mock_transcriber_instance

            pipeline = VoicePipeline(use_mock=True)

            status = pipeline.get_status()

            assert "listening" in status
            assert "processing" in status
            assert "wake_detector_available" in status
            assert "transcriber_available" in status
            assert "transcriber_info" in status

    def test_get_status_with_wake_detector_info(self):
        """Test status reporting with wake detector information."""
        with patch('chatty_commander.voice.pipeline.MockWakeWordDetector') as mock_detector:
            with patch('chatty_commander.voice.pipeline.VoiceTranscriber') as mock_transcriber:
                mock_detector_instance = Mock()
                mock_detector_instance.get_available_models.return_value = ["hey_jarvis", "ok_computer"]
                mock_detector.return_value = mock_detector_instance

                mock_transcriber_instance = Mock()
                mock_transcriber.return_value = mock_transcriber_instance

                pipeline = VoicePipeline(use_mock=True)

                status = pipeline.get_status()

                assert "available_wake_words" in status
                assert status["available_wake_words"] == ["hey_jarvis", "ok_computer"]

    def test_is_listening(self):
        """Test listening state checking."""
        pipeline = VoicePipeline(use_mock=True)

        # Not listening initially
        assert pipeline.is_listening() is False

        # Listening but not processing
        pipeline._listening = True
        pipeline._processing = False
        assert pipeline.is_listening() is True

        # Listening but processing
        pipeline._listening = True
        pipeline._processing = True
        assert pipeline.is_listening() is False

        # Not listening but processing
        pipeline._listening = False
        pipeline._processing = True
        assert pipeline.is_listening() is False


class TestMockWakeWordTrigger:
    """Test mock wake word triggering functionality."""

    def test_trigger_mock_wake_word(self):
        """Test triggering mock wake word."""
        with patch('chatty_commander.voice.pipeline.MockWakeWordDetector') as mock_detector:
            mock_detector_instance = Mock()
            mock_detector.return_value = mock_detector_instance

            pipeline = VoicePipeline(use_mock=True)

            pipeline.trigger_mock_wake_word("test_wake_word")

            mock_detector_instance.trigger_wake_word.assert_called_once_with("test_wake_word")

    def test_trigger_mock_wake_word_unavailable(self):
        """Test triggering mock wake word when not available."""
        with patch('chatty_commander.voice.pipeline.MockWakeWordDetector') as mock_detector:
            mock_detector_instance = Mock()
            # Remove the trigger method
            del mock_detector_instance.trigger_wake_word
            mock_detector.return_value = mock_detector_instance

            pipeline = VoicePipeline(use_mock=True)

            with patch('chatty_commander.voice.pipeline.logger') as mock_logger:
                pipeline.trigger_mock_wake_word("test_wake_word")

                mock_logger.warning.assert_called_once_with("Mock wake word trigger not available")

    def test_trigger_mock_wake_word_default_value(self):
        """Test triggering mock wake word with default value."""
        with patch('chatty_commander.voice.pipeline.MockWakeWordDetector') as mock_detector:
            mock_detector_instance = Mock()
            mock_detector.return_value = mock_detector_instance

            pipeline = VoicePipeline(use_mock=True)

            pipeline.trigger_mock_wake_word()  # No argument

            mock_detector_instance.trigger_wake_word.assert_called_once_with("hey_jarvis")


class TestIntegrationScenarios:
    """Integration tests for complex scenarios."""

    def test_full_voice_processing_pipeline(self):
        """Test a complete voice processing pipeline scenario."""
        mock_config = Mock()
        mock_config.model_actions = {"lights": {"keypress": "ctrl+l"}}
        mock_executor = Mock()
        mock_executor.execute_command.return_value = True

        with patch('chatty_commander.voice.pipeline.VoiceTranscriber') as mock_transcriber:
            mock_transcriber_instance = Mock()
            mock_transcriber_instance.record_and_transcribe.return_value = "turn on lights"
            mock_transcriber.return_value = mock_transcriber_instance

            with patch('chatty_commander.voice.pipeline.TextToSpeech') as mock_tts:
                mock_tts_instance = Mock()
                mock_tts_instance.is_available.return_value = True
                mock_tts.return_value = mock_tts_instance

                pipeline = VoicePipeline(
                    config_manager=mock_config,
                    command_executor=mock_executor,
                    voice_only=True,
                    use_mock=True
                )

                # Test text command processing (simulates voice pipeline)
                result = pipeline.process_text_command("turn on lights")

                assert result == "lights"
                mock_executor.execute_command.assert_called_once_with("lights")
                mock_tts_instance.speak.assert_called_once_with("lights")

    def test_concurrent_wake_word_handling(self):
        """Test handling of concurrent wake word detections."""
        pipeline = VoicePipeline(use_mock=True)
        pipeline._processing = True  # Already processing

        # Multiple wake word detections should be ignored
        pipeline._on_wake_word_detected("wake1", 0.9)
        pipeline._on_wake_word_detected("wake2", 0.95)
        pipeline._on_wake_word_detected("wake3", 0.8)

        # No processing should occur due to already processing flag
        assert pipeline._processing is True

    def test_callback_exception_isolation(self):
        """Test that exceptions in one callback don't affect others."""
        pipeline = VoicePipeline(use_mock=True)

        def failing_callback(command, transcription):
            raise Exception("Callback failed")

        def working_callback(command, transcription):
            pass

        def another_working_callback(command, transcription):
            pass

        pipeline.add_command_callback(failing_callback)
        pipeline.add_command_callback(working_callback)
        pipeline.add_command_callback(another_working_callback)

        # Should not raise an exception
        with patch('chatty_commander.voice.pipeline.logger') as mock_logger:
            pipeline._notify_callbacks("test_command", "test transcription")

            # Should log the error
            mock_logger.error.assert_called_once_with("Error in voice command callback: Callback failed")

    def test_state_transitions_during_processing(self):
        """Test state transitions during voice processing."""
        mock_state_manager = Mock()

        with patch('chatty_commander.voice.pipeline.VoiceTranscriber') as mock_transcriber:
            mock_transcriber_instance = Mock()
            mock_transcriber_instance.record_and_transcribe.return_value = "test"
            mock_transcriber.return_value = mock_transcriber_instance

            pipeline = VoicePipeline(state_manager=mock_state_manager, use_mock=True)

            # Process command
            pipeline._process_voice_command("hey_assistant")

            # Verify state transitions
            expected_calls = [
                mock.call.change_state("voice_recording"),
                mock.call.change_state("voice_processing"),
                mock.call.change_state("voice_listening")
            ]

            mock_state_manager.change_state.assert_has_calls(expected_calls)

    def test_error_recovery(self):
        """Test that the pipeline recovers from errors."""
        with patch('chatty_commander.voice.pipeline.VoiceTranscriber') as mock_transcriber:
            mock_transcriber_instance = Mock()
            mock_transcriber_instance.record_and_transcribe.side_effect = Exception("Transcription failed")
            mock_transcriber.return_value = mock_transcriber_instance

            pipeline = VoicePipeline(use_mock=True)

            # Should not raise an exception and should reset processing flag
            initial_processing = pipeline._processing

            with patch.object(pipeline, 'state_manager'):
                pipeline._process_voice_command("hey_assistant")

            # Processing should be reset even after error
            assert pipeline._processing is False
            assert pipeline._processing != initial_processing
