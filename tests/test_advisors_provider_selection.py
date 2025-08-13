from unittest.mock import Mock, patch

from chatty_commander.advisors.providers import build_provider_safe


def test_build_provider_safe_without_sdk():
    """When SDK is unavailable, we should get a stub provider."""
    config = {'llm_api_mode': 'completion', 'model': 'gpt-3.5-turbo'}

    with patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', False):
        provider = build_provider_safe(config)

        assert provider is not None
        assert hasattr(provider, 'generate')
        assert hasattr(provider, 'generate_stream')


def test_build_provider_safe_with_sdk_and_key():
    """When SDK is available and API key is present, use build_provider."""
    config = {'llm_api_mode': 'responses', 'model': 'gpt-4', 'api_key': 'test-key'}

    with patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True):
        with patch('chatty_commander.advisors.providers.build_provider') as mock_build:
            mock_build.return_value = Mock()
            provider = build_provider_safe(config)

            assert provider is not None
            mock_build.assert_called_once_with(config)


def test_build_provider_safe_without_key():
    """When API key is missing, use stub provider even if SDK is present."""
    config = {'llm_api_mode': 'completion', 'model': 'gpt-3.5-turbo'}

    with patch('chatty_commander.advisors.providers.AGENTS_AVAILABLE', True):
        provider = build_provider_safe(config)

        assert provider is not None
        assert hasattr(provider, 'generate')
        assert hasattr(provider, 'generate_stream')
