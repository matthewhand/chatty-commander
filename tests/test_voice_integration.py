"""Tests for voice integration components."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from chatty_commander.voice import VoicePipeline, VoiceTranscriber, WakeWordDetector
from chatty_commander.voice.transcription import MockTranscriptionBackend
from chatty_commander.voice.wakeword import MockWakeWordDetector


class TestMockWakeWordDetector:
    def test_mock_detector_initialization(self):
        detector = MockWakeWordDetector()
        assert not detector.is_listening()
        assert detector.get_available_models() == ["hey_jarvis", "alexa", "hey_google"]

    def test_mock_detector_callbacks(self):
        detector = MockWakeWordDetector()
        callback_called = []

        def test_callback(wake_word, confidence):
            callback_called.append((wake_word, confidence))

        detector.add_callback(test_callback)
        detector.start_listening()
        detector.trigger_wake_word("hey_jarvis", 0.9)

        assert len(callback_called) == 1
        assert callback_called[0] == ("hey_jarvis", 0.9)

    def test_mock_detector_start_stop(self):
        detector = MockWakeWordDetector()
        assert not detector.is_listening()

        detector.start_listening()
        assert detector.is_listening()

        detector.stop_listening()
        assert not detector.is_listening()


class TestMockTranscriptionBackend:
    def test_mock_backend_transcription(self):
        backend = MockTranscriptionBackend()
        assert backend.is_available()

        # Test cycling through responses
        result1 = backend.transcribe(b"dummy_audio")
        result2 = backend.transcribe(b"dummy_audio")

        assert result1 == "hello world"
        assert result2 == "turn on the lights"

    def test_mock_backend_custom_responses(self):
        responses = ["test response 1", "test response 2"]
        backend = MockTranscriptionBackend(responses=responses)

        result1 = backend.transcribe(b"dummy_audio")
        result2 = backend.transcribe(b"dummy_audio")
        result3 = backend.transcribe(b"dummy_audio")  # Should cycle back

        assert result1 == "test response 1"
        assert result2 == "test response 2"
        assert result3 == "test response 1"


class TestVoiceTranscriber:
    def test_transcriber_with_mock_backend(self):
        transcriber = VoiceTranscriber(backend="mock")
        assert transcriber.is_available()

        result = transcriber.transcribe_audio_data(b"dummy_audio")
        assert result == "hello world"

    def test_transcriber_backend_info(self):
        transcriber = VoiceTranscriber(backend="mock")
        info = transcriber.get_backend_info()

        assert "backend_type" in info
        assert "is_available" in info
        assert info["is_available"] is True
        assert info["sample_rate"] == 16000


class TestVoicePipeline:
    def setup_method(self):
        # Create mock managers
        self.mock_config = Mock()
        self.mock_config.model_actions = {
            "hello": {"keypress": {"keys": "ctrl+h"}},
            "lights": {"url": {"url": "http://example.com/lights"}},
        }

        self.mock_executor = Mock()
        self.mock_executor.execute_command.return_value = True

        self.mock_state = Mock()

    def test_pipeline_initialization(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            state_manager=self.mock_state,
            use_mock=True,
        )

        assert not pipeline.is_listening()
        status = pipeline.get_status()
        assert "listening" in status
        assert "transcriber_available" in status

    def test_pipeline_start_stop(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config, command_executor=self.mock_executor, use_mock=True
        )

        pipeline.start()
        assert pipeline.is_listening()

        pipeline.stop()
        assert not pipeline.is_listening()

    def test_command_matching(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config, command_executor=self.mock_executor, use_mock=True
        )

        # Test direct name match
        command = pipeline._match_command("hello there")
        assert command == "hello"

        # Test keyword match
        command = pipeline._match_command("turn on the lights please")
        assert command == "lights"

        # Test no match
        command = pipeline._match_command("unknown command")
        assert command is None

    def test_text_command_processing(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config, command_executor=self.mock_executor, use_mock=True
        )

        result = pipeline.process_text_command("hello world")
        assert result == "hello"
        self.mock_executor.execute_command.assert_called_with("hello")

    def test_command_callbacks(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config, command_executor=self.mock_executor, use_mock=True
        )

        callback_calls = []

        def test_callback(command_name, transcription):
            callback_calls.append((command_name, transcription))

        pipeline.add_command_callback(test_callback)
        pipeline.process_text_command("hello there")

        assert len(callback_calls) == 1
        assert callback_calls[0] == ("hello", "hello there")

    def test_mock_wake_word_trigger(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config, command_executor=self.mock_executor, use_mock=True
        )

        # Should not raise an error
        pipeline.trigger_mock_wake_word("hey_jarvis")

    def test_voice_only_invokes_tts(self):
        pipeline = VoicePipeline(
            config_manager=self.mock_config,
            command_executor=self.mock_executor,
            use_mock=True,
            tts_backend="mock",
            voice_only=True,
        )

        pipeline.process_text_command("hello there")
        assert pipeline.tts.backend.spoken[0] == "hello"

    def test_pipeline_without_managers(self):
        # Test pipeline works without config/executor managers
        pipeline = VoicePipeline(use_mock=True)

        pipeline.start()
        assert pipeline.is_listening()

        # Should not crash when processing commands without managers
        result = pipeline.process_text_command("hello")
        assert result is None

        pipeline.stop()


class TestVoiceIntegrationE2E:
    def test_end_to_end_mock_flow(self):
        """Test complete voice flow using mock components."""
        # Setup
        config = Mock()
        config.model_actions = {"hello": {"keypress": {"keys": "ctrl+h"}}}

        executor = Mock()
        executor.execute_command.return_value = True

        state_manager = Mock()

        # Create pipeline
        pipeline = VoicePipeline(
            config_manager=config,
            command_executor=executor,
            state_manager=state_manager,
            use_mock=True,
        )

        # Track callbacks
        commands_processed = []

        def command_callback(command_name, transcription):
            commands_processed.append((command_name, transcription))

        pipeline.add_command_callback(command_callback)

        # Start pipeline
        pipeline.start()
        assert pipeline.is_listening()

        # Process a command
        result = pipeline.process_text_command("hello world")
        assert result == "hello"

        # Verify execution
        executor.execute_command.assert_called_with("hello")
        assert len(commands_processed) == 1
        assert commands_processed[0] == ("hello", "hello world")

        # Stop pipeline
        pipeline.stop()
        assert not pipeline.is_listening()

    def test_voice_pipeline_status_reporting(self):
        """Test status reporting functionality."""
        pipeline = VoicePipeline(use_mock=True)

        status = pipeline.get_status()

        # Check required status fields
        required_fields = [
            "listening",
            "processing",
            "wake_detector_available",
            "transcriber_available",
            "transcriber_info",
            "available_wake_words",
        ]

        for field in required_fields:
            assert field in status

        assert isinstance(status["transcriber_info"], dict)
        assert isinstance(status["available_wake_words"], list)
