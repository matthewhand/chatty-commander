"""
Tests for real LLM provider implementations.
"""

from unittest.mock import Mock, patch

import pytest

from chatty_commander.advisors.providers import (
    CompletionProvider,
    FallbackProvider,
    ResponsesProvider,
    build_provider,
    build_provider_safe,
)


class TestCompletionProvider:
    """Test CompletionProvider implementation."""

    @pytest.fixture
    def config(self):
        """Test configuration."""
        return {
            'model': 'gpt-3.5-turbo',
            'api_mode': 'completion',
            'api_key': 'test-key',
            'base_url': 'https://api.openai.com/v1',
            'temperature': 0.7,
            'max_tokens': 1000,
            'max_retries': 2,
            'timeout': 30,
        }

    @patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True)
    @patch('chatty_commander.advisors.providers.Agent')
    def test_completion_provider_initialization(self, mock_agent, config):
        """Test CompletionProvider initialization."""
        mock_client = Mock()
        mock_agent.return_value = mock_client

        provider = CompletionProvider(config)

        assert provider.model == 'gpt-3.5-turbo'
        assert provider.api_mode == 'completion'
        assert provider.api_key == 'test-key'
        assert provider.base_url == 'https://api.openai.com/v1'
        assert provider.temperature == 0.7
        assert provider.max_tokens == 1000

        mock_agent.assert_called_once()

    @patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True)
    @patch('chatty_commander.advisors.providers.Agent')
    def test_completion_provider_generate_success(self, mock_agent, config):
        """Test successful generation."""
        mock_client = Mock()
        mock_client.chat.return_value = "Test response"
        mock_agent.return_value = mock_client

        provider = CompletionProvider(config)
        result = provider.generate("Test prompt")

        assert result == "Test response"
        mock_client.chat.assert_called_once_with("Test prompt")

    @patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True)
    @patch('chatty_commander.advisors.providers.Agent')
    def test_completion_provider_generate_retry(self, mock_agent, config):
        """Test generation with retry logic."""
        mock_client = Mock()
        mock_client.chat.side_effect = [Exception("First failure"), "Success"]
        mock_agent.return_value = mock_client

        provider = CompletionProvider(config)
        result = provider.generate("Test prompt")

        assert result == "Success"
        assert mock_client.chat.call_count == 2

    @patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True)
    @patch('chatty_commander.advisors.providers.Agent')
    def test_completion_provider_generate_stream(self, mock_agent, config):
        """Test streaming generation (fallback to single chat)."""
        mock_client = Mock()
        mock_client.chat.return_value = "Hello World"
        mock_agent.return_value = mock_client

        provider = CompletionProvider(config)
        result = provider.generate_stream("Test prompt")

        assert result == "Hello World"

    @patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True)
    @patch('chatty_commander.advisors.providers.Agent')
    def test_completion_provider_health_check(self, mock_agent, config):
        """Test health check functionality."""
        mock_client = Mock()
        mock_client.chat.return_value = "Test"
        mock_agent.return_value = mock_client

        provider = CompletionProvider(config)
        result = provider.health_check()

        assert result is True

    @patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True)
    @patch('chatty_commander.advisors.providers.Agent')
    def test_completion_provider_health_check_failure(self, mock_agent, config):
        """Test health check failure."""
        mock_client = Mock()
        mock_client.chat.side_effect = Exception("API error")
        mock_agent.return_value = mock_client

        provider = CompletionProvider(config)
        result = provider.health_check()

        assert result is False


