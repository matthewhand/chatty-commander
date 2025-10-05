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

"""Tests for AI intelligence core module."""

from dataclasses import asdict
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.ai.intelligence_core import (
    AIResponse,
    IntelligenceCore,
)
from src.chatty_commander.app.config import Config


class TestAIResponse:
    """Test AIResponse dataclass."""

    def test_ai_response_creation(self):
        """Test creating an AIResponse instance."""
        timestamp = datetime.now()
        response = AIResponse(
            text="Hello world",
            confidence=0.95,
            intent="greeting",
            actions=[{"type": "speak", "text": "Hello"}],
            metadata={"model": "gpt-4"},
            timestamp=timestamp,
        )

        assert response.text == "Hello world"
        assert response.confidence == 0.95
        assert response.intent == "greeting"
        assert len(response.actions) == 1
        assert response.actions[0]["type"] == "speak"
        assert response.metadata["model"] == "gpt-4"
        assert response.timestamp == timestamp

    def test_ai_response_as_dict(self):
        """Test converting AIResponse to dictionary."""
        timestamp = datetime.now()
        response = AIResponse(
            text="Test",
            confidence=0.8,
            intent="test",
            actions=[],
            metadata={},
            timestamp=timestamp,
        )

        response_dict = asdict(response)
        assert isinstance(response_dict, dict)
        assert response_dict["text"] == "Test"
        assert response_dict["confidence"] == 0.8


