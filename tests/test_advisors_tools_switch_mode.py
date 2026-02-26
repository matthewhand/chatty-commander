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

import pytest
from chatty_commander.advisors.tools.switch_mode import switch_mode


@pytest.mark.unit
def test_switch_mode_happy_path():
    """Test valid mode strings."""
    assert switch_mode("idle") == "SWITCH_MODE:idle"
    assert switch_mode("chatty") == "SWITCH_MODE:chatty"
    assert switch_mode("computer") == "SWITCH_MODE:computer"


@pytest.mark.unit
def test_switch_mode_whitespace():
    """Test mode strings with surrounding whitespace."""
    assert switch_mode(" idle ") == "SWITCH_MODE:idle"
    assert switch_mode("\tchatty\n") == "SWITCH_MODE:chatty"


@pytest.mark.unit
def test_switch_mode_empty_or_invalid():
    """Test empty strings, whitespace-only strings, and None."""
    assert switch_mode("") == "SWITCH_MODE:invalid"
    assert switch_mode("   ") == "SWITCH_MODE:invalid"
    assert switch_mode(None) == "SWITCH_MODE:invalid"
