import pytest
from chatty_commander.advisors.tools.switch_mode import switch_mode

def test_switch_mode():
    assert switch_mode("idle") == "SWITCH_MODE:idle"
    assert switch_mode("  active  ") == "SWITCH_MODE:active"
    assert switch_mode("") == "SWITCH_MODE:invalid"
    assert switch_mode(None) == "SWITCH_MODE:invalid"
