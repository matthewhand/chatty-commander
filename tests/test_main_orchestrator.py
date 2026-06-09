"""Orchestrator tests: CLI flag parsing, run_orchestrator_mode, and adapter selection matrix."""

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


# ── Advisor sink wiring through the discord bridge ───────────────────────


class _RecordingAdvisorSink:
    def __init__(self):
        self.messages = []

    def handle_message(self, message):
        self.messages.append(message)
        return "reply"


class TestAdvisorSinkWiring:
    def _orchestrator(self, advisor_sink=None):
        return ModeOrchestrator(
            config=_DummyConfigAdvisorsEnabled(),
            command_sink=_DummyCommandSink(),
            advisor_sink=advisor_sink,
            flags=OrchestratorFlags(enable_discord_bridge=True),
        )

    def test_discord_bridge_uses_advisor_adapter_when_sink_provided(self):
        orch = self._orchestrator(advisor_sink=_RecordingAdvisorSink())
        assert orch.select_adapters() == ["discord_bridge"]
        assert isinstance(orch.adapters[0], DiscordBridgeAdapter)

    def test_bridge_message_reaches_advisor_sink(self):
        sink = _RecordingAdvisorSink()
        orch = self._orchestrator(advisor_sink=sink)
        orch.start()
        message = {"platform": "discord", "channel": "c", "user": "u", "text": "hi"}
        result = orch.adapters[0].feed(message)
        assert sink.messages == [message]
        assert result == "reply"

    def test_bridge_drops_messages_before_start_and_after_stop(self):
        sink = _RecordingAdvisorSink()
        orch = self._orchestrator(advisor_sink=sink)
        orch.select_adapters()
        adapter = orch.adapters[0]
        assert adapter.feed("early") is None
        orch.start()
        orch.stop()
        assert adapter.feed("late") is None
        assert sink.messages == []

    def test_warns_and_falls_back_when_no_sink(self, caplog):
        orch = self._orchestrator(advisor_sink=None)
        with caplog.at_level("WARNING", logger="chatty_commander.app.orchestrator"):
            names = orch.select_adapters()
        assert names == ["discord_bridge"]
        assert not isinstance(orch.adapters[0], DiscordBridgeAdapter)
        assert any(
            "no advisor_sink" in record.getMessage() for record in caplog.records
        )

    def test_dispatch_advisor_message_without_sink_warns_and_returns_none(
        self, caplog
    ):
        orch = self._orchestrator(advisor_sink=None)
        with caplog.at_level("WARNING", logger="chatty_commander.app.orchestrator"):
            assert orch._dispatch_advisor_message({"text": "hi"}) is None
        assert any(
            "Advisor message dropped" in record.getMessage()
            for record in caplog.records
        )
