# MIT License
#
# Copyright (c) 2024 mhand
#
# Tests for src/chatty_commander/llm/cli.py — the LLM CLI surface.
# All external LLM backends are mocked at the import boundary so nothing real
# (network/onnx/torch) loads.

"""Coverage tests for the LLM CLI subcommands.

The production module imports ``LLMManager`` and ``CommandProcessor`` at module
load time:

    from .manager import LLMManager
    from .processor import CommandProcessor

so we patch ``chatty_commander.llm.cli.LLMManager`` /
``chatty_commander.llm.cli.CommandProcessor`` (the names bound in the cli module)
to keep everything hermetic.
"""

from __future__ import annotations

import argparse
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from chatty_commander.llm import cli as llm_cli

# ---------------------------------------------------------------------------
# Helpers / fakes
# ---------------------------------------------------------------------------


def _make_manager(**overrides):
    """Build a MagicMock that behaves like an LLMManager."""
    m = MagicMock(name="LLMManager")
    m.get_active_backend_name.return_value = overrides.get("active", "mock")
    m.is_available.return_value = overrides.get("available", True)
    m.get_all_backends_info.return_value = overrides.get(
        "all_info",
        {
            "active": "mock",
            "mock": {"available": True, "responses_count": 5, "call_count": 2},
            "openai": {
                "available": False,
                "base_url": "https://api.openai.com",
                "has_api_key": False,
                "error": "no key",
            },
        },
    )
    m.get_backend_info.return_value = overrides.get(
        "backend_info", {"name": "mock", "available": True}
    )
    m.generate_response.return_value = overrides.get("response", "hi there")
    m.test_backend.return_value = overrides.get(
        "test_result",
        {"success": True, "response": "ok", "response_time": 0.123},
    )
    return m


def _make_processor(**overrides):
    p = MagicMock(name="CommandProcessor")
    p.get_processor_status.return_value = overrides.get(
        "status",
        {
            "llm_backend": "mock",
            "available_commands": ["lights", "music"],
        },
    )
    p.process_command.return_value = overrides.get(
        "process", ("lights", 0.92, "matched lights")
    )
    p.explain_command.return_value = overrides.get(
        "explain", {"description": "toggle the lights"}
    )
    p.get_command_suggestions.return_value = overrides.get(
        "suggestions",
        [
            {"command": "lights", "confidence": 0.8},
            {"command": "music", "confidence": 0.5},
        ],
    )
    return p


@pytest.fixture
def patch_manager(monkeypatch):
    """Patch LLMManager at the cli import boundary; returns the mock instance."""
    instance = _make_manager()
    factory = MagicMock(return_value=instance)
    monkeypatch.setattr(llm_cli, "LLMManager", factory)
    return SimpleNamespace(factory=factory, instance=instance)


@pytest.fixture
def patch_processor(monkeypatch):
    instance = _make_processor()
    factory = MagicMock(return_value=instance)
    monkeypatch.setattr(llm_cli, "CommandProcessor", factory)
    return SimpleNamespace(factory=factory, instance=instance)


# ---------------------------------------------------------------------------
# add_llm_subcommands — argument parsing
# ---------------------------------------------------------------------------


def _build_parser():
    parser = argparse.ArgumentParser(prog="cc")
    sub = parser.add_subparsers(dest="command")
    llm_cli.add_llm_subcommands(sub)
    return parser


def test_add_subcommands_status_parses():
    parser = _build_parser()
    ns = parser.parse_args(["llm", "status"])
    assert ns.command == "llm"
    assert ns.llm_command == "status"


def test_add_subcommands_test_defaults():
    parser = _build_parser()
    ns = parser.parse_args(["llm", "test"])
    assert ns.llm_command == "test"
    assert ns.backend is None
    assert ns.prompt == "Hello, how are you?"
    assert ns.mock is False


