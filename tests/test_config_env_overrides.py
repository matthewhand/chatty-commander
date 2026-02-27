# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json

from chatty_commander.app.config import Config


def test_config_env_endpoint_overrides(monkeypatch, tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{}")

    monkeypatch.setenv("CHATBOT_ENDPOINT", "http://override.local/")
    monkeypatch.setenv("HOME_ASSISTANT_ENDPOINT", "http://ha.local/api")

    c = Config(config_file=str(cfg_path))
    assert c.api_endpoints["chatbot_endpoint"] == "http://override.local/"
    assert c.api_endpoints["home_assistant"] == "http://ha.local/api"


def test_config_env_audio_overrides(monkeypatch, tmp_path):
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


def test_config_env_bridge_token_overrides(monkeypatch, tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{}")

    # Test CHATCOMM_BRIDGE_TOKEN
    monkeypatch.setenv("CHATCOMM_BRIDGE_TOKEN", "token1")
    c = Config(config_file=str(cfg_path))
    assert c.bridge_token == "token1"
    assert c.web_server["bridge_token"] == "token1"

    # Test ADVISORS_BRIDGE_TOKEN (has priority due to loop order)
    monkeypatch.setenv("ADVISORS_BRIDGE_TOKEN", "token2")
    c = Config(config_file=str(cfg_path))
    assert c.bridge_token == "token2"
    assert c.web_server["bridge_token"] == "token2"
