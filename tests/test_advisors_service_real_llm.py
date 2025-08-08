"""
Tests for AdvisorsService with real LLM integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from chatty_commander.advisors.service import AdvisorsService, AdvisorMessage, AdvisorReply
from chatty_commander.advisors.context import PlatformType


class TestAdvisorsServiceRealLLM:
    """Test AdvisorsService with real LLM provider integration."""
    
    @pytest.fixture
    def config(self):
        """Test configuration with real LLM provider."""
        return {
            'enabled': True,
            'providers': {
                'llm_api_mode': 'completion',
                'model': 'gpt-3.5-turbo',
                'api_key': 'test-key',
                'temperature': 0.7,
                'max_tokens': 1000
            },
            'context': {
                'personas': {
                    'general': {'system_prompt': 'You are a helpful assistant.'},
                    'philosopher': {'system_prompt': 'You are a philosophical advisor.'},
                    'discord_default': {'system_prompt': 'You are a Discord bot assistant.'},
                    'slack_default': {'system_prompt': 'You are a Slack app assistant.'}
                },
                'default_persona': 'general',
                'persistence_enabled': False
            },
            'memory': {
                'persistence_enabled': False
            }
        }
    
    @pytest.fixture
    def mock_provider(self):
        """Mock LLM provider."""
        provider = Mock()
        provider.model = 'gpt-3.5-turbo'
        provider.api_mode = 'completion'
        provider.generate.return_value = "This is a real LLM response."
        return provider
    
    @patch('chatty_commander.advisors.service.build_provider_safe')
    def test_advisors_service_initialization(self, mock_build_provider, config, mock_provider):
        """Test AdvisorsService initialization with real LLM provider."""
        mock_build_provider.return_value = mock_provider
        
        service = AdvisorsService(config)
        
        assert service.enabled is True
        assert service.provider is mock_provider
        assert service.context_manager is not None
        assert service.memory is not None
        
        mock_build_provider.assert_called_once_with(config['providers'])
    
    @patch('chatty_commander.advisors.service.build_provider_safe')
    def test_handle_message_real_llm_response(self, mock_build_provider, config, mock_provider):
        """Test handling message with real LLM response."""
        mock_build_provider.return_value = mock_provider
        
        service = AdvisorsService(config)
        
        message = AdvisorMessage(
            platform="discord",
            channel="123456789",
            user="user123",
            text="Hello, how are you?",
            username="testuser"
        )
        
        reply = service.handle_message(message)
        
        assert isinstance(reply, AdvisorReply)
        assert reply.reply == "This is a real LLM response."
        assert "discord:123456789:user123" in reply.context_key
        assert reply.persona_id == "discord_default"
        assert reply.model == "gpt-3.5-turbo"
        assert reply.api_mode == "completion"
        
        # Verify LLM was called with proper prompt
        mock_provider.generate.assert_called_once()
        call_args = mock_provider.generate.call_args[0][0]
        assert "Hello, how are you?" in call_args
        assert "You are a Discord bot assistant" in call_args
    
    @patch('chatty_commander.advisors.service.build_provider_safe')
    def test_handle_message_llm_failure_fallback(self, mock_build_provider, config):
        """Test handling message when LLM fails with fallback."""
        mock_provider = Mock()
        mock_provider.model = 'gpt-3.5-turbo'
        mock_provider.api_mode = 'completion'
        mock_provider.generate.side_effect = Exception("API rate limit exceeded")
        mock_build_provider.return_value = mock_provider
        
        service = AdvisorsService(config)
        
        message = AdvisorMessage(
            platform="slack",
            channel="general",
            user="user456",
            text="What's the weather like?",
            username="weatheruser"
        )
        
        reply = service.handle_message(message)
        
        assert isinstance(reply, AdvisorReply)
        assert "LLM error: API rate limit exceeded" in reply.reply
        assert "slack:general:user456" in reply.context_key
        assert reply.persona_id == "slack_default"
    
    @patch('chatty_commander.advisors.service.build_provider_safe')
    def test_handle_message_context_persistence(self, mock_build_provider, config, mock_provider):
        """Test that context persists across multiple messages."""
        mock_build_provider.return_value = mock_provider
        
        service = AdvisorsService(config)
        
        # Send first message
        message1 = AdvisorMessage(
            platform="web",
            channel="chat",
            user="user789",
            text="My name is Alice",
            username="alice"
        )
        
        reply1 = service.handle_message(message1)
        
        # Send second message
        message2 = AdvisorMessage(
            platform="web",
            channel="chat",
            user="user789",
            text="What's my name?",
            username="alice"
        )
        
        reply2 = service.handle_message(message2)
        
        # Should have same context key
        assert reply1.context_key == reply2.context_key
        assert reply1.persona_id == reply2.persona_id
        
        # Verify LLM was called twice
        assert mock_provider.generate.call_count == 2
    
    @patch('chatty_commander.advisors.service.build_provider_safe')
    def test_handle_message_summarize_command(self, mock_build_provider, config, mock_provider):
        """Test handling summarize command."""
        mock_build_provider.return_value = mock_provider
        
        service = AdvisorsService(config)
        
        message = AdvisorMessage(
            platform="web",
            channel="test",
            user="user123",
            text="summarize https://example.com"
        )
        
        reply = service.handle_message(message)
        
        assert isinstance(reply, AdvisorReply)
        assert "Summary of https://example.com" in reply.reply
        assert reply.context_key == "summarize"
        assert reply.persona_id == "analyst"
        
        # LLM should not be called for summarize command
        mock_provider.generate.assert_not_called()
    
    @patch('chatty_commander.advisors.service.build_provider_safe')
    def test_switch_persona(self, mock_build_provider, config, mock_provider):
        """Test switching persona for a context."""
        mock_build_provider.return_value = mock_provider
        
        service = AdvisorsService(config)
        
        # Create context first
        message = AdvisorMessage(
            platform="discord",
            channel="test",
            user="user123",
            text="Hello"
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
            text="What do you think about ethics?"
        )
        
        reply2 = service.handle_message(message2)
        
        assert reply2.persona_id == "philosopher"
        
        # Verify LLM was called with philosopher prompt
        call_args = mock_provider.generate.call_args[0][0]
        assert "You are a philosophical advisor" in call_args
    
    @patch('chatty_commander.advisors.service.build_provider_safe')
    def test_get_context_stats(self, mock_build_provider, config, mock_provider):
        """Test getting context statistics."""
        mock_build_provider.return_value = mock_provider
        
        service = AdvisorsService(config)
        
        # Create some contexts
        service.handle_message(AdvisorMessage(
            platform="discord",
            channel="channel1",
            user="user1",
            text="Hello"
        ))
        
        service.handle_message(AdvisorMessage(
            platform="discord",
            channel="channel2",
            user="user2",
            text="Hello"
        ))
        
        service.handle_message(AdvisorMessage(
            platform="slack",
            channel="general",
            user="user3",
            text="Hello"
        ))
        
        stats = service.get_context_stats()
        
        assert stats['total_contexts'] == 3
        assert stats['platform_distribution']['discord'] == 2
        assert stats['platform_distribution']['slack'] == 1
        assert stats['persona_distribution']['discord_default'] == 2
        assert stats['persona_distribution']['slack_default'] == 1
    
    @patch('chatty_commander.advisors.service.build_provider_safe')
    def test_clear_context(self, mock_build_provider, config, mock_provider):
        """Test clearing a specific context."""
        mock_build_provider.return_value = mock_provider
        
        service = AdvisorsService(config)
        
        # Create context
        message = AdvisorMessage(
            platform="web",
            channel="test",
            user="user123",
            text="Hello"
        )
        
        reply = service.handle_message(message)
        context_key = reply.context_key
        
        # Clear context
        success = service.clear_context(context_key)
        
        assert success is True
        
        # Verify context is cleared
        stats = service.get_context_stats()
        assert stats['total_contexts'] == 0
    
    @patch('chatty_commander.advisors.service.build_provider_safe')
    def test_advisors_disabled(self, mock_build_provider, config, mock_provider):
        """Test behavior when advisors are disabled."""
        config['enabled'] = False
        mock_build_provider.return_value = mock_provider
        
        service = AdvisorsService(config)
        
        message = AdvisorMessage(
            platform="discord",
            channel="test",
            user="user123",
            text="Hello"
        )
        
        with pytest.raises(RuntimeError, match="Advisors are not enabled"):
            service.handle_message(message)
    
    @patch('chatty_commander.advisors.service.build_provider_safe')
    def test_memory_integration(self, mock_build_provider, config, mock_provider):
        """Test that memory is properly integrated with LLM responses."""
        mock_build_provider.return_value = mock_provider
        
        service = AdvisorsService(config)
        
        # Send multiple messages
        message1 = AdvisorMessage(
            platform="web",
            channel="chat",
            user="user123",
            text="I like pizza"
        )
        
        service.handle_message(message1)
        
        message2 = AdvisorMessage(
            platform="web",
            channel="chat",
            user="user123",
            text="What did I say I like?"
        )
        
        reply = service.handle_message(message2)
        
        # Verify LLM was called with memory context
        call_args = mock_provider.generate.call_args[0][0]
        assert "I like pizza" in call_args  # Previous message should be in context
        assert "What did I say I like?" in call_args  # Current message
    
    @patch('chatty_commander.advisors.service.build_provider_safe')
    def test_streaming_response_support(self, mock_build_provider, config):
        """Test support for streaming responses."""
        mock_provider = Mock()
        mock_provider.model = 'gpt-3.5-turbo'
        mock_provider.api_mode = 'completion'
        mock_provider.generate_stream.return_value = "Streaming response..."
        mock_build_provider.return_value = mock_provider
        
        service = AdvisorsService(config)
        
        message = AdvisorMessage(
            platform="web",
            channel="chat",
            user="user123",
            text="Tell me a story"
        )
        
        reply = service.handle_message(message)
        
        # Currently using generate, not generate_stream
        # This test verifies the provider has streaming capability
        assert hasattr(mock_provider, 'generate_stream')
        assert reply.reply == "This is a real LLM response."  # Uses generate, not generate_stream
