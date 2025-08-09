from chatty_commander.advisors.providers import build_provider_safe
from unittest.mock import patch, MagicMock


class Cfg:
    advisors = {"llm_api_mode": "completion", "model": "m1", "provider": {"base_url": "http://x"}}


def test_build_completion_provider():
    with patch('openai.OpenAI') as mock_openai:
        mock_openai.return_value = MagicMock()
        p = build_provider_safe(Cfg().advisors)
        assert p is not None


class Cfg2:
    advisors = {"llm_api_mode": "responses", "model": "m2", "provider": {"base_url": "http://y"}}


def test_build_responses_provider():
    with patch('openai.OpenAI') as mock_openai:
        mock_openai.return_value = MagicMock()
        p = build_provider_safe(Cfg2().advisors)
        assert p is not None


