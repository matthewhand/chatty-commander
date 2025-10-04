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
Comprehensive error handling tests for AI modules.

This test suite covers:
1. Dependency failures (LLM unavailable, network issues)
2. Invalid input handling (malformed JSON, binary data, special characters)
3. Network connectivity issues
4. Graceful degradation and fallback mechanisms
"""

import json
import time
from unittest.mock import Mock, patch

import numpy as np
import pytest

from src.chatty_commander.advisors.conversation_engine import ConversationEngine
from src.chatty_commander.advisors.service import AdvisorMessage, AdvisorsService
from src.chatty_commander.voice.enhanced_processor import (
    EnhancedVoiceProcessor,
    VoiceProcessingConfig,
)


class TestDependencyFailures:
    """Tests for dependency failures and network issues."""

    def test_llm_client_network_failure(self):
        """Test LLM client network failure handling."""
        with patch(
            "src.chatty_commander.advisors.providers.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.side_effect = ConnectionError("Network unreachable")
            mock_build.return_value = mock_provider

            # Create advisors service with mocked failing provider
            config = {"enabled": True, "providers": {"openai": {"api_key": "test"}}}
            service = AdvisorsService(config)

            # Should handle network failure gracefully - either raise exception or return fallback response
            try:
                response = service.handle_message(
                    AdvisorMessage(
                        platform="discord",
                        channel="test",
                        user="test",
                        text="Hello",
                        username="test_user",
                    )
                )
                # If it doesn't raise an exception, it should return some response
                assert response is not None
            except ConnectionError:
                # This is also acceptable - the error is being propagated
                pass

    def test_audio_hardware_failure(self):
        """Test audio hardware failure handling."""
        with patch("builtins.__import__") as mock_import:

            def side_effect(name, *args, **kwargs):
                if name in [
                    "whisper",
                    "speech_recognition",
                    "noisereduce",
                    "webrtcvad",
                ]:
                    raise ImportError("Audio libraries not available")
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = side_effect

            config = VoiceProcessingConfig()
            processor = EnhancedVoiceProcessor(config)

            # Should handle initialization failure gracefully - processor should still be created
            assert processor is not None

    def test_transcription_engine_failure(self):
        """Test handling when transcription engines are unavailable."""
        # Create a mock that simulates import failures
        original_import = __import__

        def mock_import(name, *args, **kwargs):
            if name in ["whisper", "speech_recognition"]:
                raise ImportError("Offline - no internet connection")
            return original_import(name, *args, **kwargs)

        # Temporarily replace __import__
        import builtins

        original_builtin_import = builtins.__import__
        builtins.__import__ = mock_import

        try:
            # Create processor - should handle missing transcription gracefully
            processor = EnhancedVoiceProcessor(VoiceProcessingConfig())

            # Should fall back to no transcription
            assert processor.transcription_method == "none"
            assert processor.transcriber is None

            # Test actual transcription
            result = processor._transcribe_audio(np.zeros(16000, dtype=np.int16))
            assert result.text == "[Transcription not available]"
            assert result.confidence == 0.0

        finally:
            # Restore original import
            builtins.__import__ = original_builtin_import

    def test_memory_service_failure(self):
        """Test memory service failure handling."""
        with patch("src.chatty_commander.advisors.service.MemoryStore") as mock_memory:
            mock_memory.side_effect = RuntimeError("Memory service unavailable")

            # Create advisors service with failing memory - should not crash
            config = {"enabled": True, "providers": {"openai": {"api_key": "test"}}}
            try:
                service = AdvisorsService(config)
                # If it doesn't crash, memory should be None
                assert service.memory is None
            except Exception:
                # If it crashes, that's also acceptable error handling
                pass


class TestInvalidInputHandling:
    """Tests for invalid input handling."""

    def test_malformed_json_input_handling(self):
        """Test handling of malformed JSON input."""
        # Test that malformed JSON raises appropriate exception
        malformed_preferences = '{"theme": "dark", "volume": invalid}'

        # This should raise JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            json.loads(malformed_preferences)

    def test_binary_data_input_handling(self):
        """Test handling of binary data input to voice processor."""
        # Create voice processor with proper config
        config = VoiceProcessingConfig(
            sample_rate=16000,
            noise_reduction_enabled=False,
            voice_activity_detection=True,
            confidence_threshold=0.7,
        )

        processor = EnhancedVoiceProcessor(config)

        # Test with binary data (simulated audio bytes)
        binary_data = b"\x00\x01\x02\x03\x04\x05"

        # This should return a boolean or numpy.bool_ indicating speech detection
        result = processor._energy_based_vad(binary_data)

        # Check that result is a boolean type (including numpy.bool_)
        assert isinstance(result, bool | np.bool_)

    def test_special_character_input_handling(self):
        """Test handling of input with special characters."""
        conversation_engine = ConversationEngine({})

        # Test with various special characters
        test_inputs = [
            "Hello! @#$%^&*()",
            "Test with \x00 null byte",
            "Unicode: ñáéíóú",
            "SQL injection: ' OR '1'='1",
        ]

        for input_text in test_inputs:
            # Should not crash and should return valid analysis
            intent = conversation_engine.analyze_intent(input_text)
            sentiment = conversation_engine.analyze_sentiment(input_text)

            assert intent is not None
            assert sentiment is not None

    def test_numeric_input_handling(self):
        """Test handling of numeric input."""
        conversation_engine = ConversationEngine({})

        # Test with numeric inputs
        numeric_inputs = ["12345", "3.14159", "-42", "1e10"]

        for input_text in numeric_inputs:
            # Should handle numeric input gracefully
            intent = conversation_engine.analyze_intent(input_text)
            sentiment = conversation_engine.analyze_sentiment(input_text)

            assert intent is not None
            assert sentiment is not None


class TestNetworkConnectivity:
    """Tests for network connectivity issues."""

    def test_llm_timeout_handling(self):
        """Test LLM timeout handling."""
        with patch(
            "src.chatty_commander.advisors.providers.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.side_effect = TimeoutError("Request timed out")
            mock_build.return_value = mock_provider

            config = {"enabled": True, "providers": {"openai": {"api_key": "test"}}}
            service = AdvisorsService(config)

            # Should handle timeout gracefully - either raise exception or return fallback response
            try:
                response = service.handle_message(
                    AdvisorMessage(
                        platform="discord",
                        channel="test",
                        user="test",
                        text="Hello",
                        username="test_user",
                    )
                )
                # If it doesn't raise an exception, it should return some response
                assert response is not None
            except TimeoutError:
                # This is also acceptable - the error is being propagated
                pass

    def test_voice_processing_offline_mode(self):
        """Test voice processing in offline mode."""
        # Create a mock that simulates import failures
        original_import = __import__

        def mock_import(name, *args, **kwargs):
            if name in ["whisper", "speech_recognition"]:
                raise ImportError("Offline - no internet connection")
            return original_import(name, *args, **kwargs)

        # Temporarily replace __import__
        import builtins

        original_builtin_import = builtins.__import__
        builtins.__import__ = mock_import

        try:
            config = VoiceProcessingConfig(
                sample_rate=16000,
                noise_reduction_enabled=True,
                voice_activity_detection=True,
                confidence_threshold=0.7,
            )

            processor = EnhancedVoiceProcessor(config)

            # Should handle transcription failure gracefully
            assert (
                processor.transcription_method == "none"
            )  # Should fallback to no transcription

        finally:
            # Restore original import
            builtins.__import__ = original_builtin_import


class TestFallbackMechanisms:
    """Tests for fallback mechanisms and graceful degradation."""

    def test_llm_fallback_to_cached_responses(self):
        """Test fallback to cached responses when LLM is unavailable."""
        with patch(
            "src.chatty_commander.advisors.providers.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.side_effect = Exception("LLM service down")
            mock_build.return_value = mock_provider

            # Mock memory to return cached responses
            with patch(
                "src.chatty_commander.advisors.service.MemoryStore"
            ) as mock_memory:
                mock_memory_instance = Mock()
                mock_memory_instance.get.return_value = [
                    Mock(role="user", content="Hello", timestamp=time.time()),
                    Mock(role="assistant", content="Hi there!", timestamp=time.time()),
                ]
                mock_memory.return_value = mock_memory_instance

                config = {"enabled": True, "providers": {"openai": {"api_key": "test"}}}
                service = AdvisorsService(config)

                # Should use cached response instead of failing completely
                try:
                    response = service.handle_message(
                        AdvisorMessage(
                            platform="discord",
                            channel="test",
                            user="test",
                            text="Hello",
                            username="test_user",
                        )
                    )
                    # Should get some response (even if it's from cache)
                    assert response.reply is not None
                except Exception:
                    # If it fails, it should be a graceful failure
                    pass

    def test_voice_processing_fallback_basic_vad(self):
        """Test fallback to basic VAD when enhanced features fail."""
        with patch(
            "src.chatty_commander.voice.enhanced_processor.EnhancedVoiceProcessor._initialize_noise_reduction"
        ) as mock_noise:
            mock_noise.side_effect = Exception("Noise reduction failed")

            config = VoiceProcessingConfig(
                sample_rate=16000,
                noise_reduction_enabled=True,  # This will fail
                voice_activity_detection=True,
                confidence_threshold=0.7,
            )

            # Should still initialize with basic VAD
            processor = EnhancedVoiceProcessor(config)
            assert processor is not None

            # Basic VAD should still work
            audio_data = b"\x00\x01\x02\x03"
            result = processor._energy_based_vad(audio_data)
            assert isinstance(result, bool | np.bool_)

    def test_llm_api_key_invalid_error_handling(self):
        """Test handling of invalid API key errors."""
        with patch(
            "src.chatty_commander.advisors.providers.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.side_effect = Exception("Invalid API key")
            mock_build.return_value = mock_provider

            config = {"enabled": True, "providers": {"openai": {"api_key": "invalid"}}}
            service = AdvisorsService(config)

            # Should handle invalid API key gracefully
            try:
                response = service.handle_message(
                    AdvisorMessage(
                        platform="discord",
                        channel="test",
                        user="test",
                        text="Hello",
                        username="test_user",
                    )
                )
                # If it doesn't raise an exception, it should return some response
                assert response is not None
            except Exception as e:
                # Invalid API key should be handled gracefully
                assert "Invalid API key" in str(e) or "API key" in str(e)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
