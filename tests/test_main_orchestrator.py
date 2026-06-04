"""Orchestrator tests: CLI flag parsing, run_orchestrator_mode, and adapter selection matrix."""

import logging
from types import SimpleNamespace

from chatty_commander.app.orchestrator import (
    DiscordBridgeAdapter,
    ModeOrchestrator,
    OrchestratorFlags,
)
from chatty_commander.main import create_parser, run_orchestrator_mode

# ── Shared helpers ───────────────────────────────────────────────────────


class _DummyCommandSink:
    def execute_command(self, command_name: str):
        return True


class _DummyExecutor:
    def __init__(self):
        self.executed = []

    def execute_command(self, command_name: str):
        self.executed.append(command_name)
        return True


class _DummyConfig:
    advisors = {"enabled": False}


class _DummyConfigAdvisorsEnabled:
    advisors = {"enabled": True}


# ── CLI flag parsing ─────────────────────────────────────────────────────


def test_orchestrator_flags_in_parser():
    parser = create_parser()
    args = parser.parse_args(
        [
            "--orchestrate",
            "--enable-text",
            "--enable-openwakeword",
            "--enable-computer-vision",
            "--enable-discord-bridge",
        ]
    )
    assert args.orchestrate is True
    assert args.enable_text is True
    assert args.enable_openwakeword is True
    assert args.enable_computer_vision is True
    assert args.enable_discord_bridge is True


# ── run_orchestrator_mode ────────────────────────────────────────────────


def test_run_orchestrator_mode_returns_quickly_when_web_true():
    args = SimpleNamespace(
        enable_text=True,
        gui=False,
        web=True,
        enable_openwakeword=False,
        enable_computer_vision=False,
        enable_discord_bridge=False,
    )
    rc = run_orchestrator_mode(
        config=_DummyConfig(),
        model_manager=None,
        state_manager=None,
        command_executor=_DummyExecutor(),
        logger=SimpleNamespace(info=lambda *a, **k: None),
        args=args,
    )
    assert rc == 0


# ── Adapter selection matrix (from test_orchestrator_matrix) ─────────────


class TestAdapterSelectionMatrix:
    """ModeOrchestrator.select_adapters() with various flag combinations."""

    def test_selects_text_only(self):
        orch = ModeOrchestrator(
            config=_DummyConfigAdvisorsEnabled(),
            command_sink=_DummyCommandSink(),
            flags=OrchestratorFlags(enable_text=True),
        )
        assert orch.select_adapters() == ["text"]

    def test_selects_web_only(self):
        orch = ModeOrchestrator(
            config=_DummyConfigAdvisorsEnabled(),
            command_sink=_DummyCommandSink(),
            flags=OrchestratorFlags(enable_web=True),
        )
        assert orch.select_adapters() == ["web"]

    def test_selects_text_web_discord(self):
        orch = ModeOrchestrator(
            config=_DummyConfigAdvisorsEnabled(),
            command_sink=_DummyCommandSink(),
            flags=OrchestratorFlags(
                enable_text=True, enable_web=True, enable_discord_bridge=True
            ),
        )
        assert set(orch.select_adapters()) == {"text", "web", "discord_bridge"}


# ── advisor_sink routing (P1) ────────────────────────────────────────────


class _RecordingAdvisorSink:
    """Minimal AdvisorSink: records messages and returns a canned reply."""

    def __init__(self):
        self.handled = []

    def handle_message(self, message):
        self.handled.append(message)
        return f"reply-to:{message}"


class TestAdvisorSinkRouting:
    """advisor_sink must actually receive messages from the discord bridge."""

    def test_discord_bridge_routes_messages_to_advisor_sink(self):
        sink = _RecordingAdvisorSink()
        orch = ModeOrchestrator(
            config=_DummyConfigAdvisorsEnabled(),
            command_sink=_DummyCommandSink(),
            advisor_sink=sink,
            flags=OrchestratorFlags(enable_discord_bridge=True),
        )
        orch.start()
        bridge = next(a for a in orch.adapters if isinstance(a, DiscordBridgeAdapter))
        reply = bridge.feed("hello advisor")
        assert sink.handled == ["hello advisor"]
        assert reply == "reply-to:hello advisor"

    def test_dispatch_advisor_returns_sink_reply(self):
        sink = _RecordingAdvisorSink()
        orch = ModeOrchestrator(
            config=_DummyConfigAdvisorsEnabled(),
            command_sink=_DummyCommandSink(),
            advisor_sink=sink,
            flags=OrchestratorFlags(),
        )
        assert orch._dispatch_advisor("ping") == "reply-to:ping"
        assert sink.handled == ["ping"]

    def test_discord_bridge_without_sink_warns_and_uses_dummy(self, caplog):
        orch = ModeOrchestrator(
            config=_DummyConfigAdvisorsEnabled(),
            command_sink=_DummyCommandSink(),
            advisor_sink=None,
            flags=OrchestratorFlags(enable_discord_bridge=True),
        )
        with caplog.at_level(logging.WARNING):
            names = orch.select_adapters()
        assert names == ["discord_bridge"]
        # Honest behaviour: warn that advisor messages will be dropped.
        assert any("advisor_sink" in r.message for r in caplog.records)
        # And the selected adapter is the inert dummy, not a routing bridge.
        assert not any(isinstance(a, DiscordBridgeAdapter) for a in orch.adapters)

    def test_dispatch_advisor_without_sink_warns_and_returns_none(self, caplog):
        orch = ModeOrchestrator(
            config=_DummyConfigAdvisorsEnabled(),
            command_sink=_DummyCommandSink(),
            advisor_sink=None,
            flags=OrchestratorFlags(),
        )
        with caplog.at_level(logging.WARNING):
            assert orch._dispatch_advisor("x") is None
        assert any("no advisor_sink" in r.message for r in caplog.records)
