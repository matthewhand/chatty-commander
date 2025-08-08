from chatty_commander.advisors.service import AdvisorsService, AdvisorMessage


class DummyConfig:
    advisors = {
        "enabled": True,
        "llm_api_mode": "completion",
        "model": "gpt-oss20b",
    }


def test_advisors_service_echo_reply():
    svc = AdvisorsService(config=DummyConfig())
    msg = AdvisorMessage(platform="discord", channel="c1", user="u1", text="hello")
    reply = svc.handle_message(msg)
    assert "advisor:gpt-oss20b/completion" in reply.text
    assert "hello" in reply.text


def test_advisors_service_disabled_returns_notice():
    class DisabledConfig:
        advisors = {"enabled": False}

    svc = AdvisorsService(config=DisabledConfig())
    msg = AdvisorMessage(platform="slack", channel="c2", user="u2", text="ping")
    reply = svc.handle_message(msg)
    assert "disabled" in reply.text