class TestResponsesProvider:
    """Test ResponsesProvider implementation."""

    @pytest.fixture
    def config(self):
        """Test configuration."""
        return {
            'model': 'gpt-4',
            'api_mode': 'responses',
            'api_key': 'test-key',
            'base_url': 'https://api.openai.com/v1',
            'temperature': 0.8,
            'max_tokens': 1500,
            'max_retries': 2,
            'timeout': 30,
        }

    @patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True)
    @patch('chatty_commander.advisors.providers.Agent')
    def test_responses_provider_initialization(self, mock_agent, config):
        """Test ResponsesProvider initialization."""
        mock_client = Mock()
        mock_agent.return_value = mock_client

        provider = ResponsesProvider(config)

        assert provider.model == 'gpt-4'
        assert provider.api_mode == 'responses'
        assert provider.temperature == 0.8
        assert provider.max_tokens == 1500

    @patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True)
    @patch('chatty_commander.advisors.providers.Agent')
    def test_responses_provider_generate_success(self, mock_agent, config):
        """Test successful generation with responses API."""
        mock_client = Mock()
        mock_client.chat.return_value = "Responses API response"
        mock_agent.return_value = mock_client

        provider = ResponsesProvider(config)
        result = provider.generate("Test prompt")

        assert result == "Responses API response"
        mock_client.chat.assert_called_once_with("Test prompt")


class TestFallbackProvider:
    """Test FallbackProvider implementation."""

    @pytest.fixture
    def config(self):
        """Test configuration with fallbacks."""
        return {
            'model': 'gpt-3.5-turbo',
            'primary_api_mode': 'completion',
            'fallbacks': [{'model': 'gpt-4', 'api_mode': 'responses', 'api_key': 'fallback-key'}],
            'api_key': 'primary-key',
            'max_retries': 1,
            'timeout': 30,
        }

    @patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True)
    @patch('chatty_commander.advisors.providers.CompletionProvider')
    @patch('chatty_commander.advisors.providers.ResponsesProvider')
    def test_fallback_provider_initialization(self, mock_responses, mock_completion, config):
        """Test FallbackProvider initialization."""
        mock_completion.return_value = Mock()
        mock_responses.return_value = Mock()

        provider = FallbackProvider(config)

        assert len(provider.providers) == 2
        mock_completion.assert_called_once()
        mock_responses.assert_called_once()

    @patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True)
    @patch('chatty_commander.advisors.providers.CompletionProvider')
    @patch('chatty_commander.advisors.providers.ResponsesProvider')
    def test_fallback_provider_primary_success(self, mock_responses, mock_completion, config):
        """Test fallback provider with primary success."""
        mock_primary = Mock()
        mock_primary.generate.return_value = "Primary success"
        mock_completion.return_value = mock_primary

        mock_fallback = Mock()
        mock_fallback.generate.return_value = "Fallback success"
        mock_responses.return_value = mock_fallback

        provider = FallbackProvider(config)
        result = provider.generate("Test prompt")

        assert result == "Primary success"
        mock_primary.generate.assert_called_once_with("Test prompt")
        mock_fallback.generate.assert_not_called()

    @patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True)
    @patch('chatty_commander.advisors.providers.CompletionProvider')
    @patch('chatty_commander.advisors.providers.ResponsesProvider')
    def test_fallback_provider_fallback_success(self, mock_responses, mock_completion, config):
        """Test fallback provider with fallback success."""
        mock_primary = Mock()
        mock_primary.generate.side_effect = Exception("Primary failed")
        mock_completion.return_value = mock_primary

        mock_fallback = Mock()
        mock_fallback.generate.return_value = "Fallback success"
        mock_responses.return_value = mock_fallback

        provider = FallbackProvider(config)
        result = provider.generate("Test prompt")

        assert result == "Fallback success"
        mock_primary.generate.assert_called_once()
        mock_fallback.generate.assert_called_once()

    @patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True)
    @patch('chatty_commander.advisors.providers.CompletionProvider')
    @patch('chatty_commander.advisors.providers.ResponsesProvider')
    def test_fallback_provider_all_fail(self, mock_responses, mock_completion, config):
        """Test fallback provider when all providers fail."""
        mock_primary = Mock()
        mock_primary.generate.side_effect = Exception("Primary failed")
        mock_completion.return_value = mock_primary

        mock_fallback = Mock()
        mock_fallback.generate.side_effect = Exception("Fallback failed")
        mock_responses.return_value = mock_fallback

        provider = FallbackProvider(config)
        result = provider.generate("Test prompt")

        assert "Error: All providers failed" in result


