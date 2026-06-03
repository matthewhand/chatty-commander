"""
Error handling and fallback tests for AI modules.

Covers:
- LLM provider failure and error responses
- Voice processor degradation (transcription, noise reduction)
- ConversationEngine robustness with special inputs
"""

import builtins
from unittest.mock import Mock, patch

import numpy as np
import pytest

from chatty_commander.advisors.conversation_engine import ConversationEngine
from chatty_commander.advisors.service import (
    AdvisorMessage,
    AdvisorReply,
    AdvisorsService,
)
from chatty_commander.voice.enhanced_processor import (
    EnhancedVoiceProcessor,
    VoiceProcessingConfig,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service(provider_side_effect=None, provider_return=None):
    """Create AdvisorsService with a mocked provider."""
    provider = Mock()
    provider.model = "gpt-4"
    provider.api_mode = "completion"
    if provider_side_effect:
        provider.generate.side_effect = provider_side_effect
    elif provider_return is not None:
        provider.generate.return_value = provider_return

    config = {
        "enabled": True,
        "providers": {"openai": {"api_key": "test"}},
        "context": {
            "personas": {
                "general": {
                    "system_prompt": "You are a helpful assistant.",
                    "name": "Default Assistant",
                }
            },
            "default_persona": "general",
        },
        "commands": {},
    }

    with (
        patch("chatty_commander.advisors.service.build_provider_safe") as mock_build,
        patch("chatty_commander.llm.manager.get_global_llm_manager", return_value=None),
    ):
        mock_build.return_value = provider
        service = AdvisorsService(config)

    return service


def _make_message(text="Hello"):
    return AdvisorMessage(
        platform="discord",
        channel="test",
        user="user123",
        text=text,
        username="test_user",
    )


# ---------------------------------------------------------------------------
# LLM error / fallback tests
# ---------------------------------------------------------------------------


class TestLLMErrorHandling:
    """LLM provider failure produces an error reply (not a crash)."""

    @pytest.fixture(autouse=True)
    def _disable_llm_manager(self):
        with patch(
            "chatty_commander.llm.manager.get_global_llm_manager", return_value=None
        ):
            yield

    def test_provider_exception_returns_error_reply(self):
        """Any exception from generate() yields an 'LLM Error' reply."""
        service = _make_service(
            provider_side_effect=Exception("LLM service unavailable")
        )
        response = service.handle_message(_make_message())

        assert isinstance(response, AdvisorReply)
        assert "LLM Error" in response.reply
        assert response.model == "error"

    def test_connection_error_returns_error_reply(self):
        """ConnectionError is handled the same as a generic exception."""
        service = _make_service(
            provider_side_effect=ConnectionError("Network unreachable")
        )
        response = service.handle_message(_make_message())

        assert isinstance(response, AdvisorReply)
        assert "LLM Error" in response.reply

    def test_empty_response_returned_as_is(self):
        """An empty string from the provider is returned without error."""
        service = _make_service(provider_return="")
        response = service.handle_message(_make_message("Tell me a joke"))

        assert isinstance(response, AdvisorReply)
        assert response.reply == ""

    def test_switch_mode_directive_stripped(self):
        """SWITCH_MODE directive is processed and removed from reply."""
        service = _make_service(
            provider_return="SWITCH_MODE: work\nHere's your response."
        )
        response = service.handle_message(_make_message("Switch to work mode"))

        assert isinstance(response, AdvisorReply)
        assert "SWITCH_MODE:" not in response.reply

    def test_successful_response_passthrough(self):
        """A normal response is returned verbatim."""
        service = _make_service(provider_return="This is a test response")
        response = service.handle_message(_make_message())

        assert isinstance(response, AdvisorReply)
        assert response.reply == "This is a test response"

    def test_provider_fallback_chain(self):
        """First call fails, second succeeds — service handles the error."""
        call_count = [0]

        def fallback_chain(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Provider 1 failed")
            return "Fallback response"

        service = _make_service(provider_side_effect=fallback_chain)
        response = service.handle_message(_make_message())

        assert isinstance(response, AdvisorReply)
        assert "LLM Error" in response.reply or "Fallback response" in response.reply


# ---------------------------------------------------------------------------
# Voice processor degradation tests
# ---------------------------------------------------------------------------


class TestVoiceProcessorDegradation:
    """Voice processor degrades gracefully when dependencies are missing."""

    def test_transcription_fallback_when_engines_unavailable(self):
        """When whisper/speech_recognition are missing, transcription falls back to 'none'."""
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name in ["whisper", "speech_recognition"]:
                raise ImportError("Offline - no internet connection")
            return original_import(name, *args, **kwargs)

        builtins.__import__ = mock_import
        try:
            processor = EnhancedVoiceProcessor(VoiceProcessingConfig())

            assert processor.transcription_method == "none"
            assert processor.transcriber is None

            result = processor._transcribe_audio(np.zeros(16000, dtype=np.int16))
            assert result.text == "[Transcription not available]"
            assert result.confidence == 0.0
        finally:
            builtins.__import__ = original_import

    def test_noise_reduction_failure_falls_back_to_basic_vad(self):
        """When noise reduction init fails, basic VAD still works."""
        with patch(
            "chatty_commander.voice.enhanced_processor.EnhancedVoiceProcessor._initialize_noise_reduction"
        ) as mock_nr:
            mock_nr.side_effect = Exception("Noise reduction failed")

            config = VoiceProcessingConfig(
                sample_rate=16000,
                noise_reduction_enabled=True,
                voice_activity_detection=True,
                confidence_threshold=0.7,
            )
            processor = EnhancedVoiceProcessor(config)

            result = processor._energy_based_vad(b"\x00\x01\x02\x03")
            assert isinstance(result, bool | np.bool_)

    def test_energy_based_vad_handles_binary_data(self):
        """Energy-based VAD returns a boolean for arbitrary binary input."""
        processor = EnhancedVoiceProcessor(
            VoiceProcessingConfig(
                sample_rate=16000,
                noise_reduction_enabled=False,
                voice_activity_detection=True,
                confidence_threshold=0.7,
            )
        )
        result = processor._energy_based_vad(b"\x00\x01\x02\x03\x04\x05")
        assert isinstance(result, bool | np.bool_)


# ---------------------------------------------------------------------------
# ConversationEngine robustness
# ---------------------------------------------------------------------------


class TestConversationEngineRobustness:
    """ConversationEngine handles unusual text without crashing."""

    @pytest.mark.parametrize(
        "text, expected_intent",
        [
            ("Hello! @#$%^&*()", "greeting"),
            ("Test with \x00 null byte", "general_conversation"),
            ("Unicode: \u00f1\u00e1\u00e9\u00ed\u00f3\u00fa", "general_conversation"),
            ("SQL injection: ' OR '1'='1", "general_conversation"),
        ],
    )
    def test_special_character_intent_and_sentiment(self, text, expected_intent):
        engine = ConversationEngine({})
        assert engine.analyze_intent(text) == expected_intent
        assert engine.analyze_sentiment(text) in ("positive", "negative", "neutral")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
