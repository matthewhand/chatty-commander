import json
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


def test_config_general_settings_env_overrides(monkeypatch, tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(
        json.dumps(
            {
                "general_settings": {
                    "debug_mode": False,
                    "default_state": "idle",
                    "inference_framework": "onnx",
                    "start_on_boot": False,
                    "check_for_updates": True,
                }
            }
        )
    )

    monkeypatch.setenv("CHATCOMM_DEBUG", "TrUe")
    monkeypatch.setenv("CHATCOMM_DEFAULT_STATE", "computer")
    monkeypatch.setenv("CHATCOMM_INFERENCE_FRAMEWORK", "pytorch")
    monkeypatch.setenv("CHATCOMM_START_ON_BOOT", "YeS")
    monkeypatch.setenv("CHATCOMM_CHECK_FOR_UPDATES", "0")

    c = Config(config_file=str(cfg_path))

    assert c.debug_mode is True
    assert c.default_state == "computer"
    assert c.inference_framework == "pytorch"
    assert c.start_on_boot is True
    assert c.check_for_updates is False