class TestProviderBuilder:
    """Test provider builder functions."""

    def test_build_provider_completion(self):
        """Test building completion provider."""
        config = {'llm_api_mode': 'completion', 'model': 'gpt-3.5-turbo', 'api_key': 'test-key'}

        with patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True):
            with patch('chatty_commander.advisors.providers.CompletionProvider') as mock_completion:
                mock_completion.return_value = Mock()
                provider = build_provider(config)

                assert provider is not None
                mock_completion.assert_called_once()

    def test_build_provider_responses(self):
        """Test building responses provider."""
        config = {'llm_api_mode': 'responses', 'model': 'gpt-4', 'api_key': 'test-key'}

        with patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True):
            with patch('chatty_commander.advisors.providers.ResponsesProvider') as mock_responses:
                mock_responses.return_value = Mock()
                provider = build_provider(config)

                assert provider is not None
                mock_responses.assert_called_once()

    def test_build_provider_fallback(self):
        """Test building fallback provider."""
        config = {
            'llm_api_mode': 'completion',
            'model': 'gpt-3.5-turbo',
            'api_key': 'test-key',
            'fallbacks': [{'model': 'gpt-4', 'api_mode': 'responses', 'api_key': 'fallback-key'}],
        }

        with patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True):
            with patch('chatty_commander.advisors.providers.FallbackProvider') as mock_fallback:
                mock_fallback.return_value = Mock()
                provider = build_provider(config)

                assert provider is not None
                mock_fallback.assert_called_once()

    def test_build_provider_invalid_mode(self):
        """Test building provider with invalid API mode."""
        config = {'llm_api_mode': 'invalid', 'model': 'gpt-3.5-turbo'}

        with patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True):
            with pytest.raises(ValueError, match="Unknown API mode"):
                build_provider(config)

    def test_build_provider_safe_without_openai(self):
        """Test safe provider builder without openai-agents SDK."""
        config = {'llm_api_mode': 'completion', 'model': 'gpt-3.5-turbo'}

        with patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', False):
            provider = build_provider_safe(config)

            assert provider is not None
            assert hasattr(provider, 'generate')
            assert hasattr(provider, 'generate_stream')

    def test_build_provider_safe_with_openai(self):
        """Test safe provider builder with openai-agents SDK."""
        config = {'llm_api_mode': 'completion', 'model': 'gpt-3.5-turbo', 'api_key': 'test-key'}

        with patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True):
            with patch('chatty_commander.advisors.providers.build_provider') as mock_build:
                mock_build.return_value = Mock()
                provider = build_provider_safe(config)

                assert provider is not None
                mock_build.assert_called_once_with(config)


class TestProviderIntegration:
    """Test provider integration with real scenarios."""

    @patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True)
    @patch('chatty_commander.advisors.providers.Agent')
    def test_provider_with_custom_parameters(self, mock_agent):
        """Test provider with custom generation parameters."""
        config = {
            'model': 'gpt-3.5-turbo',
            'api_mode': 'completion',
            'api_key': 'test-key',
            'temperature': 0.9,
            'max_tokens': 500,
        }

        mock_client = Mock()
        mock_client.chat.return_value = "Custom response"

        with patch('chatty_commander.advisors.providers.Agent', return_value=mock_client):
            provider = CompletionProvider(config)
            result = provider.generate("Test prompt", temperature=0.5, max_tokens=200)

            assert result == "Custom response"
            mock_client.chat.assert_called_once_with("Test prompt")

    @patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True)
    @patch('chatty_commander.advisors.providers.Agent')
    def test_provider_with_local_model(self, mock_agent):
        """Test provider with local model configuration."""
        config = {
            'model': 'gpt-oss20b',
            'api_mode': 'completion',
            'api_key': 'test-key',
            'base_url': 'http://localhost:8080/v1',
        }

        mock_client = Mock()
        mock_client.chat.return_value = "Local model response"

        with patch(
            'chatty_commander.advisors.providers.Agent', return_value=mock_client
        ) as agent_ctor:
            provider = CompletionProvider(config)
            result = provider.generate("Test prompt")

            assert result == "Local model response"
            # Verify base_url was passed to Agent constructor
            assert agent_ctor.called
            kwargs = agent_ctor.call_args.kwargs
            assert kwargs.get('base_url') == 'http://localhost:8080/v1'
