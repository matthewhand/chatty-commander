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

"""Exhaustive test coverage for IntelligenceCore AI component.

This module provides comprehensive test coverage for all IntelligenceCore functionality
including initialization, input processing, intent analysis, action extraction,
voice handling, error scenarios, and edge cases.
"""

import logging
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.ai.intelligence_core import (
    AIResponse,
    IntelligenceCore,
    create_intelligence_core,
)
from src.chatty_commander.config import Config
from src.chatty_commander.models import StateManager


class TestAIResponse:
    """Comprehensive tests for AIResponse data class."""

    def test_basic_initialization(self):
        """Test basic AIResponse initialization."""
        response = AIResponse(
            text="Hello world",
            confidence=0.95,
            intent="greeting",
            actions=[],
            metadata={"test": "data"},
            timestamp=datetime.now(),
        )

        assert response.text == "Hello world"
        assert response.confidence == 0.95
        assert response.intent == "greeting"
        assert response.actions == []
        assert response.metadata["test"] == "data"
        assert isinstance(response.timestamp, datetime)

    def test_default_values(self):
        """Test AIResponse default values."""
        response = AIResponse(text="Test")

        assert response.text == "Test"
        assert response.confidence == 0.0
        assert response.intent == "unknown"
        assert response.actions == []
        assert response.metadata == {}
        assert isinstance(response.timestamp, datetime)

    def test_to_dict_conversion(self):
        """Test AIResponse to_dict method."""
        timestamp = datetime.now()
        response = AIResponse(
            text="Test response",
            confidence=0.8,
            intent="test",
            actions=[{"type": "test"}],
            metadata={"key": "value"},
            timestamp=timestamp,
        )

        result = response.to_dict()

        assert result["text"] == "Test response"
        assert result["confidence"] == 0.8
        assert result["intent"] == "test"
        assert result["actions"] == [{"type": "test"}]
        assert result["metadata"]["key"] == "value"
        assert result["timestamp"] == timestamp.isoformat()

    def test_from_dict_conversion(self):
        """Test AIResponse from_dict method."""
        timestamp = datetime.now()
        data = {
            "text": "Test response",
            "confidence": 0.8,
            "intent": "test",
            "actions": [{"type": "test"}],
            "metadata": {"key": "value"},
            "timestamp": timestamp.isoformat(),
        }

        response = AIResponse.from_dict(data)

        assert response.text == "Test response"
        assert response.confidence == 0.8
        assert response.intent == "test"
        assert response.actions == [{"type": "test"}]
        assert response.metadata["key"] == "value"
        assert response.timestamp == timestamp


