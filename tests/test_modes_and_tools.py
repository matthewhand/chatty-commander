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
from types import SimpleNamespace

from src.chatty_commander.app.config import Config
from src.chatty_commander.app.state_manager import StateManager as RealStateManager


def make_temp_config(tmp_path, data: dict) -> str:
    p = tmp_path / "temp_config.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def base_config_dict():
    return {
        "keybindings": {
            "take_screenshot": "alt+print_screen",
            "paste": "ctrl+v",
            "submit": "enter",
            "cycle_window": "alt+tab",
            "stop_typing": "ctrl+shift+;",
        },
        "commands": {
            "take_screenshot": {"action": "keypress", "keys": "take_screenshot"},
            "paste": {"action": "keypress", "keys": "paste"},
            "submit": {"action": "keypress", "keys": "submit"},
            "cycle_window": {"action": "keypress", "keys": "cycle_window"},
            "okay_stop": {"action": "keypress", "keys": "stop_typing"},
        },
        "api_endpoints": {
            "home_assistant": "http://localhost:8123/api",
            "chatbot_endpoint": "http://localhost:3100/",
        },
        "state_models": {
            "idle": ["hey_chat_tee", "hey_khum_puter", "okay_stop"],
            "computer": ["oh_kay_screenshot", "okay_stop"],
        },
        "model_paths": {
            "idle": "models-idle",
            "computer": "models-computer",
        },
        "general_settings": {"default_state": "idle", "debug_mode": True},
    }


def test_modes_wakeword_mapping_custom_mode(tmp_path, monkeypatch):
    data = base_config_dict()
    # Add a custom mode with its own wakeword
    data["modes"] = {
        "idle": {
            "wakewords": ["hey_chat_tee", "hey_khum_puter", "okay_stop"],
            "persona": None,
        },
        "focus": {
            "wakewords": ["focus_on"],
            "persona": "analyst",
            "tools": ["browser"],
        },
    }
    data["state_models"]["focus"] = ["okay_stop"]
    data["state_transitions"] = {
        "idle": {
            "hey_chat_tee": "chatty",
            "hey_khum_puter": "computer",
            "focus_on": "focus",
            "toggle_mode": "computer",
        },
        "focus": {"okay_stop": "idle"},
    }

    cfg_path = make_temp_config(tmp_path, data)
    cfg = Config(config_file=cfg_path)

    # Create StateManager with the custom config directly
    sm = RealStateManager(config=cfg)
    assert sm.current_state == "idle"

    # Trigger the custom wakeword
    new_state = sm.update_state("focus_on")
    assert new_state == "focus"
    assert sm.current_state == "focus"


def test_modes_chatty_no_wakewords_in_default_config():
    # Load default config.json in repo
    cfg = Config()
    modes = getattr(cfg, "modes", {})
    chatty = modes.get("chatty") if isinstance(modes, dict) else None
    if chatty is not None:
        assert isinstance(chatty.get("wakewords", []), list)
        assert chatty.get("wakewords", []) == []


def test_advisors_switch_mode_directive(monkeypatch):
    # Patch provider to return a switch directive string
    class DummyProvider:
        model = "test-model"
        api_mode = "completion"

        def generate(self, prompt: str, **kwargs) -> str:
            return "SWITCH_MODE:idle"

    # Patch AdvisorsService provider builder to return DummyProvider
    # Patch AdvisorsService provider builder to return DummyProvider
    import src.chatty_commander.advisors.service as svc_mod

    monkeypatch.setattr(
        svc_mod, "build_provider_safe", lambda cfg: DummyProvider(), raising=False
    )

    # Patch StateManager inside AdvisorsService to observe change_state calls
    calls = SimpleNamespace(count=0, last=None)

    class FakeSM:
        def __init__(self):
            pass

        def change_state(self, new_state: str, callback=None):
            calls.count += 1
            calls.last = new_state

    # Patch the class inside the state_manager module so runtime import picks it up
    import src.chatty_commander.app.state_manager as sm_mod2

    monkeypatch.setattr(sm_mod2, "StateManager", FakeSM, raising=True)

    from src.chatty_commander.advisors.service import AdvisorMessage, AdvisorsService

    cfg = type("Cfg", (), {"advisors": {"enabled": True, "providers": {}}})()
    svc = AdvisorsService(config=cfg)
    msg = AdvisorMessage(platform="discord", channel="c1", user="u1", text="hello")
    _ = svc.handle_message(msg)
    assert calls.count == 1
    assert calls.last == "idle"
