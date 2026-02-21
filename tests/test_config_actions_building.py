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
from pathlib import Path

from chatty_commander.app.config import Config


def write_tmp_config(tmp_path: Path, data: dict) -> Path:
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(data), encoding="utf-8")
    return cfg_path


def test_builds_model_actions_from_commands_and_keybindings(tmp_path: Path):
    data = {
        "keybindings": {"do_paste": "ctrl+v"},
        "commands": {
            "paste": {"action": "keypress", "keys": "do_paste"},
            "call_bot": {"action": "url", "url": "{chatbot_endpoint}/run"},
            "say": {"action": "custom_message", "message": "hello"},
        },
        "api_endpoints": {"chatbot_endpoint": "http://example.test"},
        "general_settings": {"debug_mode": True},
    }
    cfg_file = write_tmp_config(tmp_path, data)

    cfg = Config.load(str(cfg_file))
    assert cfg.debug_mode is True
    # keybinding resolved
    assert cfg.model_actions["paste"] == {"keypress": "ctrl+v"}
    # url placeholder substituted
    assert cfg.model_actions["call_bot"]["url"] == "http://example.test/run"
    # message mapped to shell echo (demo representation)
    assert cfg.model_actions["say"] == {"shell": "echo hello"}


def test_builds_keypress_without_keybinding_name(tmp_path: Path):
    data = {
        "commands": {"press": {"action": "keypress", "keys": "alt+tab"}},
    }
    cfg_file = write_tmp_config(tmp_path, data)
    cfg = Config.load(str(cfg_file))
    assert cfg.model_actions["press"] == {"keypress": "alt+tab"}


def test_handles_empty_commands_safely(tmp_path: Path):
    data = {"commands": {}}
    cfg_file = write_tmp_config(tmp_path, data)
    cfg = Config.load(str(cfg_file))
    assert isinstance(cfg.model_actions, dict)
    assert cfg.model_actions == {}