class TestIntelligenceCoreInitialization:
    """Comprehensive tests for IntelligenceCore initialization."""

    def test_successful_initialization(self, mock_config, mock_state_manager):
        """Test successful IntelligenceCore initialization."""
        core = IntelligenceCore(mock_config)

        assert core.config == mock_config
        assert core.state_manager == mock_state_manager
        assert core.active_persona == "default"
        assert core.listening_mode == "off"
        assert core.voice_processor is None
        assert core.conversation_engine is None
        assert core.advisors_service is None
        assert core.on_mode_change is None

    def test_initialization_with_voice_processor(
        self, mock_config, mock_voice_processor
    ):
        """Test initialization with voice processor."""
        mock_config.voice_enabled = True

        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ) as mock_create_voice:
            mock_create_voice.return_value = mock_voice_processor
            core = IntelligenceCore(mock_config)

            assert core.voice_processor == mock_voice_processor
            mock_create_voice.assert_called_once_with(mock_config.voice_config)

    def test_initialization_with_conversation_engine(self, mock_config):
        """Test initialization with conversation engine."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_conversation_engine"
        ) as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine

            core = IntelligenceCore(mock_config)

            assert core.conversation_engine == mock_engine
            mock_create_engine.assert_called_once_with(mock_config.ai_config)

    def test_initialization_with_advisors_service(
        self, mock_config, mock_advisors_service
    ):
        """Test initialization with advisors service."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.AdvisorsService"
        ) as mock_advisors_class:
            mock_advisors_class.return_value = mock_advisors_service

            core = IntelligenceCore(mock_config)

            assert core.advisors_service == mock_advisors_service
            mock_advisors_class.assert_called_once_with(mock_config)

    def test_initialization_with_llm_service(self, mock_config, mock_llm_service):
        """Test initialization with LLM service."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.LLMService"
        ) as mock_llm_class:
            mock_llm_class.return_value = mock_llm_service

            core = IntelligenceCore(mock_config)

            assert core.llm_service == mock_llm_service
            mock_llm_class.assert_called_once_with(mock_config)

    def test_initialization_failure_handling(self, mock_config):
        """Test initialization failure handling."""
        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ) as mock_create_voice:
            mock_create_voice.side_effect = Exception("Voice processor error")

            # Should not raise exception, should handle gracefully
            core = IntelligenceCore(mock_config)

            assert core.voice_processor is None  # Should be None on failure


class TestIntelligenceCoreInputProcessing:
    """Comprehensive tests for input processing methods."""

    def test_process_text_input_success(self, mock_core_with_services):
        """Test successful text input processing."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        expected_response = AIResponse(
            text="Test response",
            confidence=0.9,
            intent="test",
            actions=[],
            metadata={},
            timestamp=datetime.now(),
        )

        mock_llm.generate_response.return_value = expected_response

        result = core.process_text_input("Hello AI")

        assert result.text == "Test response"
        assert result.confidence == 0.9
        mock_llm.generate_response.assert_called_once()

    def test_process_input_with_different_input_types(self, mock_core_with_services):
        """Test input processing with different input types."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        test_cases = [
            ("text", "Hello"),
            ("voice", "Hello via voice"),
            ("voice_file", "Hello via file"),
            ("command", "Hello via command"),
        ]

        for input_type, text in test_cases:
            mock_llm.generate_response.reset_mock()
            expected_response = AIResponse(text=f"Response to {input_type}")
            mock_llm.generate_response.return_value = expected_response

            result = core.process_input(text, input_type=input_type)

            assert result.text == f"Response to {input_type}"
            # Verify metadata includes input_type
            call_args = mock_llm.generate_response.call_args
            assert call_args[1]["metadata"]["input_type"] == input_type

    def test_process_input_with_metadata(self, mock_core_with_services):
        """Test input processing with additional metadata."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        extra_metadata = {"confidence": 0.85, "duration": 2.5}
        expected_response = AIResponse(text="Response with metadata")
        mock_llm.generate_response.return_value = expected_response

        result = core.process_input("Test", metadata=extra_metadata)

        # Verify metadata was merged
        call_args = mock_llm.generate_response.call_args
        assert call_args[1]["metadata"]["confidence"] == 0.85
        assert call_args[1]["metadata"]["duration"] == 2.5

    def test_process_input_with_conversation_engine(self, mock_core_with_services):
        """Test input processing with conversation engine integration."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        # Mock conversation engine methods
        mock_engine.analyze_intent.return_value = "test_intent"
        mock_engine.analyze_sentiment.return_value = "positive"
        mock_engine.build_enhanced_prompt.return_value = "Enhanced prompt"

        expected_response = AIResponse(text="Enhanced response")
        mock_llm.generate_response.return_value = expected_response

        result = core.process_input("Test input")

        # Verify conversation engine was used
        mock_engine.analyze_intent.assert_called_once_with("Test input")
        mock_engine.analyze_sentiment.assert_called_once_with("Test input")
        mock_engine.build_enhanced_prompt.assert_called_once()

    def test_process_input_with_advisors_service(self, mock_core_with_services):
        """Test input processing with advisors service integration."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        # Mock advisors service
        mock_advisors.process_message.return_value = {
            "enhanced": True,
            "suggestions": ["suggestion1", "suggestion2"],
        }

        expected_response = AIResponse(text="Advised response")
        mock_llm.generate_response.return_value = expected_response

        result = core.process_input("Test with advisors")

        # Verify advisors service was called
        mock_advisors.process_message.assert_called_once()

    def test_process_input_action_extraction_and_execution(
        self, mock_core_with_services
    ):
        """Test action extraction and execution during input processing."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        # Response with mode switch action
        response_text = (
            "Switching modes now SWITCH_MODE:test_mode ✓ Switched to test mode"
        )
        expected_response = AIResponse(
            text=response_text,
            actions=[
                {"type": "mode_switch", "target_mode": "test_mode", "priority": "high"}
            ],
        )
        mock_llm.generate_response.return_value = expected_response

        result = core.process_input("Switch to test mode")

        # Verify actions were extracted and executed
        assert len(result.actions) > 0
        assert result.actions[0]["type"] == "mode_switch"

    def test_process_voice_file_success(self, mock_core_with_voice):
        """Test successful voice file processing."""
        core, mock_llm, mock_engine, mock_advisors, mock_voice = mock_core_with_voice

        # Mock voice processor
        voice_result = Mock()
        voice_result.text = "Voice input text"
        voice_result.confidence = 0.9
        voice_result.duration = 3.0

        mock_voice.process_audio_file.return_value = voice_result

        expected_response = AIResponse(text="Voice response")
        mock_llm.generate_response.return_value = expected_response

        result = core.process_voice_file("/path/to/audio.wav")

        assert result.text == "Voice response"
        mock_voice.process_audio_file.assert_called_once_with("/path/to/audio.wav")

    def test_process_voice_file_no_voice_processor(self, mock_core_with_services):
        """Test voice file processing when voice processor is unavailable."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        result = core.process_voice_file("/path/to/audio.wav")

        assert "Voice processing not available" in result.text
        assert result.confidence == 0.0
        assert result.intent == "error"

    def test_process_voice_file_processing_error(self, mock_core_with_voice):
        """Test voice file processing with voice processor error."""
        core, mock_llm, mock_engine, mock_advisors, mock_voice = mock_core_with_voice

        mock_voice.process_audio_file.side_effect = Exception("Audio processing failed")

        result = core.process_voice_file("/path/to/audio.wav")

        assert "Error processing voice file" in result.text
        assert result.confidence == 0.0
        assert result.intent == "error"