def test_add_subcommands_test_flags():
    parser = _build_parser()
    ns = parser.parse_args(
        ["llm", "test", "--backend", "openai", "--prompt", "yo", "--mock"]
    )
    assert ns.backend == "openai"
    assert ns.prompt == "yo"
    assert ns.mock is True


def test_add_subcommands_process_requires_text():
    parser = _build_parser()
    ns = parser.parse_args(["llm", "process", "turn on lights", "--mock"])
    assert ns.llm_command == "process"
    assert ns.text == "turn on lights"
    assert ns.mock is True


def test_add_subcommands_process_missing_text_errors():
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["llm", "process"])


def test_add_subcommands_backends_parses():
    parser = _build_parser()
    ns = parser.parse_args(["llm", "backends"])
    assert ns.llm_command == "backends"


# ---------------------------------------------------------------------------
# handle_llm_command — dispatch
# ---------------------------------------------------------------------------


def test_handle_no_llm_command_attr(capsys):
    args = SimpleNamespace()  # no llm_command attribute
    llm_cli.handle_llm_command(args)
    out = capsys.readouterr().out
    assert "No LLM command specified" in out


def test_handle_empty_llm_command(capsys):
    args = SimpleNamespace(llm_command=None)
    llm_cli.handle_llm_command(args)
    out = capsys.readouterr().out
    assert "No LLM command specified" in out


def test_handle_unknown_llm_command(capsys):
    args = SimpleNamespace(llm_command="bogus")
    llm_cli.handle_llm_command(args)
    out = capsys.readouterr().out
    assert "Unknown LLM command: bogus" in out


def test_handle_dispatches_status(monkeypatch):
    called = {}
    monkeypatch.setattr(
        llm_cli, "_handle_llm_status", lambda a: called.setdefault("status", a)
    )
    args = SimpleNamespace(llm_command="status")
    llm_cli.handle_llm_command(args)
    assert "status" in called


def test_handle_dispatches_test(monkeypatch):
    called = {}
    monkeypatch.setattr(
        llm_cli, "_handle_llm_test", lambda a: called.setdefault("test", a)
    )
    llm_cli.handle_llm_command(SimpleNamespace(llm_command="test"))
    assert "test" in called


def test_handle_dispatches_process(monkeypatch):
    called = {}
    monkeypatch.setattr(
        llm_cli,
        "_handle_llm_process",
        lambda a, c=None: called.setdefault("process", (a, c)),
    )
    cm = object()
    llm_cli.handle_llm_command(SimpleNamespace(llm_command="process"), config_manager=cm)
    assert called["process"][1] is cm


def test_handle_dispatches_backends(monkeypatch):
    called = {}
    monkeypatch.setattr(
        llm_cli, "_handle_llm_backends", lambda a: called.setdefault("backends", a)
    )
    llm_cli.handle_llm_command(SimpleNamespace(llm_command="backends"))
    assert "backends" in called


# ---------------------------------------------------------------------------
# _handle_llm_status
# ---------------------------------------------------------------------------


def test_status_happy_path(patch_manager, monkeypatch, capsys):
    # Control env vars: one set (masked key), one plain, one unset.
    monkeypatch.setenv("OPENAI_API_KEY", "abcd1234efgh5678")
    monkeypatch.setenv("LLM_BACKEND", "mock")
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)

    llm_cli._handle_llm_status(SimpleNamespace())
    out = capsys.readouterr().out

    assert "LLM System Status" in out
    assert "Dependencies:" in out
    assert "Active backend: mock" in out
    # masked key: first4 + ... + last4
    assert "abcd...5678" in out
    assert "OPENAI_API_KEY: abcd...5678" in out
    assert "LLM_BACKEND: mock" in out
    assert "OPENAI_API_BASE: Not set" in out
    patch_manager.factory.assert_called_once_with(use_mock=True)


def test_status_backend_with_error(patch_manager, monkeypatch, capsys):
    patch_manager.instance.get_all_backends_info.return_value = {
        "active": "mock",
        "openai": {"available": False, "error": "boom"},
    }
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    llm_cli._handle_llm_status(SimpleNamespace())
    out = capsys.readouterr().out
    assert "Error: boom" in out
    assert "openai: Not available" in out


