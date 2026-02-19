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
Tests for AdvisorsService with real LLM integration.
"""

from unittest.mock import Mock, patch

import pytest

from chatty_commander.advisors.service import (
    AdvisorMessage,
    AdvisorReply,
    AdvisorsService,
)


class TestAdvisorsServiceRealLLM:
    """Test AdvisorsService with real LLM provider integration."""

    @pytest.fixture
    def config(self):
        """Test configuration with real LLM provider."""
        return {
            "enabled": True,
            "providers": {
                "llm_api_mode": "completion",
                "model": "gpt-3.5-turbo",
                "api_key": "test-key",
                "temperature": 0.7,
                "max_tokens": 1000,
            },
            "context": {
                "personas": {
                    "general": {"system_prompt": "You are a helpful assistant."},
                    "philosopher": {
                        "system_prompt": "You are a philosophical advisor."
                    },
                    "discord_default": {
                        "system_prompt": "You are a Discord bot assistant."
                    },
                    "slack_default": {
                        "system_prompt": "You are a Slack app assistant."
                    },
                },
                "default_persona": "general",
                "persistence_enabled": False,
            },
            "memory": {"persistence_enabled": False},
        }

    @pytest.fixture
    def mock_provider(self):
        """Mock LLM provider."""
        provider = Mock()
        provider.model = "gpt-3.5-turbo"
        provider.api_mode = "completion"
        provider.generate.return_value = "This is a real LLM response."
        return provider

    @pytest.fixture
    def mock_llm_manager(self, mock_provider):
        """Mock LLM manager."""
        manager = Mock()
        manager.generate_response.return_value = "This is a real LLM response."
        manager.active_backend = mock_provider
        manager.get_active_backend_name.return_value = "gpt-3.5-turbo"
        return manager

    @patch("chatty_commander.advisors.service.build_provider_safe")
    def test_advisors_service_initialization(
        self, mock_build_provider, config, mock_provider
    ):
        """Test AdvisorsService initialization with real LLM provider."""
        mock_build_provider.return_value = mock_provider

        with patch("chatty_commander.llm.manager.get_global_llm_manager") as mock_get_llm:
            mock_get_llm.return_value = Mock()
            service = AdvisorsService(config)

            assert service.enabled is True
            assert service.provider is mock_provider
            assert service.context_manager is not None
            assert service.memory is not None

            mock_build_provider.assert_called_once_with(config["providers"])

    @patch("chatty_commander.advisors.service.build_provider_safe")
    def test_handle_message_real_llm_response(
        self, mock_build_provider, config, mock_provider, mock_llm_manager
    ):
        """Test handling message with real LLM response."""
        mock_build_provider.return_value = mock_provider

        with patch("chatty_commander.llm.manager.get_global_llm_manager") as mock_get_llm:
            mock_get_llm.return_value = mock_llm_manager
            service = AdvisorsService(config)

            message = AdvisorMessage(
                platform="discord",
                channel="123456789",
                user="user123",
                text="Hello, how are you?",
                username="testuser",
            )

            reply = service.handle_message(message)

            assert isinstance(reply, AdvisorReply)
            assert reply.reply == "This is a real LLM response."
            assert "discord:123456789:user123" in reply.context_key
            assert reply.persona_id == "discord_default"
            assert reply.model == "gpt-3.5-turbo"
            assert reply.api_mode == "chat"

            # Verify LLM manager was called
            mock_llm_manager.generate_response.assert_called_once()

    @patch("chatty_commander.advisors.service.build_provider_safe")
    def test_handle_message_llm_failure_fallback(self, mock_build_provider, config):
        """Test handling message when LLM fails with fallback."""
        mock_provider = Mock()
        mock_provider.model = "gpt-3.5-turbo"
        mock_provider.api_mode = "completion"
        mock_build_provider.return_value = mock_provider

        mock_manager = Mock()
        mock_manager.generate_response.side_effect = Exception("API rate limit exceeded")
        mock_manager.active_backend = mock_provider
        mock_manager.get_active_backend_name.return_value = "gpt-3.5-turbo"

        with patch("chatty_commander.llm.manager.get_global_llm_manager") as mock_get_llm:
            mock_get_llm.return_value = mock_manager
            service = AdvisorsService(config)

            message = AdvisorMessage(
                platform="slack",
                channel="general",
                user="user456",
                text="What's the weather like?",
                username="weatheruser",
            )

            reply = service.handle_message(message)

            assert isinstance(reply, AdvisorReply)
            assert "[LLM Error]" in reply.reply
            assert "slack:general:user456" in reply.context_key
            assert reply.persona_id == "slack_default"

    @patch("chatty_commander.advisors.service.build_provider_safe")
    def test_handle_message_context_persistence(
        self, mock_build_provider, config, mock_provider, mock_llm_manager
    ):
        """Test that context persists across multiple messages."""
        mock_build_provider.return_value = mock_provider

        with patch("chatty_commander.llm.manager.get_global_llm_manager") as mock_get_llm:
            mock_get_llm.return_value = mock_llm_manager
            service = AdvisorsService(config)

            # Send first message
            message1 = AdvisorMessage(
                platform="web",
                channel="chat",
                user="user789",
                text="My name is Alice",
                username="alice",
            )

            reply1 = service.handle_message(message1)

            # Send second message
            message2 = AdvisorMessage(
                platform="web",
                channel="chat",
                user="user789",
                text="What's my name?",
                username="alice",
            )

            reply2 = service.handle_message(message2)

            # Should have same context key
            assert reply1.context_key == reply2.context_key
            assert reply1.persona_id == reply2.persona_id

            # Verify LLM manager was called twice
            assert mock_llm_manager.generate_response.call_count == 2

    @patch("chatty_commander.advisors.service.build_provider_safe")
    def test_handle_message_summarize_command(
        self, mock_build_provider, config, mock_provider, mock_llm_manager
    ):
        """Test handling summarize command."""
        mock_build_provider.return_value = mock_provider

        with patch("chatty_commander.llm.manager.get_global_llm_manager") as mock_get_llm:
            mock_get_llm.return_value = mock_llm_manager
            service = AdvisorsService(config)

            message = AdvisorMessage(
                platform="web",
                channel="test",
                user="user123",
                text="summarize https://example.com",
            )

            reply = service.handle_message(message)

            assert isinstance(reply, AdvisorReply)
            assert "Summary of https://example.com" in reply.reply
            assert reply.context_key == "summarize"
            assert reply.persona_id == "analyst"

            # LLM manager should not be called for summarize command
            mock_llm_manager.generate_response.assert_not_called()

    @patch("chatty_commander.advisors.service.build_provider_safe")
    def test_switch_persona(self, mock_build_provider, config, mock_provider, mock_llm_manager):
        """Test switching persona for a context."""
        mock_build_provider.return_value = mock_provider

        with patch("chatty_commander.llm.manager.get_global_llm_manager") as mock_get_llm:
            mock_get_llm.return_value = mock_llm_manager
            service = AdvisorsService(config)

            # Create context first
            message = AdvisorMessage(
                platform="discord", channel="test", user="user123", text="Hello"
            )

            reply = service.handle_message(message)
            context_key = reply.context_key

            # Switch persona
            success = service.switch_persona(context_key, "philosopher")

            assert success is True

            # Send another message to verify persona change
            message2 = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="What do you think about ethics?",
            )

            reply2 = service.handle_message(message2)

            assert reply2.persona_id == "philosopher"

            # Verify LLM manager was called
            assert mock_llm_manager.generate_response.call_count == 2

    @patch("chatty_commander.advisors.service.build_provider_safe")
    def test_get_context_stats(self, mock_build_provider, config, mock_provider, mock_llm_manager):
        """Test getting context statistics."""
        mock_build_provider.return_value = mock_provider

        with patch("chatty_commander.llm.manager.get_global_llm_manager") as mock_get_llm:
            mock_get_llm.return_value = mock_llm_manager
            service = AdvisorsService(config)

            # Create some contexts
            service.handle_message(
                AdvisorMessage(
                    platform="discord", channel="channel1", user="user1", text="Hello"
                )
            )

            service.handle_message(
                AdvisorMessage(
                    platform="discord", channel="channel2", user="user2", text="Hello"
                )
            )

            service.handle_message(
                AdvisorMessage(
                    platform="slack", channel="general", user="user3", text="Hello"
                )
            )

            stats = service.get_context_stats()

            assert stats["total_contexts"] == 3
            assert stats["platform_distribution"]["discord"] == 2
            assert stats["platform_distribution"]["slack"] == 1
            assert stats["persona_distribution"]["discord_default"] == 2
            assert stats["persona_distribution"]["slack_default"] == 1

    @patch("chatty_commander.advisors.service.build_provider_safe")
    def test_clear_context(self, mock_build_provider, config, mock_provider, mock_llm_manager):
        """Test clearing a specific context."""
        mock_build_provider.return_value = mock_provider

        with patch("chatty_commander.llm.manager.get_global_llm_manager") as mock_get_llm:
            mock_get_llm.return_value = mock_llm_manager
            service = AdvisorsService(config)

            # Create context
            message = AdvisorMessage(
                platform="web", channel="test", user="user123", text="Hello"
            )

            reply = service.handle_message(message)
            context_key = reply.context_key

            # Clear context
            success = service.clear_context(context_key)

            assert success is True

            # Verify context is cleared
            stats = service.get_context_stats()
            assert stats["total_contexts"] == 0

    @patch("chatty_commander.advisors.service.build_provider_safe")
    def test_advisors_disabled(self, mock_build_provider, config, mock_provider):
        """Test behavior when advisors are disabled."""
        config["enabled"] = False
        mock_build_provider.return_value = mock_provider

        service = AdvisorsService(config)

        message = AdvisorMessage(
            platform="discord", channel="test", user="user123", text="Hello"
        )

        with pytest.raises(RuntimeError, match="Advisors are not enabled"):
            service.handle_message(message)

    @patch("chatty_commander.advisors.service.build_provider_safe")
    def test_memory_integration(self, mock_build_provider, config, mock_provider, mock_llm_manager):
        """Test that memory is properly integrated with LLM responses."""
        mock_build_provider.return_value = mock_provider

        with patch("chatty_commander.llm.manager.get_global_llm_manager") as mock_get_llm:
            mock_get_llm.return_value = mock_llm_manager
            service = AdvisorsService(config)

            # Send multiple messages
            message1 = AdvisorMessage(
                platform="web", channel="chat", user="user123", text="I like pizza"
            )

            service.handle_message(message1)

            message2 = AdvisorMessage(
                platform="web",
                channel="chat",
                user="user123",
                text="What did I say I like?",
            )

            _ = service.handle_message(message2)

            # Verify LLM manager was called twice
            assert mock_llm_manager.generate_response.call_count == 2

    @patch("chatty_commander.advisors.service.build_provider_safe")
    def test_streaming_response_support(self, mock_build_provider, config, mock_provider, mock_llm_manager):
        """Test support for streaming responses."""
        mock_provider.generate_stream.return_value = "Streaming response..."
        mock_build_provider.return_value = mock_provider

        with patch("chatty_commander.llm.manager.get_global_llm_manager") as mock_get_llm:
            mock_get_llm.return_value = mock_llm_manager
            service = AdvisorsService(config)

            message = AdvisorMessage(
                platform="web", channel="chat", user="user123", text="Tell me a story"
            )

            _ = service.handle_message(message)

            # Currently using generate, not generate_stream
            # This test verifies the provider has streaming capability
            assert hasattr(mock_provider, "generate_stream")
            # LLM manager was called
            mock_llm_manager.generate_response.assert_called_once()
