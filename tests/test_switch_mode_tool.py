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

"""Tests for the switch_mode advisor tool and the advisor tool registry."""

import pytest

from chatty_commander.advisors.tools import TOOL_REGISTRY, get_tool_instance
from chatty_commander.advisors.tools.switch_mode import (
    AGENTS_AVAILABLE,
    switch_mode,
    switch_mode_tool_instance,
)


def test_switch_mode_returns_directive():
    assert switch_mode("idle") == "SWITCH_MODE:idle"
    assert switch_mode("  computer  ") == "SWITCH_MODE:computer"


def test_switch_mode_empty_is_invalid():
    assert switch_mode("") == "SWITCH_MODE:invalid"
    assert switch_mode("   ") == "SWITCH_MODE:invalid"
    assert switch_mode(None) == "SWITCH_MODE:invalid"  # type: ignore[arg-type]


def test_switch_mode_registered_in_registry():
    """switch_mode must be wired into the advisor tool registry alongside
    browser_analyst and dograh_place_call."""
    assert "switch_mode" in TOOL_REGISTRY
    assert "browser_analyst" in TOOL_REGISTRY
    assert "dograh_place_call" in TOOL_REGISTRY


def test_get_tool_instance_unknown_name_returns_none():
    assert get_tool_instance("does_not_exist") is None


@pytest.mark.skipif(not AGENTS_AVAILABLE, reason="openai-agents SDK not installed")
def test_switch_mode_function_tool_instance():
    """When the agents SDK is available the module exposes a FunctionTool
    instance (mirroring dograh_call) ready to hand to an Agent."""
    assert switch_mode_tool_instance is not None
    assert switch_mode_tool_instance.name == "switch_mode"
    schema = switch_mode_tool_instance.params_json_schema
    assert schema["required"] == ["mode"]
    assert "mode" in schema["properties"]
    # The tool invokes the plain switch_mode function.
    assert switch_mode_tool_instance.on_invoke_tool is switch_mode


@pytest.mark.skipif(not AGENTS_AVAILABLE, reason="openai-agents SDK not installed")
def test_registry_resolves_switch_mode_instance():
    instance = get_tool_instance("switch_mode")
    assert instance is switch_mode_tool_instance