class TestIntelligenceCore:
    """Test IntelligenceCore functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        config = Mock(spec=Config)
        config.voice = Mock()
        config.voice.sample_rate = 16000
        config.voice.noise_reduction = True
        return config

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_init_success(
        self, mock_state_manager, mock_voice_processor, mock_advisors, mock_config
    ):
        """Test successful initialization of IntelligenceCore."""
        mock_voice_proc = Mock()
        mock_voice_processor.return_value = mock_voice_proc

        core = IntelligenceCore(mock_config)

        assert core.config == mock_config
        assert core.advisors_service is not None
        assert core.voice_processor == mock_voice_proc
        assert core.state_manager is not None
        assert core.current_conversation_context == {}
        assert core.active_persona == "chatty"
        assert core.listening_mode == "continuous"
        assert core.on_response is None
        assert core.on_mode_change is None
        assert core.on_error is None

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_init_voice_processor_failure(
        self, mock_state_manager, mock_voice_processor, mock_advisors, mock_config
    ):
        """Test initialization when voice processor creation fails."""
        mock_voice_processor.side_effect = Exception("Voice processor failed")

        core = IntelligenceCore(mock_config)

        assert core.voice_processor is None

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_voice_processor_callbacks_setup(
        self, mock_state_manager, mock_voice_processor, mock_advisors, mock_config
    ):
        """Test that voice processor callbacks are properly set up."""
        mock_voice_proc = Mock()
        mock_voice_processor.return_value = mock_voice_proc

        core = IntelligenceCore(mock_config)

        # Verify callbacks were assigned
        assert mock_voice_proc.on_transcription == core._handle_voice_input
        assert mock_voice_proc.on_wake_word == core._handle_wake_word
        assert mock_voice_proc.on_speech_start == core._handle_speech_start
        assert mock_voice_proc.on_speech_end == core._handle_speech_end

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_handle_voice_input_low_confidence(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test handling voice input with low confidence."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            # Mock VoiceResult with low confidence
            voice_result = Mock()
            voice_result.confidence = 0.3
            voice_result.text = "unclear speech"

            # Should not process low confidence input
            with patch.object(core, "process_input") as mock_process:
                core._handle_voice_input(voice_result)
                mock_process.assert_not_called()

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_handle_voice_input_high_confidence(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test handling voice input with high confidence."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            # Mock VoiceResult with high confidence
            voice_result = Mock()
            voice_result.confidence = 0.8
            voice_result.text = "clear speech"
            voice_result.duration = 2.5
            voice_result.language = "en"
            voice_result.wake_word_detected = False

            mock_response = Mock(spec=AIResponse)

            with patch.object(
                core, "process_input", return_value=mock_response
            ) as mock_process:
                core._handle_voice_input(voice_result)

                mock_process.assert_called_once_with(
                    text="clear speech",
                    input_type="voice",
                    metadata={
                        "confidence": 0.8,
                        "duration": 2.5,
                        "language": "en",
                        "wake_word_detected": False,
                    },
                )

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_handle_voice_input_with_callback(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test handling voice input with response callback."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            # Set up callback
            callback = Mock()
            core.on_response = callback

            voice_result = Mock()
            voice_result.confidence = 0.8
            voice_result.text = "test input"
            voice_result.duration = 1.0
            voice_result.language = "en"
            voice_result.wake_word_detected = False

            mock_response = Mock(spec=AIResponse)

            with patch.object(core, "process_input", return_value=mock_response):
                core._handle_voice_input(voice_result)

                callback.assert_called_once_with(mock_response)

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_handle_voice_input_with_error(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test handling voice input when processing fails."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            # Set up error callback
            error_callback = Mock()
            core.on_error = error_callback

            voice_result = Mock()
            voice_result.confidence = 0.8
            voice_result.text = "test input"

            with patch.object(
                core, "process_input", side_effect=Exception("Processing failed")
            ):
                core._handle_voice_input(voice_result)

                error_callback.assert_called_once_with(
                    "Voice processing error: Processing failed"
                )

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_handle_wake_word_chatty(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test handling 'chatty' wake word."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            # Mock state manager
            mock_state_manager_instance = mock_state_manager.return_value
            mock_state_manager_instance.current_state = "computer"
            core.state_manager = mock_state_manager_instance

            # Set up mode change callback
            mode_callback = Mock()
            core.on_mode_change = mode_callback

            core._handle_wake_word("hey chatty")

            mock_state_manager_instance.change_state.assert_called_once_with("chatty")
            mode_callback.assert_called_once_with("chatty")

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_handle_wake_word_computer(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test handling 'computer' wake word."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            # Mock state manager
            mock_state_manager_instance = mock_state_manager.return_value
            mock_state_manager_instance.current_state = "chatty"
            core.state_manager = mock_state_manager_instance

            core._handle_wake_word("computer")

            mock_state_manager_instance.change_state.assert_called_once_with("computer")

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_handle_wake_word_same_mode(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test handling wake word when already in target mode."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            # Mock state manager
            mock_state_manager_instance = mock_state_manager.return_value
            mock_state_manager_instance.current_state = "chatty"
            core.state_manager = mock_state_manager_instance

            core._handle_wake_word("chatty")

            # Should not change state if already in target mode
            mock_state_manager_instance.change_state.assert_not_called()

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_handle_wake_word_state_change_error(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test handling wake word when state change fails."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            # Mock state manager
            mock_state_manager_instance = mock_state_manager.return_value
            mock_state_manager_instance.current_state = "computer"
            mock_state_manager_instance.change_state.side_effect = Exception(
                "State change failed"
            )
            core.state_manager = mock_state_manager_instance

            # Should not raise exception
            core._handle_wake_word("chatty")

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_handle_speech_start(self, mock_state_manager, mock_advisors, mock_config):
        """Test handling speech start event."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            # Should not raise exception
            core._handle_speech_start()

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_handle_speech_end(self, mock_state_manager, mock_advisors, mock_config):
        """Test handling speech end event."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            # Should not raise exception
            core._handle_speech_end()

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_process_input_text(self, mock_state_manager, mock_advisors, mock_config):
        """Test processing text input."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            # Mock advisors service
            mock_advisors_instance = mock_advisors.return_value
            mock_reply = Mock()
            mock_reply.reply = "Hello there!"
            mock_reply.persona_id = "chatty"
            mock_reply.model = "gpt-4"
            mock_reply.api_mode = "chat"
            mock_reply.context_key = "main"
            mock_advisors_instance.handle_message.return_value = mock_reply
            core.advisors_service = mock_advisors_instance

            with patch.object(
                core, "_extract_actions", return_value=[]
            ) as mock_extract:
                with patch.object(
                    core, "_analyze_intent", return_value="greeting"
                ) as mock_analyze:
                    with patch.object(core, "_execute_actions") as mock_execute:
                        response = core.process_input("Hello", "text")

                        assert isinstance(response, AIResponse)
                        assert response.text == "Hello there!"
                        assert response.confidence == 1.0
                        assert response.intent == "greeting"
                        assert response.actions == []
                        assert response.metadata["persona_id"] == "chatty"
                        assert response.metadata["input_type"] == "text"

                        mock_extract.assert_called_once_with("Hello there!")
                        mock_analyze.assert_called_once_with("Hello")
                        mock_execute.assert_called_once_with([])

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_process_input_voice_with_metadata(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test processing voice input with metadata."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            # Mock advisors service
            mock_advisors_instance = mock_advisors.return_value
            mock_reply = Mock()
            mock_reply.reply = "Voice response"
            mock_reply.persona_id = "computer"
            mock_reply.model = "gpt-3.5"
            mock_reply.api_mode = "completion"
            mock_reply.context_key = "voice"
            mock_advisors_instance.handle_message.return_value = mock_reply
            core.advisors_service = mock_advisors_instance

            metadata = {"confidence": 0.9, "language": "en"}

            with patch.object(
                core, "_extract_actions", return_value=[{"type": "speak"}]
            ):
                with patch.object(core, "_analyze_intent", return_value="command"):
                    with patch.object(core, "_execute_actions"):
                        response = core.process_input("Test voice", "voice", metadata)

                        assert response.confidence == 0.9
                        assert response.metadata["language"] == "en"
                        assert response.metadata["input_type"] == "voice"

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_process_input_error_handling(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test processing input when an error occurs."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            # Mock advisors service to raise exception
            mock_advisors_instance = mock_advisors.return_value
            mock_advisors_instance.handle_message.side_effect = Exception(
                "Service error"
            )
            core.advisors_service = mock_advisors_instance

            response = core.process_input("Test input")

            assert isinstance(response, AIResponse)
            assert "error processing your request" in response.text.lower()
            assert response.confidence == 0.0
            assert response.intent == "error"
            assert response.actions == []
            assert response.metadata["error"] == "Service error"

    def test_extract_actions_placeholder(self, mock_config):
        """Test _extract_actions method (placeholder implementation)."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            with patch("src.chatty_commander.ai.intelligence_core.AdvisorsService"):
                with patch("src.chatty_commander.ai.intelligence_core.StateManager"):
                    core = IntelligenceCore(mock_config)

                    # This method should exist but may be a placeholder
                    try:
                        actions = core._extract_actions("Some response text")
                        assert isinstance(actions, list)
                    except AttributeError:
                        # Method might not be implemented yet
                        pass

    def test_analyze_intent_placeholder(self, mock_config):
        """Test _analyze_intent method (placeholder implementation)."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            with patch("src.chatty_commander.ai.intelligence_core.AdvisorsService"):
                with patch("src.chatty_commander.ai.intelligence_core.StateManager"):
                    core = IntelligenceCore(mock_config)

                    # This method should exist but may be a placeholder
                    try:
                        intent = core._analyze_intent("Hello world")
                        assert isinstance(intent, str)
                    except AttributeError:
                        # Method might not be implemented yet
                        pass

    def test_execute_actions_placeholder(self, mock_config):
        """Test _execute_actions method (placeholder implementation)."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            with patch("src.chatty_commander.ai.intelligence_core.AdvisorsService"):
                with patch("src.chatty_commander.ai.intelligence_core.StateManager"):
                    core = IntelligenceCore(mock_config)

                    # This method should exist but may be a placeholder
                    try:
                        core._execute_actions([{"type": "test"}])
                        # Should not raise exception
                    except AttributeError:
                        # Method might not be implemented yet
                        pass

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_analyze_intent_comprehensive(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test comprehensive intent analysis scenarios."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            # Test mode switch intent
            intent = core._analyze_intent("switch to chatty mode")
            assert intent == "mode_switch"

            # Test screenshot intent
            intent = core._analyze_intent("take a screenshot")
            assert intent == "screenshot"

            # Test lights intents
            intent = core._analyze_intent("turn on the lights")
            assert intent == "lights_on"

            intent = core._analyze_intent("lights off")
            assert intent == "lights_off"

            # Test question intent
            intent = core._analyze_intent("What is the weather like?")
            assert intent == "question"

            # Test greeting intent
            intent = core._analyze_intent("Hello there")
            assert intent == "greeting"

            # Test task request intent
            intent = core._analyze_intent("Help me with something")
            assert intent == "task_request"

            # Test default conversation intent
            intent = core._analyze_intent("Just talking about stuff")
            assert intent == "conversation"

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_extract_actions_comprehensive(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test comprehensive action extraction scenarios."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            # Test mode switch action extraction
            response = "I will SWITCH_MODE:chatty for you"
            actions = core._extract_actions(response)
            assert len(actions) == 1
            assert actions[0]["type"] == "mode_switch"
            assert actions[0]["target_mode"] == "chatty"
            assert actions[0]["priority"] == "high"

            # Test mode switched confirmation
            response = "✓ Switched to computer mode"
            actions = core._extract_actions(response)
            assert len(actions) == 1
            assert actions[0]["type"] == "mode_switched"
            assert actions[0]["priority"] == "info"

            # Test screenshot action
            response = "I will take a screenshot now"
            actions = core._extract_actions(response)
            assert len(actions) == 1
            assert actions[0]["type"] == "screenshot"
            assert actions[0]["priority"] == "medium"

            # Test lights actions
            response = "Turning lights on"
            actions = core._extract_actions(response)
            assert len(actions) == 1
            assert actions[0]["type"] == "lights_on"

            response = "Lights will go off"
            actions = core._extract_actions(response)
            assert len(actions) == 1
            assert actions[0]["type"] == "lights_off"

            # Test no actions
            response = "Just a regular response"
            actions = core._extract_actions(response)
            assert len(actions) == 0

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_execute_actions_comprehensive(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test comprehensive action execution scenarios."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            # Mock state manager
            mock_state_manager_instance = mock_state_manager.return_value
            core.state_manager = mock_state_manager_instance

            # Set up callbacks
            mode_callback = Mock()
            core.on_mode_change = mode_callback

            # Test mode switch action
            actions = [{"type": "mode_switch", "target_mode": "computer"}]
            core._execute_actions(actions)

            mock_state_manager_instance.change_state.assert_called_once_with("computer")
            mode_callback.assert_called_once_with("computer")

            # Reset mocks
            mock_state_manager_instance.reset_mock()
            mode_callback.reset_mock()

            # Test screenshot action (should just log)
            actions = [{"type": "screenshot"}]
            core._execute_actions(actions)
            # Should not raise exception

            # Test lights actions (should just log)
            actions = [{"type": "lights_on"}, {"type": "lights_off"}]
            core._execute_actions(actions)
            # Should not raise exception

            # Test action execution error
            actions = [{"type": "mode_switch", "target_mode": "invalid"}]
            mock_state_manager_instance.change_state.side_effect = Exception(
                "Invalid mode"
            )

            # Should not raise exception
            core._execute_actions(actions)

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_voice_listening_controls(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test voice listening start/stop functionality."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ) as mock_voice_proc:
            mock_voice_instance = Mock()
            mock_voice_proc.return_value = mock_voice_instance

            core = IntelligenceCore(mock_config)

            # Test start listening
            core.start_voice_listening()
            mock_voice_instance.start_listening.assert_called_once()
            assert core.listening_mode == "continuous"

            # Test stop listening
            core.stop_voice_listening()
            mock_voice_instance.stop_listening.assert_called_once()
            assert core.listening_mode == "off"

            # Test when voice processor is None
            core.voice_processor = None
            core.start_voice_listening()  # Should not raise exception
            core.stop_voice_listening()  # Should not raise exception

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_process_text_input(self, mock_state_manager, mock_advisors, mock_config):
        """Test process_text_input convenience method."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            mock_response = Mock(spec=AIResponse)

            with patch.object(
                core, "process_input", return_value=mock_response
            ) as mock_process:
                result = core.process_text_input("Hello world")

                mock_process.assert_called_once_with("Hello world", input_type="text")
                assert result == mock_response

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_process_voice_file_success(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test successful voice file processing."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ) as mock_voice_proc:
            mock_voice_instance = Mock()
            mock_voice_proc.return_value = mock_voice_instance

            core = IntelligenceCore(mock_config)

            # Mock voice result
            mock_voice_result = Mock()
            mock_voice_result.text = "Transcribed speech"
            mock_voice_result.confidence = 0.85
            mock_voice_result.duration = 3.2
            mock_voice_instance.process_audio_file.return_value = mock_voice_result

            mock_response = Mock(spec=AIResponse)

            with patch.object(
                core, "process_input", return_value=mock_response
            ) as mock_process:
                result = core.process_voice_file("/path/to/audio.wav")

                mock_voice_instance.process_audio_file.assert_called_once_with(
                    "/path/to/audio.wav"
                )
                mock_process.assert_called_once_with(
                    text="Transcribed speech",
                    input_type="voice_file",
                    metadata={
                        "confidence": 0.85,
                        "duration": 3.2,
                        "file_path": "/path/to/audio.wav",
                    },
                )
                assert result == mock_response

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_process_voice_file_no_processor(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test voice file processing when no voice processor available."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)
            core.voice_processor = None

            result = core.process_voice_file("/path/to/audio.wav")

            assert result.text == "Voice processing not available"
            assert result.confidence == 0.0
            assert result.intent == "error"
            assert result.actions == []
            assert "No voice processor" in result.metadata["error"]

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_process_voice_file_error(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test voice file processing when an error occurs."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ) as mock_voice_proc:
            mock_voice_instance = Mock()
            mock_voice_proc.return_value = mock_voice_instance

            core = IntelligenceCore(mock_config)

            mock_voice_instance.process_audio_file.side_effect = Exception(
                "Audio file error"
            )

            result = core.process_voice_file("/path/to/audio.wav")

            assert result.text == "Error processing voice file: Audio file error"
            assert result.confidence == 0.0
            assert result.intent == "error"
            assert result.actions == []
            assert result.metadata["error"] == "Audio file error"

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_set_persona(self, mock_state_manager, mock_advisors, mock_config):
        """Test changing the active persona."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            core.set_persona("computer")
            assert core.active_persona == "computer"

            core.set_persona("assistant")
            assert core.active_persona == "assistant"

    @patch("src.chatty_commander.ai.intelligence_core.AdvisorsService")
    @patch("src.chatty_commander.ai.intelligence_core.StateManager")
    def test_get_conversation_stats(
        self, mock_state_manager, mock_advisors, mock_config
    ):
        """Test getting conversation statistics."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ):
            core = IntelligenceCore(mock_config)

            # Mock dependencies
            mock_state_manager_instance = mock_state_manager.return_value
            mock_state_manager_instance.current_state = "chatty"
            mock_advisors_instance = mock_advisors.return_value
            mock_advisors_instance.enabled = True

            core.state_manager = mock_state_manager_instance
            core.advisors_service = mock_advisors_instance
            core.active_persona = "computer"
            core.listening_mode = "continuous"
            core.voice_processor = Mock()

            stats = core.get_conversation_stats()

            assert stats["active_persona"] == "computer"
            assert stats["current_mode"] == "chatty"
            assert stats["listening_mode"] == "continuous"
            assert stats["voice_available"] is True
            assert stats["advisors_enabled"] is True
