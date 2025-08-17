from chatty_commander.advisors.service import AdvisorMessage, AdvisorsService


def test_advisors_happy_path_with_stub_provider(monkeypatch):
    # Configure advisors enabled with stub provider (no API key)
    cfg = {
        "enabled": True,
        "providers": {"model": "gpt-oss20b", "api_mode": "completion"},
        "memory": {"persistence_enabled": False},
    }

    svc = AdvisorsService(cfg)
    msg = AdvisorMessage(platform="discord", channel="c1", user="u1", text="hello world")
    reply = svc.handle_message(msg)

    assert reply.reply.startswith("advisor:gpt-oss20b/completion") or "hello world" in reply.reply
    assert reply.model == svc.provider.model
    assert reply.api_mode == svc.provider.api_mode

    # Follow-up: persona switch path returns bool
    assert isinstance(svc.switch_persona(reply.context_key, "default"), bool)