def test_status_short_key_not_masked(patch_manager, monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "short")  # len <= 8 -> shown raw
    llm_cli._handle_llm_status(SimpleNamespace())
    out = capsys.readouterr().out
    assert "OPENAI_API_KEY: short" in out


def test_status_exception_path(monkeypatch, capsys):
    boom = MagicMock(side_effect=RuntimeError("init failed"))
    monkeypatch.setattr(llm_cli, "LLMManager", boom)
    llm_cli._handle_llm_status(SimpleNamespace())
    out = capsys.readouterr().out
    assert "Status check failed: init failed" in out


# ---------------------------------------------------------------------------
# _handle_llm_test
# ---------------------------------------------------------------------------


def test_test_specific_backend_success(patch_manager, capsys):
    args = SimpleNamespace(backend="openai", prompt="hi", mock=False)
    llm_cli._handle_llm_test(args)
    out = capsys.readouterr().out
    assert "Testing backend: openai" in out
    assert "Success!" in out
    assert "Response: ok" in out
    assert "Time: 0.123s" in out
    patch_manager.instance.test_backend.assert_called_once_with("openai", "hi")
    patch_manager.factory.assert_called_once_with(use_mock=False)


def test_test_specific_backend_failure(patch_manager, capsys):
    patch_manager.instance.test_backend.return_value = {
        "success": False,
        "error": "backend down",
    }
    args = SimpleNamespace(backend="openai", prompt="hi", mock=True)
    llm_cli._handle_llm_test(args)
    out = capsys.readouterr().out
    assert "Failed: backend down" in out


def test_test_specific_backend_failure_unknown_error(patch_manager, capsys):
    patch_manager.instance.test_backend.return_value = {"success": False}
    args = SimpleNamespace(backend="openai", prompt="hi", mock=True)
    llm_cli._handle_llm_test(args)
    out = capsys.readouterr().out
    assert "Failed: Unknown error" in out


def test_test_active_backend_success(patch_manager, capsys):
    args = SimpleNamespace(backend=None, prompt="hello", mock=True)
    llm_cli._handle_llm_test(args)
    out = capsys.readouterr().out
    assert "Testing active backend: mock" in out
    assert "Response: hi there" in out
    patch_manager.instance.generate_response.assert_called_once_with(
        "hello", max_tokens=50
    )


def test_test_active_backend_generate_raises(patch_manager, capsys):
    patch_manager.instance.generate_response.side_effect = RuntimeError("gen err")
    args = SimpleNamespace(backend=None, prompt="hello", mock=True)
    llm_cli._handle_llm_test(args)
    out = capsys.readouterr().out
    assert "Failed: gen err" in out
    # Backend info still printed afterward
    assert "Backend Info:" in out


def test_test_outer_exception(monkeypatch, capsys):
    monkeypatch.setattr(
        llm_cli, "LLMManager", MagicMock(side_effect=RuntimeError("no manager"))
    )
    args = SimpleNamespace(backend=None, prompt="x", mock=False)
    llm_cli._handle_llm_test(args)
    out = capsys.readouterr().out
    assert "LLM test failed: no manager" in out


# ---------------------------------------------------------------------------
# _handle_llm_process
# ---------------------------------------------------------------------------


def test_process_matched_command(patch_manager, patch_processor, capsys):
    args = SimpleNamespace(text="turn on lights", mock=True)
    cm = object()
    llm_cli._handle_llm_process(args, config_manager=cm)
    out = capsys.readouterr().out
    assert "Processing command: 'turn on lights'" in out
    assert "Available commands: lights, music" in out
    assert "Matched command: lights" in out
    assert "Confidence: 0.92" in out
    assert "Explanation: matched lights" in out
    assert "Action: toggle the lights" in out
    assert "Suggestions:" in out
    patch_processor.factory.assert_called_once_with(
        llm_manager=patch_manager.instance, config_manager=cm
    )
    patch_processor.instance.get_command_suggestions.assert_called_once_with("tur")