class TestIntelligenceCoreIntentAnalysis:
    """Comprehensive tests for intent analysis methods."""

    def test_analyze_intent_mode_switching(self, mock_core):
        """Test intent analysis for mode switching."""
        test_cases = [
            ("switch to computer mode", "mode_switch"),
            ("change to idle mode", "mode_switch"),
            ("go to chatty mode", "mode_switch"),
            ("can you switch modes", "mode_switch"),
        ]

        for text, expected_intent in test_cases:
            result = core._analyze_intent(text)
            assert result == expected_intent, f"Failed for text: {text}"

    def test_analyze_intent_system_commands(self, mock_core):
        """Test intent analysis for system commands."""
        test_cases = [
            ("take a screenshot", "screenshot"),
            ("capture the screen", "screenshot"),
            ("take picture", "screenshot"),
            ("turn on lights", "lights_on"),
            ("lights on please", "lights_on"),
            ("turn off lights", "lights_off"),
            ("lights off now", "lights_off"),
        ]

        for text, expected_intent in test_cases:
            result = core._analyze_intent(text)
            assert result == expected_intent, f"Failed for text: {text}"

    def test_analyze_intent_questions(self, mock_core):
        """Test intent analysis for questions."""
        test_cases = [
            ("what is the weather", "question"),
            ("how are you doing", "question"),
            ("why is the sky blue", "question"),
            ("when will you be ready", "question"),
            ("where is the library", "question"),
            ("who are you", "question"),
        ]

        for text, expected_intent in test_cases:
            result = core._analyze_intent(text)
            assert result == expected_intent, f"Failed for text: {text}"

    def test_analyze_intent_greetings(self, mock_core):
        """Test intent analysis for greetings."""
        test_cases = [
            ("hello", "greeting"),
            ("hi there", "greeting"),
            ("hey", "greeting"),
            ("good morning", "greeting"),
            ("good afternoon", "greeting"),
        ]

        for text, expected_intent in test_cases:
            result = core._analyze_intent(text)
            assert result == expected_intent, f"Failed for text: {text}"

    def test_analyze_intent_task_requests(self, mock_core):
        """Test intent analysis for task requests."""
        test_cases = [
            ("help me with this", "task_request"),
            ("assist me please", "task_request"),
            ("do this task", "task_request"),
            ("make a reservation", "task_request"),
            ("create a document", "task_request"),
        ]

        for text, expected_intent in test_cases:
            result = core._analyze_intent(text)
            assert result == expected_intent, f"Failed for text: {text}"

    def test_analyze_intent_conversation_fallback(self, mock_core):
        """Test intent analysis fallback to conversation."""
        test_cases = [
            ("I think this is interesting", "conversation"),
            ("tell me about yourself", "conversation"),
            ("that's fascinating", "conversation"),
            ("random text", "conversation"),
        ]

        for text, expected_intent in test_cases:
            result = core._analyze_intent(text)
            assert result == expected_intent, f"Failed for text: {text}"

    def test_analyze_intent_case_insensitive(self, mock_core):
        """Test intent analysis is case insensitive."""
        test_cases = [
            ("SWITCH TO COMPUTER MODE", "mode_switch"),
            ("HELLO", "greeting"),
            ("Take A Screenshot", "screenshot"),
            ("WHAT IS THIS", "question"),
        ]

        for text, expected_intent in test_cases:
            result = core._analyze_intent(text)
            assert result == expected_intent, f"Failed for text: {text}"


