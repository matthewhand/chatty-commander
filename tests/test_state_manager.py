import pytest
from state_manager import StateManager

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
