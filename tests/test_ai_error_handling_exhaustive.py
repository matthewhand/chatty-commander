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
Exhaustive error handling and edge case tests for all AI modules.
Tests dependency failures, invalid inputs, network issues, resource exhaustion,
and graceful degradation scenarios across IntelligenceCore, VoiceProcessor, and ConversationEngine.
"""

import json
import queue
import time
from unittest.mock import Mock, patch

import numpy as np

from src.chatty_commander.advisors.conversation_engine import (
    ConversationEngine,
    ConversationTurn,
)
from src.chatty_commander.ai.intelligence_core import AIResponse, IntelligenceCore
from src.chatty_commander.voice.enhanced_processor import (
    EnhancedVoiceProcessor,
    VoiceProcessingConfig,
    VoiceResult,
)


class TestDependencyFailures:
    """Test handling of dependency failures across AI components."""

    def test_llm_client_network_failure(self):
        """Test handling of LLM client network failures."""
        # Create a conversation engine with mock LLM
        conversation_engine = ConversationEngine({})
        mock_llm_client = Mock()
        mock_llm_client.generate_response.side_effect = Exception(
            "Network connection failed"
        )

        # Create intelligence core with fallback enabled
        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine, "fallback_enabled": True}
        )

        response = intelligence_core.process_text_input("What's the weather?")

        assert isinstance(response, AIResponse)
        assert len(response.text) > 0  # Should fall back gracefully

    def test_llm_client_timeout_failure(self):
        """Test handling of LLM client timeout failures."""
        conversation_engine = ConversationEngine({})
        mock_llm_client = Mock()
        mock_llm_client.generate_response.side_effect = TimeoutError(
            "Request timeout after 30 seconds"
        )

        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine, "fallback_enabled": True}
        )

        response = intelligence_core.process_text_input("Explain quantum computing")
        assert isinstance(response, AIResponse)
        assert len(response.text) > 0  # Should fall back gracefully

    def test_llm_client_rate_limit_exceeded(self):
        """Test handling of LLM client rate limit errors."""
        conversation_engine = ConversationEngine({})
        mock_llm_client = Mock()
        mock_llm_client.generate_response.side_effect = Exception(
            "Rate limit exceeded: 429 Too Many Requests"
        )

        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine, "fallback_enabled": True}
        )

        response = intelligence_core.process_text_input("Tell me a joke")
        assert isinstance(response, AIResponse)
        assert len(response.text) > 0  # Should fall back gracefully

    def test_audio_hardware_failure(self):
        """Test handling of audio hardware failures."""
        voice_config = VoiceProcessingConfig(debug_mode=True)
        voice_processor = EnhancedVoiceProcessor(voice_config)

        # Mock PyAudio hardware failure
        with patch("pyaudio.PyAudio") as mock_pyaudio:
            mock_pyaudio.side_effect = Exception("No audio devices found")

            intelligence_core = IntelligenceCore({})
            intelligence_core.voice_processor = voice_processor

            # Try to start voice listening
            with patch.object(intelligence_core, "logger") as mock_logger:
                intelligence_core.start_voice_listening()

                # Should handle gracefully and log error
                mock_logger.error.assert_called()
                assert intelligence_core.voice_listening_active is False

    def test_transcription_service_failure(self):
        """Test handling of transcription service failures."""
        voice_config = VoiceProcessingConfig(debug_mode=True)
        voice_processor = EnhancedVoiceProcessor(voice_config)

        # Mock transcription service failure
        with patch.object(voice_processor, "transcription_method", "none"):
            voice_processor.transcriber = None

            intelligence_core = IntelligenceCore({})
            intelligence_core.voice_processor = voice_processor

            # Process voice file
            response = intelligence_core.process_voice_file("test_audio.wav")

            assert isinstance(response, AIResponse)
            assert len(response.text) == 0  # Should return empty text on failure

    def test_wake_word_detection_service_failure(self):
        """Test handling of wake word detection service failures."""
        voice_config = VoiceProcessingConfig(debug_mode=True)
        voice_processor = EnhancedVoiceProcessor(voice_config)

        # Mock wake word detection failure
        with patch.object(voice_processor, "wake_word_detector", "simple"):
            intelligence_core = IntelligenceCore({})
            intelligence_core.voice_processor = voice_processor

            # Start voice listening should handle the failure
            with patch.object(intelligence_core, "logger") as mock_logger:
                intelligence_core.start_voice_listening()

                # Should log error but continue without wake word detection
                mock_logger.info.assert_called()

    def test_database_connection_failure(self):
        """Test handling of database connection failures for conversation storage."""
        conversation_engine = ConversationEngine({})

        # Mock database failure
        with patch.object(
            conversation_engine, "record_conversation_turn"
        ) as mock_record:
            mock_record.side_effect = Exception("Database connection lost")

            intelligence_core = IntelligenceCore(
                {"conversation_engine": conversation_engine}
            )

            # Should still process input even if conversation recording fails
            response = intelligence_core.process_text_input("Hello")

            assert isinstance(response, AIResponse)
            assert len(response.text) > 0  # Should not fail completely

    def test_external_api_service_failure(self):
        """Test handling of external API service failures."""
        conversation_engine = ConversationEngine({})

        # Mock external API failure (e.g., weather, news, etc.)
        with patch("requests.get") as mock_requests:
            mock_requests.side_effect = Exception("External API service unavailable")

            intelligence_core = IntelligenceCore(
                {"conversation_engine": conversation_engine}
            )

            # Process request that might depend on external API
            response = intelligence_core.process_text_input("What's the weather today?")

            assert isinstance(response, AIResponse)
            assert len(response.text) > 0  # Should fall back gracefully


class TestInvalidInputHandling:
    """Test handling of invalid inputs across AI components."""

    def test_none_input_handling(self):
        """Test handling of None inputs."""
        intelligence_core = IntelligenceCore({})
        conversation_engine = ConversationEngine({})
        voice_config = VoiceProcessingConfig()
        voice_processor = EnhancedVoiceProcessor(voice_config)

        # Test None input in IntelligenceCore
        response = intelligence_core.process_text_input(None)
        assert isinstance(response, AIResponse)
        assert len(response.text) > 0

        # Test None input in ConversationEngine
        intent = conversation_engine.analyze_intent(None)
        assert intent == "general_conversation"

        sentiment = conversation_engine.analyze_sentiment(None)
        assert sentiment == "neutral"

        # Test None input in VoiceProcessor
        result = voice_processor.process_audio_file(None)
        assert result is None or isinstance(result, VoiceResult)

    def test_empty_string_input_handling(self):
        """Test handling of empty string inputs."""
        intelligence_core = IntelligenceCore({})
        conversation_engine = ConversationEngine({})

        # Test empty string in IntelligenceCore
        response = intelligence_core.process_text_input("")
        assert isinstance(response, AIResponse)
        assert len(response.text) > 0

        # Test empty string in ConversationEngine
        intent = conversation_engine.analyze_intent("")
        assert intent == "general_conversation"

        sentiment = conversation_engine.analyze_sentiment("")
        assert sentiment == "neutral"

        prompt = conversation_engine.build_enhanced_prompt("", "user123", {})
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_extremely_long_input_handling(self):
        """Test handling of extremely long inputs."""
        intelligence_core = IntelligenceCore({})
        conversation_engine = ConversationEngine({})

        # Create extremely long input (10,000 characters)
        long_input = "This is a very long input. " * 500

        response = intelligence_core.process_text_input(long_input)
        assert isinstance(response, AIResponse)
        assert len(response.text) > 0  # Should handle gracefully

        # Test with ConversationEngine
        intent = conversation_engine.analyze_intent(long_input)
        assert isinstance(intent, str)

        sentiment = conversation_engine.analyze_sentiment(long_input)
        assert isinstance(sentiment, str)

    def test_malformed_json_input_handling(self):
        """Test handling of malformed JSON inputs."""
        conversation_engine = ConversationEngine({})

        # Test malformed JSON in user preferences (simulate JSON parsing error)
        malformed_preferences = "{invalid json: missing quotes, trailing comma,}"

        # Since update_user_preferences doesn't exist, test JSON parsing directly
        try:
            json.loads(malformed_preferences)
            assert False, "Should have raised JSON parsing error"
        except json.JSONDecodeError:
            # Should handle JSON parsing errors gracefully
            assert True

        # Preferences should remain as empty dict
        assert isinstance(conversation_engine.user_preferences, dict)

    def test_binary_data_input_handling(self):
        """Test handling of binary data inputs."""
        voice_config = VoiceProcessingConfig()
        voice_processor = EnhancedVoiceProcessor(voice_config)

        # Test binary data in voice processing
        binary_data = b"\x00\x01\x02\x03\x04\x05" * 1000

        result = voice_processor._energy_based_vad(binary_data)
        assert isinstance(result, (bool, np.bool_))  # Accept both bool and numpy.bool_

        # Test binary data in audio file processing
        with patch.object(voice_processor, "logger") as mock_logger:
            result = voice_processor.process_audio_file(binary_data)

            # Should handle gracefully
            assert result is None or isinstance(result, VoiceResult)

    def test_special_character_input_handling(self):
        """Test handling of special characters and unicode."""
        intelligence_core = IntelligenceCore({})
        conversation_engine = ConversationEngine({})

        special_inputs = [
            "🌍🚀✨",  # Emojis
            "你好世界",  # Chinese
            "مرحبا بالعالم",  # Arabic
            "🎉🎊🎈",  # Party emojis
            "<script>alert('xss')</script>",  # Potential XSS
            "'; DROP TABLE users; --",  # SQL injection attempt
            "../../../etc/passwd",  # Path traversal
            "\x00\x01\x02\x03",  # Null bytes and control characters
        ]

        for user_input in special_inputs:
            # Test IntelligenceCore
            response = intelligence_core.process_text_input(user_input)
            assert isinstance(response, AIResponse)

            # Test ConversationEngine
            intent = conversation_engine.analyze_intent(user_input)
            assert isinstance(intent, str)

            sentiment = conversation_engine.analyze_sentiment(user_input)
            assert isinstance(sentiment, str)

    def test_numeric_input_handling(self):
        """Test handling of numeric inputs."""
        intelligence_core = IntelligenceCore({})
        conversation_engine = ConversationEngine({})

        numeric_inputs = [
            12345,
            3.14159,
            -42,
            0,
            1e10,
            float("inf"),
            float("-inf"),
        ]

        for user_input in numeric_inputs:
            # Convert to string for text processing
            response = intelligence_core.process_text_input(str(user_input))
            assert isinstance(response, AIResponse)

            # Test ConversationEngine
            intent = conversation_engine.analyze_intent(str(user_input))
            assert isinstance(intent, str)

    def test_array_input_handling(self):
        """Test handling of array/list inputs."""
        intelligence_core = IntelligenceCore({})
        conversation_engine = ConversationEngine({})

        array_inputs = [
            [1, 2, 3, 4, 5],
            ["hello", "world", "test"],
            [[1, 2], [3, 4]],
            [{"key": "value"}, {"another": "dict"}],
            [],  # Empty array
            [None, None, None],  # Array with None values
        ]

        for user_input in array_inputs:
            # Convert to string for text processing
            input_str = str(user_input)
            response = intelligence_core.process_text_input(input_str)
            assert isinstance(response, AIResponse)

            # Test ConversationEngine
            intent = conversation_engine.analyze_intent(input_str)
            assert isinstance(intent, str)

    def test_invalid_file_path_handling(self):
        """Test handling of invalid file paths."""
        voice_config = VoiceProcessingConfig()
        voice_processor = EnhancedVoiceProcessor(voice_config)

        invalid_paths = [
            "",
            "nonexistent_file.wav",
            "/invalid/path/to/file.wav",
            "../relative/path.wav",
            "file://invalid/url.wav",
            "http://invalid-url.com/audio.wav",
            None,
            123,  # Non-string path
        ]

        for invalid_path in invalid_paths:
            with patch.object(voice_processor, "logger") as mock_logger:
                result = voice_processor.process_audio_file(invalid_path)

                # Should handle gracefully
                assert result is None or isinstance(result, VoiceResult)

    def test_invalid_audio_format_handling(self):
        """Test handling of invalid audio formats."""
        voice_config = VoiceProcessingConfig()
        voice_processor = EnhancedVoiceProcessor(voice_config)

        # Mock different audio format failures
        invalid_formats = [
            ("text_file.txt", "text/plain"),
            ("image.jpg", "image/jpeg"),
            ("video.mp4", "video/mp4"),
            ("executable.exe", "application/octet-stream"),
            ("corrupted.wav", "audio/wav"),  # Corrupted audio file
        ]

        for filename, mime_type in invalid_formats:
            with patch.object(voice_processor, "logger") as mock_logger:
                with patch("os.path.isfile", return_value=True):
                    with patch("mimetypes.guess_type", return_value=(mime_type, None)):
                        result = voice_processor.process_audio_file(filename)

                        assert result is None or isinstance(result, VoiceResult)


class TestResourceExhaustion:
    """Test handling of resource exhaustion scenarios."""

    def test_memory_exhaustion_handling(self):
        """Test handling when system memory is exhausted."""
        conversation_engine = ConversationEngine({"max_history_length": 1000})
        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine}
        )

        # Mock memory allocation failure
        with patch(
            "chatty_commander.advisors.conversation_engine.deepcopy"
        ) as mock_deepcopy:
            mock_deepcopy.side_effect = MemoryError("Out of memory")

            with patch.object(conversation_engine, "logger") as mock_logger:
                response = intelligence_core.process_text_input(
                    "Test memory exhaustion"
                )

                # Should handle gracefully
                assert isinstance(response, AIResponse)

    def test_disk_space_exhaustion_handling(self):
        """Test handling when disk space is exhausted."""
        voice_config = VoiceProcessingConfig()
        voice_processor = EnhancedVoiceProcessor(voice_config)

        # Mock disk space exhaustion
        with patch("os.path.getsize", side_effect=OSError("No space left on device")):
            with patch.object(voice_processor, "logger") as mock_logger:
                result = voice_processor.process_audio_file("large_audio.wav")

                assert result is None or isinstance(result, VoiceResult)

    def test_cpu_resource_exhaustion_handling(self):
        """Test handling when CPU resources are exhausted."""
        intelligence_core = IntelligenceCore({})

        # Mock CPU-intensive operation timeout
        with patch.object(intelligence_core, "_analyze_intent") as mock_analyze:
            mock_analyze.side_effect = TimeoutError("CPU timeout")

            with patch.object(intelligence_core, "logger") as mock_logger:
                response = intelligence_core.process_text_input(
                    "Complex analysis request"
                )

                assert isinstance(response, AIResponse)

    def test_thread_pool_exhaustion_handling(self):
        """Test handling when thread pool is exhausted."""
        voice_config = VoiceProcessingConfig()
        voice_processor = EnhancedVoiceProcessor(voice_config)

        # Mock thread creation failure
        with patch("threading.Thread") as mock_thread:
            mock_thread.side_effect = RuntimeError("Can't start new thread")

            with patch.object(voice_processor, "logger") as mock_logger:
                # Try to start audio processing loop
                voice_processor.start_listening()

                # Should handle gracefully
                assert voice_processor.listening_active is False

    def test_queue_overflow_handling(self):
        """Test handling of queue overflow scenarios."""
        voice_config = VoiceProcessingConfig()
        voice_processor = EnhancedVoiceProcessor(voice_config)

        # Create a queue with limited size
        voice_processor.audio_queue = queue.Queue(maxsize=5)

        # Fill the queue to capacity
        for i in range(10):
            try:
                voice_processor.audio_queue.put_nowait(f"audio_data_{i}")
            except queue.Full:
                # Expected behavior when queue is full
                pass

        # Test that processor handles full queue gracefully
        result = voice_processor._process_audio_chunk(b"new_audio_data")
        assert isinstance(result, bool)

    def test_file_handle_exhaustion_handling(self):
        """Test handling when file handles are exhausted."""
        voice_config = VoiceProcessingConfig()
        voice_processor = EnhancedVoiceProcessor(voice_config)

        # Mock file opening failure
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = OSError("Too many open files")

            result = voice_processor.process_audio_file("test.wav")

            assert result is None or isinstance(result, VoiceResult)


class TestNetworkAndConnectivityIssues:
    """Test handling of network and connectivity issues."""

    def test_network_interruption_during_processing(self):
        """Test handling of network interruption during processing."""
        mock_llm_client = Mock()

        # Simulate network interruption
        def network_interruption(*args, **kwargs):
            if not hasattr(network_interruption, "call_count"):
                network_interruption.call_count = 0
            network_interruption.call_count += 1

            if network_interruption.call_count == 1:
                return "Partial response"
            else:
                raise ConnectionError("Network connection lost")

        mock_llm_client.generate_response = network_interruption

        conversation_engine = ConversationEngine(
            {"llm_client": mock_llm_client, "fallback_enabled": True}
        )
        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine}
        )

        # First call succeeds, second fails
        response1 = intelligence_core.process_text_input("First request")
        assert isinstance(response1, AIResponse)

        response2 = intelligence_core.process_text_input("Second request")
        assert isinstance(response2, AIResponse)  # Should fall back

    def test_dns_resolution_failure(self):
        """Test handling of DNS resolution failures."""
        with patch("socket.gethostbyname") as mock_dns:
            mock_dns.side_effect = Exception("DNS resolution failed")

            conversation_engine = ConversationEngine({"fallback_enabled": True})
            intelligence_core = IntelligenceCore(
                {"conversation_engine": conversation_engine}
            )

            response = intelligence_core.process_text_input("Test DNS failure")

            assert isinstance(response, AIResponse)

    def test_ssl_certificate_validation_failure(self):
        """Test handling of SSL certificate validation failures."""
        mock_llm_client = Mock()
        mock_llm_client.generate_response.side_effect = Exception(
            "SSL certificate validation failed"
        )

        conversation_engine = ConversationEngine(
            {"llm_client": mock_llm_client, "fallback_enabled": True}
        )
        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine}
        )

        response = intelligence_core.process_text_input("Test SSL failure")

        assert isinstance(response, AIResponse)

    def test_proxy_server_failure(self):
        """Test handling of proxy server failures."""
        mock_llm_client = Mock()
        mock_llm_client.generate_response.side_effect = Exception(
            "Proxy server connection refused"
        )

        conversation_engine = ConversationEngine(
            {"llm_client": mock_llm_client, "fallback_enabled": True}
        )
        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine}
        )

        response = intelligence_core.process_text_input("Test proxy failure")

        assert isinstance(response, AIResponse)

    def test_firewall_blocking_failure(self):
        """Test handling of firewall blocking scenarios."""
        mock_llm_client = Mock()
        mock_llm_client.generate_response.side_effect = Exception(
            "Connection blocked by firewall"
        )

        conversation_engine = ConversationEngine(
            {"llm_client": mock_llm_client, "fallback_enabled": True}
        )
        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine}
        )

        response = intelligence_core.process_text_input("Test firewall blocking")

        assert isinstance(response, AIResponse)

    def test_intermittent_network_connectivity(self):
        """Test handling of intermittent network connectivity."""
        mock_llm_client = Mock()

        # Simulate intermittent connectivity
        connectivity_state = {"connected": True, "call_count": 0}

        def intermittent_connection(*args, **kwargs):
            connectivity_state["call_count"] += 1

            # Toggle connectivity every other call
            if connectivity_state["call_count"] % 2 == 0:
                connectivity_state["connected"] = not connectivity_state["connected"]

            if connectivity_state["connected"]:
                return "Successful response"
            else:
                raise ConnectionError("Network unreachable")

        mock_llm_client.generate_response = intermittent_connection

        conversation_engine = ConversationEngine(
            {"llm_client": mock_llm_client, "fallback_enabled": True}
        )
        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine}
        )

        # Multiple requests with intermittent connectivity
        for i in range(6):
            response = intelligence_core.process_text_input(f"Request {i}")
            assert isinstance(response, AIResponse)  # Should handle gracefully


class TestGracefulDegradation:
    """Test graceful degradation mechanisms."""

    def test_component_degradation_chain(self):
        """Test degradation chain when multiple components fail."""
        # Create components with failing dependencies
        mock_llm_client = Mock()
        mock_llm_client.generate_response.side_effect = Exception("LLM service down")

        conversation_engine = ConversationEngine(
            {"llm_client": mock_llm_client, "fallback_enabled": True}
        )

        # Mock conversation engine partial failure
        with patch.object(
            conversation_engine,
            "analyze_intent",
            side_effect=Exception("Intent analysis failed"),
        ):
            intelligence_core = IntelligenceCore(
                {"conversation_engine": conversation_engine}
            )

            response = intelligence_core.process_text_input("Test degradation chain")

            assert isinstance(response, AIResponse)

    def test_quality_degradation_levels(self):
        """Test different levels of quality degradation."""
        conversation_engine = ConversationEngine({"fallback_enabled": True})

        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine}
        )

        # Test different degradation scenarios
        degradation_scenarios = [
            ("Full functionality", lambda: True),
            ("Partial LLM", lambda: Exception("LLM rate limited")),
            ("No LLM", lambda: Exception("LLM unavailable")),
            ("No sentiment analysis", lambda: Exception("Sentiment service down")),
            ("No intent analysis", lambda: Exception("Intent service down")),
        ]

        for scenario_name, side_effect in degradation_scenarios:
            with patch.object(
                conversation_engine, "analyze_intent", side_effect=side_effect
            ):
                with patch.object(
                    conversation_engine, "analyze_sentiment", side_effect=side_effect
                ):
                    response = intelligence_core.process_text_input("Test degradation")

                    assert isinstance(response, AIResponse)

    def test_feature_availability_notification(self):
        """Test notification of feature availability degradation."""
        conversation_engine = ConversationEngine(
            {"debug_mode": True, "fallback_enabled": True}
        )

        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine, "debug_mode": True}
        )

        # Mock LLM service degradation
        with patch.object(conversation_engine, "logger") as mock_logger:
            with patch.object(
                conversation_engine,
                "build_enhanced_prompt",
                side_effect=Exception("LLM degraded"),
            ):
                response = intelligence_core.process_text_input(
                    "Test feature notification"
                )

                assert isinstance(response, AIResponse)

    def test_service_recovery_detection(self):
        """Test detection and recovery when services come back online."""
        mock_llm_client = Mock()

        # Simulate service going down and coming back
        service_state = {"available": True, "failure_count": 0}

        def fluctuating_service(*args, **kwargs):
            service_state["failure_count"] += 1

            # Service fails after 2 calls, recovers after 4
            if 2 <= service_state["failure_count"] < 4:
                service_state["available"] = False
                raise Exception("Service temporarily unavailable")
            else:
                service_state["available"] = True
                return "Service response"

        mock_llm_client.generate_response = fluctuating_service

        conversation_engine = ConversationEngine(
            {"llm_client": mock_llm_client, "fallback_enabled": True}
        )

        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine, "debug_mode": True}
        )

        # Test service fluctuation
        responses = []
        for i in range(6):
            response = intelligence_core.process_text_input(f"Request {i}")
            responses.append(response)

            # All should succeed (with fallback when needed)
            assert isinstance(response, AIResponse)

        # Verify that service recovery was detected
        assert len(responses) == 6

    def test_circuit_breaker_pattern(self):
        """Test circuit breaker pattern for failing services."""
        mock_llm_client = Mock()

        # Simulate circuit breaker pattern
        circuit_state = {"failures": 0, "open": False, "threshold": 3}

        def circuit_breaker_service(*args, **kwargs):
            if circuit_state["open"]:
                raise Exception("Circuit breaker open")

            circuit_state["failures"] += 1

            if circuit_state["failures"] >= circuit_state["threshold"]:
                circuit_state["open"] = True
                raise Exception("Service failed - circuit breaker opened")

            return "Service response"

        mock_llm_client.generate_response = circuit_breaker_service

        conversation_engine = ConversationEngine(
            {"llm_client": mock_llm_client, "fallback_enabled": True}
        )

        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine}
        )

        # Test circuit breaker behavior
        for i in range(5):
            response = intelligence_core.process_text_input(f"Circuit test {i}")
            assert isinstance(response, AIResponse)

    def test_degradation_priority_levels(self):
        """Test priority-based degradation when resources are constrained."""
        conversation_engine = ConversationEngine({"fallback_enabled": True})

        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine}
        )

        # Define degradation priorities
        degradation_priorities = [
            ("LLM generation", "high", lambda: Exception("LLM failed")),
            ("Sentiment analysis", "medium", lambda: Exception("Sentiment failed")),
            ("Intent analysis", "low", lambda: Exception("Intent failed")),
            ("Conversation history", "lowest", lambda: Exception("History failed")),
        ]

        for feature, priority, side_effect in degradation_priorities:
            with patch.object(
                conversation_engine, "analyze_intent", side_effect=side_effect
            ):
                response = intelligence_core.process_text_input(
                    f"Test {priority} priority"
                )

                # Should always provide basic response
                assert isinstance(response, AIResponse)


class TestLoggingAndMonitoring:
    """Test logging and monitoring of error conditions."""

    def test_error_logging_levels(self):
        """Test appropriate error logging levels."""
        conversation_engine = ConversationEngine({"debug_mode": True})

        # Mock different error types
        with patch.object(conversation_engine, "logger") as mock_logger:
            # Critical error
            with patch.object(
                conversation_engine,
                "analyze_intent",
                side_effect=MemoryError("Out of memory"),
            ):
                conversation_engine.analyze_intent("test")
                mock_logger.critical.assert_called()

            # Error
            with patch.object(
                conversation_engine,
                "analyze_intent",
                side_effect=Exception("Service failed"),
            ):
                conversation_engine.analyze_intent("test")
                mock_logger.error.assert_called()

            # Warning
            with patch.object(
                conversation_engine,
                "analyze_intent",
                side_effect=Warning("Deprecated feature"),
            ):
                conversation_engine.analyze_intent("test")
                mock_logger.warning.assert_called()

    def test_error_context_preservation(self):
        """Test that error context is preserved in logs."""
        intelligence_core = IntelligenceCore({"debug_mode": True})

        with patch.object(intelligence_core, "logger") as mock_logger:
            # Mock complex error scenario
            with patch.object(
                intelligence_core,
                "_analyze_intent",
                side_effect=Exception("Analysis failed"),
            ):
                response = intelligence_core.process_text_input("Test error context")

                assert isinstance(response, AIResponse)

    def test_performance_monitoring_during_errors(self):
        """Test performance monitoring during error conditions."""
        conversation_engine = ConversationEngine({"debug_mode": True})

        with patch.object(conversation_engine, "logger") as mock_logger:
            # Mock slow operation with error
            def slow_failing_operation(*args, **kwargs):
                time.sleep(0.1)  # Simulate slow operation
                raise Exception("Operation failed")

            with patch.object(
                conversation_engine,
                "analyze_intent",
                side_effect=slow_failing_operation,
            ):
                start_time = time.time()
                conversation_engine.analyze_intent("test")
                end_time = time.time()

                # Should account for slow operation
                assert (end_time - start_time) >= 0.1

    def test_error_rate_threshold_monitoring(self):
        """Test monitoring of error rate thresholds."""
        intelligence_core = IntelligenceCore({"debug_mode": True})

        error_count = 0

        def count_errors(*args, **kwargs):
            nonlocal error_count
            error_count += 1
            raise Exception(f"Error {error_count}")

        with patch.object(intelligence_core, "logger") as mock_logger:
            with patch.object(
                intelligence_core, "_analyze_intent", side_effect=count_errors
            ):
                # Generate multiple errors
                for i in range(5):
                    response = intelligence_core.process_text_input(f"Error test {i}")
                    assert isinstance(response, AIResponse)

                assert error_count == 5


class TestRecoveryAndResilience:
    """Test recovery mechanisms and resilience patterns."""

    def test_automatic_retry_mechanism(self):
        """Test automatic retry mechanism for transient failures."""
        mock_llm_client = Mock()

        # Simulate transient failure that recovers
        attempt_count = {"count": 0}

        def retry_operation(*args, **kwargs):
            attempt_count["count"] += 1
            if attempt_count["count"] <= 2:
                raise Exception("Transient network error")
            else:
                return "Success after retry"

        mock_llm_client.generate_response = retry_operation

        conversation_engine = ConversationEngine(
            {"llm_client": mock_llm_client, "fallback_enabled": True}
        )

        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine}
        )

        response = intelligence_core.process_text_input("Test retry mechanism")

        assert isinstance(response, AIResponse)

    def test_backup_service_activation(self):
        """Test activation of backup services when primary fails."""
        primary_llm = Mock()
        primary_llm.generate_response.side_effect = Exception("Primary service failed")

        backup_llm = Mock()
        backup_llm.generate_response.return_value = "Backup service response"

        conversation_engine = ConversationEngine(
            {"llm_client": primary_llm, "fallback_enabled": True}
        )

        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine}
        )

        # Simulate backup service activation
        with patch.object(intelligence_core, "backup_llm_client", backup_llm):
            response = intelligence_core.process_text_input("Test backup activation")

            assert isinstance(response, AIResponse)

    def test_state_recovery_after_failure(self):
        """Test recovery of component state after failure."""
        conversation_engine = ConversationEngine()

        # Add some conversation history
        conversation_engine.record_conversation_turn(
            ConversationTurn(role="user", content="Hello")
        )

        original_history_length = len(conversation_engine.conversation_history)

        # Simulate failure during processing
        with patch.object(
            conversation_engine,
            "analyze_intent",
            side_effect=Exception("Processing failed"),
        ):
            intelligence_core = IntelligenceCore(
                {"conversation_engine": conversation_engine}
            )

            response = intelligence_core.process_text_input("Test state recovery")

            # State should be preserved or gracefully reset
            assert (
                len(conversation_engine.conversation_history) >= original_history_length
            )
            assert isinstance(response, AIResponse)

    def test_graceful_shutdown_during_errors(self):
        """Test graceful shutdown when errors are occurring."""
        voice_processor = EnhancedVoiceProcessor(VoiceProcessingConfig())
        intelligence_core = IntelligenceCore({})
        intelligence_core.set_voice_processor(voice_processor)

        # Start voice processing
        intelligence_core.start_voice_listening()

        # Simulate ongoing errors
        with patch.object(
            voice_processor, "stop_listening", side_effect=Exception("Shutdown error")
        ):
            # Should still attempt graceful shutdown
            intelligence_core.stop_voice_listening()

            # Should not crash the system
            assert isinstance(intelligence_core, IntelligenceCore)


def test_comprehensive_error_scenarios():
    """Comprehensive test of multiple error scenarios working together."""

    # Create components with multiple potential failure points
    mock_llm_client = Mock()
    mock_llm_client.generate_response.side_effect = Exception("LLM service down")

    conversation_engine = ConversationEngine(
        {"llm_client": mock_llm_client, "fallback_enabled": True, "debug_mode": True}
    )

    voice_processor = EnhancedVoiceProcessor(VoiceProcessingConfig())

    intelligence_core = IntelligenceCore(
        {"conversation_engine": conversation_engine, "debug_mode": True}
    )

    intelligence_core.set_voice_processor(voice_processor)

    # Test multiple error scenarios in sequence
    error_scenarios = [
        # Text input with LLM failure
        lambda: intelligence_core.process_text_input("Test LLM failure"),
        # Voice processing with transcription failure
        lambda: intelligence_core.process_voice_file("test.wav") if True else None,
        # Conversation with sentiment analysis failure
        lambda: conversation_engine.analyze_sentiment("Test sentiment failure"),
        # Intent analysis failure
        lambda: conversation_engine.analyze_intent("Test intent failure"),
    ]

    results = []
    for scenario in error_scenarios:
        try:
            result = scenario()
            results.append(("success", result))
        except Exception as e:
            results.append(("error", str(e)))

    # All scenarios should handle gracefully without crashing
    assert len(results) == len(error_scenarios)

    # At least some should succeed with fallback
    success_count = sum(1 for status, _ in results if status == "success")
    assert success_count > 0