def test_process_no_match(patch_manager, patch_processor, capsys):
    patch_processor.instance.process_command.return_value = (None, 0.0, "nothing fit")
    patch_processor.instance.get_command_suggestions.return_value = []
    args = SimpleNamespace(text="zzz", mock=True)
    llm_cli._handle_llm_process(args)
    out = capsys.readouterr().out
    assert "No command matched" in out
    assert "Reason: nothing fit" in out
    assert "Suggestions:" not in out


def test_process_exception(monkeypatch, capsys):
    monkeypatch.setattr(
        llm_cli, "LLMManager", MagicMock(side_effect=RuntimeError("proc boom"))
    )
    args = SimpleNamespace(text="x", mock=False)
    llm_cli._handle_llm_process(args)
    out = capsys.readouterr().out
    assert "Command processing failed: proc boom" in out


# ---------------------------------------------------------------------------
# _handle_llm_backends
# ---------------------------------------------------------------------------


def test_backends_all_branches(patch_manager, capsys):
    patch_manager.instance.get_all_backends_info.return_value = {
        "active": "ollama",
        "openai": {"available": True, "base_url": "u", "has_api_key": True},
        "ollama": {"available": True, "host": "localhost", "model": "llama"},
        "local": {"available": False, "model_name": "gpt2", "device": "cpu"},
        "mock": {"available": True, "responses_count": 3, "call_count": 7},
    }
    llm_cli._handle_llm_backends(SimpleNamespace())
    out = capsys.readouterr().out
    assert "Active Backend: ollama" in out
    assert "OPENAI" in out
    assert "Has API Key: True" in out
    assert "Host: localhost" in out
    assert "Model: llama" in out
    assert "Model: gpt2" in out
    assert "Device: cpu" in out
    assert "Responses: 3" in out
    assert "Calls: 7" in out


def test_backends_with_error_and_no_active(patch_manager, capsys):
    patch_manager.instance.get_all_backends_info.return_value = {
        "openai": {"available": False, "error": "key missing"},
    }
    llm_cli._handle_llm_backends(SimpleNamespace())
    out = capsys.readouterr().out
    # active key absent -> default "none"
    assert "Active Backend: none" in out
    assert "Error: key missing" in out


def test_backends_exception(monkeypatch, capsys):
    monkeypatch.setattr(
        llm_cli, "LLMManager", MagicMock(side_effect=RuntimeError("be boom"))
    )
    llm_cli._handle_llm_backends(SimpleNamespace())
    out = capsys.readouterr().out
    assert "Failed to get backend information: be boom" in out


# ---------------------------------------------------------------------------
# demo_llm_integration
# ---------------------------------------------------------------------------


def test_demo_happy_path(patch_manager, patch_processor, capsys):
    # First input matches, return a no-match for one to hit both branches.
    results = iter(
        [
            ("lights", 0.9, "ok"),
            (None, 0.0, "no"),
            ("music", 0.7, "ok2"),
            (None, 0.0, "no2"),
            (None, 0.1, "unknown"),
        ]
    )
    patch_processor.instance.process_command.side_effect = lambda _i: next(results)
    llm_cli.demo_llm_integration(config_manager=object())
    out = capsys.readouterr().out
    assert "LLM Integration Demo" in out
    assert "LLM Backend: mock" in out
    assert "→ lights (confidence: 0.90)" in out
    assert "No match (no)" in out
    assert "demo completed!" in out


def test_demo_exception(monkeypatch, caplog, capsys):
    monkeypatch.setattr(
        llm_cli, "LLMManager", MagicMock(side_effect=RuntimeError("demo boom"))
    )
    with caplog.at_level("ERROR"):
        llm_cli.demo_llm_integration()
    out = capsys.readouterr().out
    assert "Demo failed: demo boom" in out
    assert any("LLM demo error" in r.message for r in caplog.records)