class TestIntelligenceCoreActionExtraction:
    """Comprehensive tests for action extraction methods."""

    def test_extract_mode_switch_actions(self, mock_core):
        """Test extraction of mode switch actions."""
        test_cases = [
            (
                "Switching to computer mode SWITCH_MODE:computer",
                [
                    {
                        "type": "mode_switch",
                        "target_mode": "computer",
                        "priority": "high",
                    }
                ],
            ),
            (
                "SWITCH_MODE:test_mode and then SWITCH_MODE:backup",
                [
                    {"type": "mode_switch", "target_mode": "test", "priority": "high"},
                    {
                        "type": "mode_switch",
                        "target_mode": "backup",
                        "priority": "high",
                    },
                ],
            ),
        ]

        for text, expected_actions in test_cases:
            result = core._extract_actions(text)
            assert result == expected_actions, f"Failed for text: {text}"

    def test_extract_mode_switched_confirmation(self, mock_core):
        """Test extraction of mode switched confirmation."""
        text = "Mode switched successfully ✓ Switched to computer mode"
        result = core._extract_actions(text)

        assert len(result) == 1
        assert result[0]["type"] == "mode_switched"
        assert result[0]["priority"] == "info"

    def test_extract_system_command_actions(self, mock_core):
        """Test extraction of system command actions."""
        test_cases = [
            ("I'll take a screenshot", [{"type": "screenshot", "priority": "medium"}]),
            ("Turning lights on", [{"type": "lights_on", "priority": "medium"}]),
            ("Lights off now", [{"type": "lights_off", "priority": "medium"}]),
        ]

        for text, expected_actions in test_cases:
            result = core._extract_actions(text)
            assert result == expected_actions, f"Failed for text: {text}"

    def test_extract_multiple_actions(self, mock_core):
        """Test extraction of multiple actions from single text."""
        text = "I'll take a screenshot and turn lights on, then SWITCH_MODE:test_mode"
        result = core._extract_actions(text)

        action_types = [action["type"] for action in result]
        assert "screenshot" in action_types
        assert "lights_on" in action_types
        assert "mode_switch" in action_types

    def test_extract_no_actions(self, mock_core):
        """Test extraction when no actions are present."""
        text = "This is just a regular conversation with no actions"
        result = core._extract_actions(text)

        assert result == []

    def test_extract_actions_case_insensitive(self, mock_core):
        """Test action extraction is case insensitive."""
        text = "TAKE A SCREENSHOT and SWITCH_MODE:COMPUTER"
        result = core._extract_actions(text)

        action_types = [action["type"] for action in result]
        assert "screenshot" in action_types
        assert "mode_switch" in action_types


