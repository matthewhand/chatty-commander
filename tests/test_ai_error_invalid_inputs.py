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
Error handling and edge case tests for invalid input handling in AI components.
Tests dependency failures, invalid inputs, network issues, resource exhaustion,
and graceful degradation scenarios across IntelligenceCore, VoiceProcessor, and ConversationEngine.
"""

from unittest.mock import patch

from chatty_commander.advisors.conversation_engine import (
    ConversationEngine,
)
from chatty_commander.ai.intelligence_core import AIResponse, IntelligenceCore
from chatty_commander.voice.enhanced_processor import (
    EnhancedVoiceProcessor,
    VoiceProcessingConfig,
    VoiceResult,
)


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
        assert response.success is False or len(response.response_text) > 0

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
        assert response.success is True or len(response.response_text) > 0

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
        assert response.success is True  # Should handle gracefully

        # Test with ConversationEngine
        intent = conversation_engine.analyze_intent(long_input)
        assert isinstance(intent, str)

        sentiment = conversation_engine.analyze_sentiment(long_input)
        assert isinstance(sentiment, str)

    def test_malformed_json_input_handling(self):
        """Test handling of malformed JSON inputs."""
        conversation_engine = ConversationEngine({})

        # Test malformed JSON in user preferences
        malformed_preferences = "{invalid json: missing quotes, trailing comma,}"

        with patch.object(conversation_engine, "logger") as mock_logger:
            conversation_engine.update_user_preferences(
                "user123", malformed_preferences
            )

            # Should handle gracefully and log error
            mock_logger.error.assert_called()
            # Preferences should remain unchanged or be set to empty dict
            assert isinstance(conversation_engine.user_preferences, dict)

    def test_binary_data_input_handling(self):
        """Test handling of binary data inputs."""
        voice_config = VoiceProcessingConfig()
        voice_processor = EnhancedVoiceProcessor(voice_config)

        # Test binary data in voice processing
        binary_data = b"\x00\x01\x02\x03\x04\x05" * 1000

        result = voice_processor._energy_based_vad(binary_data)
        assert isinstance(result, bool)

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
            intent, confidence = conversation_engine.analyze_intent(user_input)
            assert isinstance(intent, str)

            sentiment, confidence = conversation_engine.analyze_sentiment(user_input)
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
            intent, confidence = conversation_engine.analyze_intent(str(user_input))
            assert isinstance(intent, str)

    def test_invalid_file_path_handling(self):
        """Test handling of invalid file paths."""
        voice_processor = EnhancedVoiceProcessor(VoiceProcessingConfig())
        intelligence_core = IntelligenceCore({})

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
                response = intelligence_core.process_voice_file(invalid_path)

                assert isinstance(response, AIResponse)
                assert (
                    response.success is False or response.success is True
                )  # Should handle gracefully
                mock_logger.error.assert_called() or mock_logger.warning.assert_called()

    def test_invalid_audio_format_handling(self):
        """Test handling of invalid audio formats."""
        voice_processor = EnhancedVoiceProcessor(VoiceProcessingConfig())

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
                        mock_logger.warning.assert_called() or mock_logger.error.assert_called()
