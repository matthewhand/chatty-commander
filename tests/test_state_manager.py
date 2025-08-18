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
        cfg.general_settings.default_state = "computer"
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

    def test_update_state_fallback_logic(self):
        """Test fallback logic when state_transitions is not configured"""
        sm = StateManager()
        sm.config.state_transitions = {}  # Empty transitions to trigger fallback

        # Test hey_chat_tee -> chatty
        assert sm.update_state("hey_chat_tee") == "chatty"
        assert sm.current_state == "chatty"

        # Test hey_khum_puter -> computer
        assert sm.update_state("hey_khum_puter") == "computer"
        assert sm.current_state == "computer"

        # Test okay_stop -> idle
        assert sm.update_state("okay_stop") == "idle"
        assert sm.current_state == "idle"

        # Test thanks_chat_tee -> idle (from idle state, should still work)
        sm.change_state("chatty")  # First go to chatty state
        assert sm.update_state("thanks_chat_tee") == "idle"

        # Test that_ill_do -> idle
        sm.change_state("chatty")
        assert sm.update_state("that_ill_do") == "idle"

        # Test toggle_mode cycles through states
        sm.change_state("idle")
        assert sm.update_state("toggle_mode") == "computer"
        assert sm.update_state("toggle_mode") == "chatty"
        assert sm.update_state("toggle_mode") == "idle"

    def test_update_state_no_change_returns_none(self):
        """Test that update_state returns None when no state change occurs"""
        sm = StateManager()
        sm.config.state_transitions = {"idle": {}}

        # Command not in transitions and not in fallback
        assert sm.update_state("unknown_command") is None
        assert sm.current_state == "idle"

    def test_repr(self):
        """Test __repr__ method"""
        sm = StateManager()
        sm.active_models = ["model1", "model2"]
        repr_str = repr(sm)
        assert "StateManager" in repr_str
        assert "current_state=idle" in repr_str
        assert "active_models=2" in repr_str