class TestIntelligenceCoreActionExecution:
    """Comprehensive tests for action execution methods."""

    def test_execute_mode_switch_action(self, mock_core_with_services):
        """Test execution of mode switch action."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        # Set up mode change callback
        mode_change_callback = Mock()
        core.on_mode_change = mode_change_callback

        actions = [
            {"type": "mode_switch", "target_mode": "computer", "priority": "high"}
        ]

        core._execute_actions(actions)

        # Verify state manager was called
        core.state_manager.change_state.assert_called_once_with("computer")
        # Verify callback was called
        mode_change_callback.assert_called_once_with("computer")

    def test_execute_screenshot_action(self, mock_core_with_services):
        """Test execution of screenshot action."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        actions = [{"type": "screenshot", "priority": "medium"}]

        with patch.object(core.logger, "info") as mock_log:
            core._execute_actions(actions)

            # Verify logging (screenshot action currently just logs)
            mock_log.assert_called_with("Executing screenshot command")

    def test_execute_lights_actions(self, mock_core_with_services):
        """Test execution of lights on/off actions."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        test_cases = [
            (
                {"type": "lights_on", "priority": "medium"},
                "Executing lights_on command",
            ),
            (
                {"type": "lights_off", "priority": "medium"},
                "Executing lights_off command",
            ),
        ]

        for action, expected_log in test_cases:
            with patch.object(core.logger, "info") as mock_log:
                core._execute_actions([action])
                mock_log.assert_called_with(expected_log)

    def test_execute_action_with_error_handling(self, mock_core_with_services):
        """Test action execution error handling."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        # Make state manager raise an exception
        core.state_manager.change_state.side_effect = Exception("State change failed")

        actions = [
            {"type": "mode_switch", "target_mode": "computer", "priority": "high"}
        ]

        with patch.object(core.logger, "error") as mock_log_error:
            core._execute_actions(actions)

            # Verify error was logged but no exception was raised
            mock_log_error.assert_called_once()
            assert "Failed to execute action" in mock_log_error.call_args[0][0]

    def test_execute_unknown_action_type(self, mock_core_with_services):
        """Test execution of unknown action type."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        actions = [{"type": "unknown_action", "priority": "high"}]

        # Should not raise exception, should handle gracefully
        core._execute_actions(actions)

        # No specific assertions needed - just ensuring no exception


class TestIntelligenceCoreVoiceHandling:
    """Comprehensive tests for voice handling methods."""

    def test_start_voice_listening_success(self, mock_core_with_voice):
        """Test successful voice listening start."""
        core, mock_llm, mock_engine, mock_advisors, mock_voice = mock_core_with_voice

        core.start_voice_listening()

        assert core.listening_mode == "continuous"
        mock_voice.start_listening.assert_called_once()

    def test_start_voice_listening_no_voice_processor(self, mock_core_with_services):
        """Test voice listening start when voice processor is unavailable."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        with patch.object(core.logger, "warning") as mock_log:
            core.start_voice_listening()

            mock_log.assert_called_with("Voice processor not available")
            assert core.listening_mode == "off"  # Should remain off

    def test_stop_voice_listening_success(self, mock_core_with_voice):
        """Test successful voice listening stop."""
        core, mock_llm, mock_engine, mock_advisors, mock_voice = mock_core_with_voice

        # First start listening
        core.start_voice_listening()
        assert core.listening_mode == "continuous"

        # Then stop listening
        core.stop_voice_listening()

        assert core.listening_mode == "off"
        mock_voice.stop_listening.assert_called_once()

    def test_stop_voice_listening_no_voice_processor(self, mock_core_with_services):
        """Test voice listening stop when voice processor is unavailable."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        # Should not raise exception
        core.stop_voice_listening()
        assert core.listening_mode == "off"


class TestIntelligenceCorePersonalityAndState:
    """Comprehensive tests for personality and state management."""

    def test_set_persona(self, mock_core):
        """Test persona setting."""
        with patch.object(core.logger, "info") as mock_log:
            core.set_persona("professional")

            assert core.active_persona == "professional"
            mock_log.assert_called_with("Changed persona to professional")

    def test_get_conversation_stats(self, mock_core_with_services):
        """Test conversation statistics retrieval."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        # Set up some state
        core.active_persona = "test_persona"
        core.listening_mode = "continuous"
        mock_advisors.enabled = True

        stats = core.get_conversation_stats()

        assert stats["active_persona"] == "test_persona"
        assert stats["current_mode"] == mock_core.state_manager.current_state
        assert stats["listening_mode"] == "continuous"
        assert stats["voice_available"] is False  # No voice processor in this mock
        assert stats["advisors_enabled"] is True

    def test_get_conversation_stats_with_voice(self, mock_core_with_voice):
        """Test conversation statistics with voice processor."""
        core, mock_llm, mock_engine, mock_advisors, mock_voice = mock_core_with_voice

        stats = core.get_conversation_stats()

        assert stats["voice_available"] is True

    def test_shutdown(self, mock_core_with_voice):
        """Test core shutdown."""
        core, mock_llm, mock_engine, mock_advisors, mock_voice = mock_core_with_voice

        # Start listening first
        core.start_voice_listening()
        assert core.listening_mode == "continuous"

        # Then shutdown
        with patch.object(core.logger, "info") as mock_log:
            core.shutdown()

            assert core.listening_mode == "off"
            mock_voice.stop_listening.assert_called_once()
            mock_log.assert_called_with("Intelligence core shutdown")


