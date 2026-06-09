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


# ---------------------------------------------------------------------------
# Provider gating: providers.py only registers switch_mode with the Agent
# when the advisors tools config explicitly enables it (mirrors dograh_call).
# ---------------------------------------------------------------------------


@pytest.fixture()
def _stub_agents_module(monkeypatch):
    """Stub the openai-agents SDK surface so provider construction runs in
    tests without the real SDK (mirrors tests/test_dograh_advisor_tool.py),
    then restore the real modules on teardown."""
    import importlib
    import sys
    import types

    fake_agents = types.ModuleType("agents")

    class _StubAgent:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def chat(self, prompt):
            return ""

    fake_agents.Agent = _StubAgent
    fake_agents.FunctionTool = type(
        "FunctionTool",
        (),
        {"__init__": lambda self, **kw: setattr(self, "kwargs", kw)},
    )

    monkeypatch.setitem(sys.modules, "agents", fake_agents)

    # Re-import providers + tool modules so they see the fake agents module.
    import chatty_commander.advisors.providers as providers_mod
    import chatty_commander.advisors.tools.browser_analyst as ba
    import chatty_commander.advisors.tools.dograh_call as dc
    import chatty_commander.advisors.tools.switch_mode as sm

    modules = (providers_mod, ba, dc, sm)
    for mod in modules:
        importlib.reload(mod)
    yield
    # Put the real `agents` module back before re-reloading so other tests
    # see the genuine SDK objects again.
    monkeypatch.undo()
    for mod in modules:
        importlib.reload(mod)


def _agent_tool_names(provider):
    return [
        getattr(t, "kwargs", {}).get("name") for t in provider.agent.kwargs["tools"]
    ]


def _provider_config(tools):
    return {
        "api_key": "k",
        "model": "test",
        "base_url": "http://example",
        "tools": tools,
    }


@pytest.mark.usefixtures("_stub_agents_module")
def test_completion_provider_loads_switch_mode_when_enabled():
    from chatty_commander.advisors.providers import CompletionProvider

    provider = CompletionProvider(
        _provider_config(
            {
                "browser_analyst": {"enabled": False},
                "switch_mode": {"enabled": True},
            }
        )
    )
    assert "switch_mode" in _agent_tool_names(provider)


@pytest.mark.usefixtures("_stub_agents_module")
def test_completion_provider_omits_switch_mode_by_default():
    from chatty_commander.advisors.providers import CompletionProvider

    provider = CompletionProvider(
        _provider_config({"browser_analyst": {"enabled": False}})
    )
    assert "switch_mode" not in _agent_tool_names(provider)


@pytest.mark.usefixtures("_stub_agents_module")
def test_completion_provider_omits_switch_mode_when_disabled():
    from chatty_commander.advisors.providers import CompletionProvider

    provider = CompletionProvider(
        _provider_config(
            {
                "browser_analyst": {"enabled": False},
                "switch_mode": {"enabled": False},
            }
        )
    )
    assert "switch_mode" not in _agent_tool_names(provider)


@pytest.mark.usefixtures("_stub_agents_module")
def test_responses_provider_loads_switch_mode_when_enabled():
    from chatty_commander.advisors.providers import ResponsesProvider

    config = _provider_config(
        {
            "browser_analyst": {"enabled": False},
            "switch_mode": {"enabled": True},
        }
    )
    config["llm_api_mode"] = "responses"
    provider = ResponsesProvider(config)
    assert "switch_mode" in _agent_tool_names(provider)


@pytest.mark.usefixtures("_stub_agents_module")
def test_responses_provider_omits_switch_mode_by_default():
    from chatty_commander.advisors.providers import ResponsesProvider

    config = _provider_config({"browser_analyst": {"enabled": False}})
    config["llm_api_mode"] = "responses"
    provider = ResponsesProvider(config)
    assert "switch_mode" not in _agent_tool_names(provider)
