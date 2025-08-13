import pytest

from chatty_commander.app.config import Config
from chatty_commander.app.state_manager import StateManager


class TestStateManager:
    def test_initial_state(self):
        sm = StateManager()
        assert sm.current_state == "idle"
        assert sm.get_active_models() == sm.config.state_models.get("idle", [])

    def test_state_change(self):
        sm = StateManager()
        sm.change_state("chatty")
        assert sm.current_state == "chatty"
        sm.change_state("computer")
        assert sm.current_state == "computer"

    def test_add_state_change_callback(self):
        sm = StateManager()
        called = []

        def cb(old, new):
            called.append((old, new))

        sm.add_state_change_callback(cb)
        sm.change_state("chatty")
        assert called == [("idle", "chatty")]

    def test_invalid_state(self):
        sm = StateManager()
        with pytest.raises(ValueError):
            sm.change_state("invalid")

    def test_active_models(self):
        sm = StateManager()
        sm.active_models = ["model1", "model2"]
        assert sm.get_active_models() == ["model1", "model2"]

    def test_update_state_with_custom_mapping(self):
        sm = StateManager()
        sm.config.state_transitions = {"idle": {"go": "chatty"}, "chatty": {}}
        assert sm.update_state("go") == "chatty"
        assert sm.current_state == "chatty"
        assert sm.update_state("go") is None

    def test_initial_state_respects_config(self, monkeypatch):
        cfg = Config()
        cfg.default_state = "computer"
        cfg.state_models["computer"] = ["comp_model"]
        monkeypatch.setattr("chatty_commander.app.state_manager.Config", lambda: cfg)
        sm = StateManager()
        assert sm.current_state == "computer"
        assert sm.get_active_models() == ["comp_model"]

    def test_dynamic_state_from_config(self, monkeypatch):
        cfg = Config()
        cfg.state_models["gaming"] = ["shoot"]
        monkeypatch.setattr("chatty_commander.app.state_manager.Config", lambda: cfg)
        sm = StateManager()
        sm.change_state("gaming")
        assert sm.current_state == "gaming"
        assert sm.get_active_models() == ["shoot"]