class TestIntelligenceCoreErrorHandling:
    """Comprehensive tests for error handling scenarios."""

    def test_process_input_with_llm_service_error(self, mock_core_with_services):
        """Test input processing when LLM service fails."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        mock_llm.generate_response.side_effect = Exception("LLM service error")

        with patch.object(core.logger, "error") as mock_log_error:
            result = core.process_input("Test input")

            assert "I apologize, but I encountered an error" in result.text
            assert result.confidence == 0.0
            assert result.intent == "error"
            assert "error" in result.metadata
            mock_log_error.assert_called_once_with(
                "Error processing input: LLM service error"
            )

    def test_process_input_with_conversation_engine_error(
        self, mock_core_with_services
    ):
        """Test input processing when conversation engine fails."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        mock_engine.build_enhanced_prompt.side_effect = Exception("Engine error")

        expected_response = AIResponse(text="Fallback response")
        mock_llm.generate_response.return_value = expected_response

        # Should handle error gracefully and continue
        result = core.process_input("Test input")

        assert result.text == "Fallback response"

    def test_process_input_with_advisors_service_error(self, mock_core_with_services):
        """Test input processing when advisors service fails."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        mock_advisors.process_message.side_effect = Exception("Advisors error")

        expected_response = AIResponse(text="Response despite advisors error")
        mock_llm.generate_response.return_value = expected_response

        # Should handle error gracefully and continue
        result = core.process_input("Test input")

        assert result.text == "Response despite advisors error"

    def test_voice_processor_initialization_error_handling(self, mock_config):
        """Test voice processor initialization error handling."""
        mock_config.voice_enabled = True

        with patch(
            "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor"
        ) as mock_create_voice:
            mock_create_voice.side_effect = Exception("Voice init failed")

            with patch.object(
                logging.getLogger("src.chatty_commander.ai.intelligence_core"), "error"
            ) as mock_log_error:
                core = IntelligenceCore(mock_config)

                assert core.voice_processor is None
                mock_log_error.assert_called_once_with(
                    "Failed to initialize voice processor: Voice init failed"
                )

    def test_action_execution_error_propagation(self, mock_core_with_services):
        """Test that action execution errors don't crash the system."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        # Make state manager raise an exception
        core.state_manager.change_state.side_effect = Exception("State change failed")

        # Create a response that will trigger action execution
        response_text = "SWITCH_MODE:test_mode"
        expected_response = AIResponse(text=response_text)
        mock_llm.generate_response.return_value = expected_response

        with patch.object(core.logger, "error") as mock_log_error:
            # Should not raise exception despite action execution failure
            result = core.process_input("Switch modes")

            assert result.text == response_text
            mock_log_error.assert_called()  # Error should be logged

    def test_edge_case_empty_and_none_inputs(self, mock_core_with_services):
        """Test handling of edge case inputs."""
        core, mock_llm, mock_engine, mock_advisors = mock_core_with_services

        test_cases = [
            ("", "Empty string"),
            ("   ", "Whitespace only"),
            ("\n\t", "Special characters"),
        ]

        for text, description in test_cases:
            expected_response = AIResponse(text=f"Response to {description}")
            mock_llm.generate_response.return_value = expected_response

            # Should handle gracefully without crashing
            result = core.process_input(text)

            assert result is not None


