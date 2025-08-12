import os

from chatty_commander.app.config import Config


def test_config_env_endpoint_overrides(monkeypatch, tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{}")

    monkeypatch.setenv("CHATBOT_ENDPOINT", "http://override.local/")
    monkeypatch.setenv("HOME_ASSISTANT_ENDPOINT", "http://ha.local/api")

    c = Config(config_file=str(cfg_path))
    assert c.api_endpoints["chatbot_endpoint"] == "http://override.local/"
    assert c.api_endpoints["home_assistant"] == "http://ha.local/api"
