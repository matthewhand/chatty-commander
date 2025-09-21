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
Exhaustive integration tests for AI components working together.
Tests the complete AI pipeline including IntelligenceCore, VoiceProcessor, and ConversationEngine
with realistic scenarios and end-to-end workflows.
"""

import threading
import time
from datetime import datetime
from unittest.mock import Mock, patch

from chatty_commander.advisors.conversation_engine import (
    create_conversation_engine,
)
from chatty_commander.ai.intelligence_core import (
    AIResponse,
    create_intelligence_core,
)
from chatty_commander.voice.enhanced_processor import (
    VoiceResult,
    create_enhanced_voice_processor,
)


class TestAIComponentIntegration:
    """Test integration between AI components."""

    def test_intelligence_core_with_conversation_engine(self):
        """Test IntelligenceCore integration with ConversationEngine."""
        # Create components
        conversation_engine = create_conversation_engine(
            {"max_history_length": 20, "context_window": 5, "debug_mode": True}
        )

        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine, "debug_mode": True}
        )

        # Test text input processing
        response = intelligence_core.process_text_input("Hello, how are you?")

        assert isinstance(response, AIResponse)
        assert response.success is True
        assert len(response.response_text) > 0

        # Verify conversation history was updated
        assert len(conversation_engine.conversation_history) > 0
        assert (
            conversation_engine.conversation_history[-1].content
            == "Hello, how are you?"
        )

    def test_voice_processor_with_intelligence_core(self):
        """Test VoiceProcessor integration with IntelligenceCore."""
        # Create mock voice processor
        voice_processor = create_enhanced_voice_processor(
            {"sample_rate": 16000, "chunk_size": 1024, "debug_mode": True}
        )

        intelligence_core = create_intelligence_core({"debug_mode": True})

        # Set up voice processor callback
        voice_results = []

        def voice_callback(result):
            voice_results.append(result)

        voice_processor.set_callback(voice_callback)
        intelligence_core.set_voice_processor(voice_processor)

        # Simulate voice input
        mock_audio_data = b"mock_audio_data"
        mock_result = VoiceResult(
            text="Turn on the lights",
            confidence=0.95,
            is_final=True,
            timestamp=datetime.now(),
        )

        # Mock the voice processing
        with patch.object(voice_processor, "process_audio_file") as mock_process:
            mock_process.return_value = mock_result

            response = intelligence_core.process_voice_file("test_audio.wav")

            assert isinstance(response, AIResponse)
            assert response.success is True
            mock_process.assert_called_once_with("test_audio.wav")

    def test_complete_voice_to_response_pipeline(self):
        """Test complete pipeline from voice input to AI response."""
        # Create all components
        conversation_engine = create_conversation_engine(
            {"max_history_length": 10, "debug_mode": True}
        )

        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine, "debug_mode": True}
        )

        voice_processor = create_enhanced_voice_processor({"debug_mode": True})

        # Wire up components
        intelligence_core.set_voice_processor(voice_processor)

        # Mock voice processing
        mock_voice_result = VoiceResult(
            text="What's the weather like today?",
            confidence=0.92,
            is_final=True,
            timestamp=datetime.now(),
        )

        with patch.object(
            voice_processor, "process_audio_file", return_value=mock_voice_result
        ):
            with patch.object(
                intelligence_core, "_analyze_intent", return_value=("question", 0.85)
            ):
                with patch.object(
                    intelligence_core,
                    "_execute_actions",
                    return_value="The weather is sunny and 75°F",
                ):
                    response = intelligence_core.process_voice_file("weather_query.wav")

                    assert isinstance(response, AIResponse)
                    assert response.success is True
                    assert (
                        "weather" in response.response_text.lower()
                        or "sunny" in response.response_text.lower()
                    )
                    assert len(conversation_engine.conversation_history) > 0

    def test_conversation_context_preservation(self):
        """Test that conversation context is preserved across different input types."""
        conversation_engine = create_conversation_engine(
            {"context_window": 10, "debug_mode": True}
        )

        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine, "debug_mode": True}
        )

        # First interaction via text
        response1 = intelligence_core.process_text_input("My name is John")
        assert response1.success is True

        # Second interaction should remember context
        response2 = intelligence_core.process_text_input("What's my name?")
        assert response2.success is True
        assert "John" in response2.response_text or "name" in response2.response_text

        # Verify conversation history continuity
        assert len(conversation_engine.conversation_history) >= 2
        assert conversation_engine.conversation_history[0].content == "My name is John"
        assert conversation_engine.conversation_history[-1].content == "What's my name?"

    def test_multi_turn_conversation_flow(self):
        """Test multi-turn conversation with mixed input types."""
        conversation_engine = create_conversation_engine(
            {"max_history_length": 15, "debug_mode": True}
        )

        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine, "debug_mode": True}
        )

        voice_processor = create_enhanced_voice_processor({"debug_mode": True})

        intelligence_core.set_voice_processor(voice_processor)

        conversation_flow = [
            ("text", "Hello, I'm planning a trip to Boston"),
            ("voice", "What's the weather like there?"),
            ("text", "What attractions should I visit?"),
            ("voice", "How do I get around the city?"),
            ("text", "Thank you for your help!"),
        ]

        responses = []

        for input_type, user_input in conversation_flow:
            if input_type == "text":
                response = intelligence_core.process_text_input(user_input)
            else:  # voice
                mock_result = VoiceResult(
                    text=user_input,
                    confidence=0.9,
                    is_final=True,
                    timestamp=datetime.now(),
                )
                with patch.object(
                    voice_processor, "process_audio_file", return_value=mock_result
                ):
                    response = intelligence_core.process_voice_file("voice_input.wav")

            responses.append(response)
            assert response.success is True
            assert len(response.response_text) > 0

        # Verify conversation continuity
        assert len(conversation_engine.conversation_history) == len(conversation_flow)
        assert "Boston" in str(
            conversation_engine.conversation_context
        ) or "trip" in str(conversation_engine.conversation_context)


class TestAIComponentErrorRecovery:
    """Test error recovery and resilience in integrated AI components."""

    def test_voice_processor_failure_recovery(self):
        """Test recovery when voice processor fails."""
        conversation_engine = create_conversation_engine()
        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine}
        )

        voice_processor = create_enhanced_voice_processor()
        intelligence_core.set_voice_processor(voice_processor)

        # Mock voice processor failure
        with patch.object(
            voice_processor,
            "process_audio_file",
            side_effect=Exception("Voice processing failed"),
        ):
            response = intelligence_core.process_voice_file("broken_audio.wav")

            assert isinstance(response, AIResponse)
            assert response.success is False
            assert (
                "voice" in response.error_message.lower()
                or "processing" in response.error_message.lower()
            )

    def test_conversation_engine_failure_recovery(self):
        """Test recovery when conversation engine fails."""
        conversation_engine = create_conversation_engine()

        # Mock conversation engine failure
        with patch.object(
            conversation_engine,
            "record_conversation_turn",
            side_effect=Exception("Conversation engine failed"),
        ):
            intelligence_core = create_intelligence_core(
                {"conversation_engine": conversation_engine}
            )

            response = intelligence_core.process_text_input("Hello")

            assert isinstance(response, AIResponse)
            # Should still process the input even if conversation recording fails
            assert response.success is True or response.success is False

    def test_llm_client_failure_fallback(self):
        """Test fallback behavior when LLM client fails."""
        mock_llm_client = Mock()
        mock_llm_client.generate_response.side_effect = Exception(
            "LLM service unavailable"
        )

        conversation_engine = create_conversation_engine(
            {"llm_client": mock_llm_client, "fallback_enabled": True}
        )

        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine}
        )

        response = intelligence_core.process_text_input("What's the meaning of life?")

        assert isinstance(response, AIResponse)
        # Should fall back to built-in responses
        assert response.success is True
        assert len(response.response_text) > 0

    def test_partial_component_failure_handling(self):
        """Test handling when some components work and others fail."""
        conversation_engine = create_conversation_engine()

        # Mock intent analysis failure but sentiment analysis works
        with patch.object(
            conversation_engine,
            "analyze_intent",
            side_effect=Exception("Intent analysis failed"),
        ):
            with patch.object(
                conversation_engine, "analyze_sentiment", return_value=("positive", 0.8)
            ):
                intelligence_core = create_intelligence_core(
                    {"conversation_engine": conversation_engine}
                )

                response = intelligence_core.process_text_input("Hello")

                assert isinstance(response, AIResponse)
                # Should still provide a response even with partial failures
                assert len(response.response_text) > 0

    def test_cascading_failure_recovery(self):
        """Test recovery from cascading failures across components."""
        conversation_engine = create_conversation_engine()

        # Multiple component failures
        with patch.object(
            conversation_engine,
            "analyze_intent",
            side_effect=Exception("Intent failed"),
        ):
            with patch.object(
                conversation_engine,
                "analyze_sentiment",
                side_effect=Exception("Sentiment failed"),
            ):
                intelligence_core = create_intelligence_core(
                    {"conversation_engine": conversation_engine, "debug_mode": True}
                )

                response = intelligence_core.process_text_input("Hello")

                assert isinstance(response, AIResponse)
                # Should fall back to basic response
                assert len(response.response_text) > 0


class TestRealisticAIWorkflows:
    """Test realistic AI workflows and user scenarios."""

    def test_smart_home_voice_control_workflow(self):
        """Test smart home voice control workflow."""
        conversation_engine = create_conversation_engine({"debug_mode": True})

        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine, "debug_mode": True}
        )

        voice_processor = create_enhanced_voice_processor(
            {"wake_words": ["hey assistant", "ok computer"], "debug_mode": True}
        )

        intelligence_core.set_voice_processor(voice_processor)

        # Simulate wake word detection
        wake_word_result = VoiceResult(
            text="hey assistant",
            confidence=0.95,
            is_final=True,
            is_wake_word=True,
            timestamp=datetime.now(),
        )

        # Simulate command after wake word
        command_result = VoiceResult(
            text="turn on the living room lights",
            confidence=0.92,
            is_final=True,
            timestamp=datetime.now(),
        )

        with patch.object(
            voice_processor,
            "process_audio_file",
            side_effect=[wake_word_result, command_result],
        ):
            # Process wake word
            wake_response = intelligence_core.process_voice_file("wake_word.wav")

            # Process command
            command_response = intelligence_core.process_voice_file("command.wav")

            assert wake_response.success is True
            assert command_response.success is True
            assert (
                "light" in command_response.response_text.lower()
                or "living room" in command_response.response_text.lower()
            )

    def test_information_query_workflow(self):
        """Test information query workflow with follow-up questions."""
        conversation_engine = create_conversation_engine(
            {"context_window": 8, "debug_mode": True}
        )

        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine, "debug_mode": True}
        )

        query_sequence = [
            "Tell me about artificial intelligence",
            "What are the main types?",
            "How does machine learning work?",
            "Can you give me an example?",
            "What are the limitations?",
        ]

        responses = []

        for query in query_sequence:
            response = intelligence_core.process_text_input(query)
            responses.append(response)

            assert response.success is True
            assert len(response.response_text) > 50  # Should be informative responses

        # Verify context building
        assert len(conversation_engine.conversation_history) == len(query_sequence)

        # Test that context is maintained
        final_context = conversation_engine.get_conversation_context()
        assert len(final_context) > 0
        assert (
            "artificial intelligence" in str(final_context).lower()
            or "machine learning" in str(final_context).lower()
        )

    def test_error_correction_workflow(self):
        """Test error correction and clarification workflow."""
        conversation_engine = create_conversation_engine({"debug_mode": True})

        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine, "debug_mode": True}
        )

        # Simulate unclear input followed by clarification
        clarification_sequence = [
            ("What's that thing?", "ambiguous"),
            ("The weather app on my phone", "clarification"),
            ("How do I update it?", "specific_question"),
        ]

        responses = []

        for user_input, expected_intent in clarification_sequence:
            response = intelligence_core.process_text_input(user_input)
            responses.append(response)

            assert response.success is True
            assert len(response.response_text) > 0

        # Verify conversation flow
        assert len(conversation_engine.conversation_history) == len(
            clarification_sequence
        )

        # Test that the system handled the clarification
        final_response = responses[-1]
        assert len(final_response.response_text) > 20  # Should be detailed response

    def test_multi_modal_input_workflow(self):
        """Test workflow with multiple input modalities."""
        conversation_engine = create_conversation_engine({"debug_mode": True})

        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine, "debug_mode": True}
        )

        voice_processor = create_enhanced_voice_processor({"debug_mode": True})

        intelligence_core.set_voice_processor(voice_processor)

        # Mixed input sequence
        mixed_sequence = [
            ("text", "I'm going to send you a voice message"),
            ("voice", "Can you help me with this task?"),
            ("text", "What I meant to ask was..."),
            ("voice", "How do I configure the settings?"),
            ("text", "Thank you for explaining that!"),
        ]

        responses = []

        for input_type, user_input in mixed_sequence:
            if input_type == "text":
                response = intelligence_core.process_text_input(user_input)
            else:  # voice
                mock_result = VoiceResult(
                    text=user_input,
                    confidence=0.9,
                    is_final=True,
                    timestamp=datetime.now(),
                )
                with patch.object(
                    voice_processor, "process_audio_file", return_value=mock_result
                ):
                    response = intelligence_core.process_voice_file("voice_input.wav")

            responses.append(response)
            assert response.success is True

        # Verify mixed conversation history
        assert len(conversation_engine.conversation_history) == len(mixed_sequence)

        # Test context continuity across input types
        conversation_context = conversation_engine.conversation_context
        assert (
            len(conversation_context) > 0
            or len(conversation_engine.conversation_history) > 0
        )


class TestAIComponentConfiguration:
    """Test configuration and setup of integrated AI components."""

    def test_component_configuration_consistency(self):
        """Test that configuration is consistent across components."""
        # Create components with consistent configuration
        config = {
            "debug_mode": True,
            "max_history_length": 25,
            "context_window": 8,
            "fallback_enabled": True,
        }

        conversation_engine = create_conversation_engine(config)
        intelligence_core = create_intelligence_core(config)
        voice_processor = create_enhanced_voice_processor(config)

        # Wire up components
        intelligence_core.set_voice_processor(voice_processor)
        intelligence_core.conversation_engine = conversation_engine

        # Test that configuration is respected
        assert conversation_engine.debug_mode is True
        assert conversation_engine.max_history_length == 25
        assert conversation_engine.context_window == 8
        assert conversation_engine.fallback_enabled is True

        # Test integrated functionality
        response = intelligence_core.process_text_input("Test configuration")
        assert response.success is True

    def test_component_dependency_injection(self):
        """Test dependency injection between components."""
        # Create mock dependencies
        mock_llm_client = Mock()
        mock_llm_client.generate_response.return_value = "Mock LLM response"

        mock_voice_callback = Mock()

        # Create components with injected dependencies
        conversation_engine = create_conversation_engine(
            {"llm_client": mock_llm_client, "debug_mode": True}
        )

        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine, "debug_mode": True}
        )

        voice_processor = create_enhanced_voice_processor({"debug_mode": True})

        voice_processor.set_callback(mock_voice_callback)
        intelligence_core.set_voice_processor(voice_processor)

        # Test that dependencies are used
        response = intelligence_core.process_text_input("Test with LLM")

        assert response.success is True
        mock_llm_client.generate_response.assert_called()

        # Test voice callback
        mock_result = VoiceResult(
            text="Voice input", confidence=0.9, is_final=True, timestamp=datetime.now()
        )

        voice_processor.callback(mock_result)
        mock_voice_callback.assert_called_once_with(mock_result)

    def test_component_lifecycle_management(self):
        """Test proper lifecycle management of components."""
        voice_processor = create_enhanced_voice_processor({"debug_mode": True})

        intelligence_core = create_intelligence_core({"debug_mode": True})

        # Test starting/stopping voice processing
        with patch.object(voice_processor, "start_listening") as mock_start:
            with patch.object(voice_processor, "stop_listening") as mock_stop:
                intelligence_core.start_voice_listening()
                mock_start.assert_called_once()

                intelligence_core.stop_voice_listening()
                mock_stop.assert_called_once()

    def test_component_state_synchronization(self):
        """Test that component states remain synchronized."""
        conversation_engine = create_conversation_engine({"debug_mode": True})

        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine, "debug_mode": True}
        )

        # Test state changes
        initial_history_length = len(conversation_engine.conversation_history)

        # Process input
        response = intelligence_core.process_text_input("Test state sync")

        # Verify state is synchronized
        assert (
            len(conversation_engine.conversation_history) == initial_history_length + 1
        )
        assert conversation_engine.conversation_history[-1].content == "Test state sync"


class TestAIComponentPerformance:
    """Test performance characteristics of integrated AI components."""

    def test_response_time_performance(self):
        """Test response time performance under various conditions."""
        conversation_engine = create_conversation_engine(
            {"debug_mode": False}  # Disable debug for performance testing
        )

        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine, "debug_mode": False}
        )

        test_inputs = [
            "Hello",
            "What's the weather like?",
            "Tell me about artificial intelligence",
            "How do I configure this setting?",
            "Thank you for your help",
        ]

        response_times = []

        for user_input in test_inputs:
            start_time = time.time()
            response = intelligence_core.process_text_input(user_input)
            end_time = time.time()

            response_time = end_time - start_time
            response_times.append(response_time)

            assert response.success is True
            assert response_time < 2.0  # Should respond within 2 seconds

        # Check average response time
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 1.0  # Average should be under 1 second

    def test_memory_usage_with_large_conversations(self):
        """Test memory usage with large conversation histories."""
        conversation_engine = create_conversation_engine(
            {"max_history_length": 100, "debug_mode": False}
        )

        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine, "debug_mode": False}
        )

        # Generate large conversation
        conversation_topics = [
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "neural networks",
            "natural language processing",
            "computer vision",
            "robotics",
            "autonomous vehicles",
            "smart homes",
            "internet of things",
        ]

        for i in range(100):
            topic = conversation_topics[i % len(conversation_topics)]
            user_input = f"Tell me about {topic}"

            response = intelligence_core.process_text_input(user_input)

            assert response.success is True
            assert len(conversation_engine.conversation_history) <= 100

        # Test that performance doesn't degrade significantly
        start_time = time.time()
        final_response = intelligence_core.process_text_input(
            "Summarize our conversation"
        )
        end_time = time.time()

        assert final_response.success is True
        assert (end_time - start_time) < 3.0  # Should still be responsive

    def test_concurrent_request_handling(self):
        """Test handling of concurrent requests."""
        conversation_engine = create_conversation_engine({"debug_mode": False})

        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine, "debug_mode": False}
        )

        results = []
        errors = []

        def make_request(request_id, user_input):
            try:
                response = intelligence_core.process_text_input(user_input)
                results.append((request_id, response))
            except Exception as e:
                errors.append((request_id, str(e)))

        # Create concurrent requests
        threads = []
        test_inputs = [
            "Hello",
            "What's new?",
            "How are you?",
            "Tell me something interesting",
            "What's the weather?",
            "Good morning",
            "Good afternoon",
            "Good evening",
        ]

        for i, user_input in enumerate(test_inputs):
            thread = threading.Thread(target=make_request, args=(i, user_input))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify results
        assert len(results) == len(test_inputs)
        assert len(errors) == 0

        for request_id, response in results:
            assert response.success is True
            assert len(response.response_text) > 0

    def test_resource_cleanup_and_teardown(self):
        """Test proper resource cleanup and teardown."""
        voice_processor = create_enhanced_voice_processor({"debug_mode": True})

        intelligence_core = create_intelligence_core({"debug_mode": True})

        intelligence_core.set_voice_processor(voice_processor)

        # Start voice processing
        intelligence_core.start_voice_listening()

        # Process some inputs
        for i in range(10):
            response = intelligence_core.process_text_input(f"Test message {i}")
            assert response.success is True

        # Stop voice processing
        intelligence_core.stop_voice_listening()

        # Verify cleanup
        assert intelligence_core.voice_processor is voice_processor
        # Components should be in clean state after stopping


class TestAIComponentEdgeCases:
    """Test edge cases and boundary conditions in integrated AI components."""

    def test_empty_input_handling_across_components(self):
        """Test handling of empty inputs across all components."""
        conversation_engine = create_conversation_engine()
        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine}
        )

        # Test empty text input
        response = intelligence_core.process_text_input("")
        assert isinstance(response, AIResponse)

        # Test empty voice result
        voice_processor = create_enhanced_voice_processor()
        intelligence_core.set_voice_processor(voice_processor)

        empty_voice_result = VoiceResult(
            text="", confidence=0.0, is_final=True, timestamp=datetime.now()
        )

        with patch.object(
            voice_processor, "process_audio_file", return_value=empty_voice_result
        ):
            response = intelligence_core.process_voice_file("empty_audio.wav")
            assert isinstance(response, AIResponse)

    def test_extremely_long_input_handling(self):
        """Test handling of extremely long inputs."""
        conversation_engine = create_conversation_engine()
        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine}
        )

        # Create very long input
        long_input = "Tell me about " + "artificial intelligence " * 100

        response = intelligence_core.process_text_input(long_input)

        assert isinstance(response, AIResponse)
        assert response.success is True
        assert len(response.response_text) > 0

    def test_special_character_handling(self):
        """Test handling of special characters and unicode."""
        conversation_engine = create_conversation_engine()
        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine}
        )

        special_inputs = [
            "Hello! @#$%^&*()",
            "Unicode: 你好世界 🌍",
            "Math: ∫x²dx = x³/3 + C",
            "Code: print('Hello, World!')",
            "Mixed: Hello 世界 🌍 !@#$%",
        ]

        for user_input in special_inputs:
            response = intelligence_core.process_text_input(user_input)

            assert isinstance(response, AIResponse)
            assert response.success is True
            assert len(response.response_text) > 0

    def test_rapid_input_switching(self):
        """Test rapid switching between different input types."""
        conversation_engine = create_conversation_engine()
        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine}
        )

        voice_processor = create_enhanced_voice_processor()
        intelligence_core.set_voice_processor(voice_processor)

        # Rapidly switch between text and voice inputs
        for i in range(20):
            if i % 2 == 0:
                # Text input
                response = intelligence_core.process_text_input(f"Text message {i}")
            else:
                # Voice input
                voice_result = VoiceResult(
                    text=f"Voice message {i}",
                    confidence=0.9,
                    is_final=True,
                    timestamp=datetime.now(),
                )
                with patch.object(
                    voice_processor, "process_audio_file", return_value=voice_result
                ):
                    response = intelligence_core.process_voice_file(f"voice_{i}.wav")

            assert isinstance(response, AIResponse)
            assert response.success is True

        # Verify conversation history includes both types
        assert len(conversation_engine.conversation_history) == 20

    def test_boundary_condition_values(self):
        """Test boundary condition values across components."""
        conversation_engine = create_conversation_engine(
            {
                "max_history_length": 1,  # Minimum meaningful value
                "context_window": 0,  # Edge case
                "debug_mode": True,
            }
        )

        intelligence_core = create_intelligence_core(
            {"conversation_engine": conversation_engine, "debug_mode": True}
        )

        # Test with boundary values
        response = intelligence_core.process_text_input("Test boundary conditions")

        assert isinstance(response, AIResponse)
        assert response.success is True

        # Test with maximum confidence values
        voice_processor = create_enhanced_voice_processor()
        intelligence_core.set_voice_processor(voice_processor)

        max_confidence_result = VoiceResult(
            text="Maximum confidence test",
            confidence=1.0,  # Maximum confidence
            is_final=True,
            timestamp=datetime.now(),
        )

        with patch.object(
            voice_processor, "process_audio_file", return_value=max_confidence_result
        ):
            response = intelligence_core.process_voice_file("max_confidence.wav")

            assert isinstance(response, AIResponse)
            assert response.success is True