class TestIntelligenceCoreFactoryFunction:
    """Comprehensive tests for the factory function."""

    def test_create_intelligence_core_factory(self, mock_config):
        """Test factory function creates IntelligenceCore correctly."""
        core = create_intelligence_core(mock_config)

        assert isinstance(core, IntelligenceCore)
        assert core.config == mock_config

    def test_create_intelligence_core_with_custom_config(self):
        """Test factory function with custom configuration."""
        custom_config = Config()
        custom_config.ai_enabled = True
        custom_config.voice_enabled = True

        core = create_intelligence_core(custom_config)

        assert isinstance(core, IntelligenceCore)
        assert core.config == custom_config


# Test fixtures
@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = Mock(spec=Config)
    config.ai_enabled = True
    config.voice_enabled = False
    config.ai_config = {"test": "config"}
    config.voice_config = {"voice": "config"}
    return config


@pytest.fixture
def mock_state_manager():
    """Create a mock state manager."""
    manager = Mock(spec=StateManager)
    manager.current_state = "chatty"
    manager.change_state = Mock()
    return manager


@pytest.fixture
def mock_voice_processor():
    """Create a mock voice processor."""
    processor = Mock()
    processor.start_listening = Mock()
    processor.stop_listening = Mock()
    processor.process_audio_file = Mock()
    return processor


@pytest.fixture
def mock_advisors_service():
    """Create a mock advisors service."""
    service = Mock()
    service.enabled = True
    service.process_message = Mock(return_value={"enhanced": True})
    return service


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    service = Mock()
    service.generate_response = Mock(return_value=AIResponse(text="Test response"))
    return service


@pytest.fixture
def mock_core(mock_config, mock_state_manager):
    """Create a basic IntelligenceCore mock."""
    with patch(
        "src.chatty_commander.models.StateManager", return_value=mock_state_manager
    ):
        core = IntelligenceCore(mock_config)
        return core


@pytest.fixture
def mock_core_with_services(
    mock_config, mock_state_manager, mock_llm_service, mock_advisors_service
):
    """Create IntelligenceCore with all services mocked."""
    with patch(
        "src.chatty_commander.models.StateManager", return_value=mock_state_manager
    ), patch(
        "src.chatty_commander.ai.intelligence_core.LLMService",
        return_value=mock_llm_service,
    ), patch(
        "src.chatty_commander.ai.intelligence_core.AdvisorsService",
        return_value=mock_advisors_service,
    ), patch(
        "src.chatty_commander.ai.intelligence_core.create_conversation_engine"
    ) as mock_create_engine:
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine

        core = IntelligenceCore(mock_config)
        return core, mock_llm_service, mock_engine, mock_advisors_service


@pytest.fixture
def mock_core_with_voice(
    mock_config,
    mock_state_manager,
    mock_llm_service,
    mock_advisors_service,
    mock_voice_processor,
):
    """Create IntelligenceCore with voice processor."""
    mock_config.voice_enabled = True

    with patch(
        "src.chatty_commander.models.StateManager", return_value=mock_state_manager
    ), patch(
        "src.chatty_commander.ai.intelligence_core.LLMService",
        return_value=mock_llm_service,
    ), patch(
        "src.chatty_commander.ai.intelligence_core.AdvisorsService",
        return_value=mock_advisors_service,
    ), patch(
        "src.chatty_commander.ai.intelligence_core.create_enhanced_voice_processor",
        return_value=mock_voice_processor,
    ), patch(
        "src.chatty_commander.ai.intelligence_core.create_conversation_engine"
    ) as mock_create_engine:
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine

        core = IntelligenceCore(mock_config)
        return (
            core,
            mock_llm_service,
            mock_engine,
            mock_advisors_service,
            mock_voice_processor,
        )
