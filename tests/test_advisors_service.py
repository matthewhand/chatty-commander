from chatty_commander.advisors.service import AdvisorsService, AdvisorMessage
from unittest.mock import patch, MagicMock


class DummyConfig:
    advisors = {
        "enabled": True,
        "providers": {
            "llm_api_mode": "completion",
            "model": "gpt-oss20b",
        },
        "context": {
            "personas": {
                "general": {"system_prompt": "You are helpful."},
                "discord_default": {"system_prompt": "You are a Discord bot."}
            },
            "default_persona": "general"
        }
    }


def test_advisors_service_echo_reply():
    with patch('openai.OpenAI') as mock_openai:
        mock_openai.return_value = MagicMock()
        svc = AdvisorsService(config=DummyConfig())
        msg = AdvisorMessage(platform="discord", channel="c1", user="u1", text="hello")
        reply = svc.handle_message(msg)
        assert reply is not None


def test_advisors_service_disabled_returns_notice():
    class DisabledConfig:
        advisors = {"enabled": False}

    svc = AdvisorsService(config=DisabledConfig())
    msg = AdvisorMessage(platform="slack", channel="c2", user="u2", text="ping")
    
    try:
        reply = svc.handle_message(msg)
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "not enabled" in str(e)


