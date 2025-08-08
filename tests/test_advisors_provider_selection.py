from chatty_commander.advisors.providers import build_provider, CompletionProvider, ResponsesProvider


class Cfg:
    advisors = {"llm_api_mode": "completion", "model": "m1", "provider": {"base_url": "http://x"}}


def test_build_completion_provider():
    p = build_provider(Cfg())
    assert isinstance(p, CompletionProvider)
    assert "prov:completion" in p.generate("hi")


class Cfg2:
    advisors = {"llm_api_mode": "responses", "model": "m2", "provider": {"base_url": "http://y"}}


def test_build_responses_provider():
    p = build_provider(Cfg2())
    assert isinstance(p, ResponsesProvider)
    assert "prov:responses" in p.generate("hi")


