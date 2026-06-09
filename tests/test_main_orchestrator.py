"""Orchestrator tests: CLI flag parsing, run_orchestrator_mode, and adapter selection matrix."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from chatty_commander.app.orchestrator import (
    DiscordBridgeAdapter,
    ModeOrchestrator,
    OrchestratorFlags,
)
from chatty_commander.cli.cli import build_advisor_sink
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


# ── build_advisor_sink (CLI advisor plumbing) ────────────────────────────


class TestBuildAdvisorSink:
    def test_returns_none_when_advisors_disabled(self):
        logger = MagicMock()
        assert build_advisor_sink(_DummyConfig(), logger) is None
        logger.warning.assert_not_called()

    def test_returns_none_when_config_has_no_advisors(self):
        logger = MagicMock()
        assert build_advisor_sink(SimpleNamespace(), logger) is None
        logger.warning.assert_not_called()

    def test_returns_service_when_enabled(self, monkeypatch):
        sentinel = object()
        created = {}

        def _fake_service(cfg):
            created["cfg"] = cfg
            return sentinel

        monkeypatch.setattr(
            "chatty_commander.advisors.service.AdvisorsService", _fake_service
        )
        config = _DummyConfigAdvisorsEnabled()
        assert build_advisor_sink(config, MagicMock()) is sentinel
        # The full config object is handed to AdvisorsService (it accepts
        # Config-like objects with an `.advisors` attribute).
        assert created["cfg"] is config

    def test_warns_and_returns_none_when_construction_fails(self, monkeypatch):
        def _boom(cfg):
            raise RuntimeError("missing deps")

        monkeypatch.setattr(
            "chatty_commander.advisors.service.AdvisorsService", _boom
        )
        logger = MagicMock()
        assert build_advisor_sink(_DummyConfigAdvisorsEnabled(), logger) is None
        logger.warning.assert_called_once()
        assert "missing deps" in logger.warning.call_args[0][0]


class TestRunOrchestratorModeAdvisorSink:
    """run_orchestrator_mode passes the constructed advisor sink through."""

    _args = SimpleNamespace(
        enable_text=False,
        gui=False,
        web=True,
        enable_openwakeword=False,
        enable_computer_vision=False,
        enable_discord_bridge=True,
    )

    def _patch_orchestrator(self, monkeypatch, captured):
        class _FakeOrchestrator:
            def __init__(self, *, config, command_sink, advisor_sink=None, flags=None):
                captured["advisor_sink"] = advisor_sink

            def start(self):
                return []

            def stop(self):
                return None

        monkeypatch.setattr(
            "chatty_commander.app.orchestrator.ModeOrchestrator", _FakeOrchestrator
        )

    def _run(self, run_fn, config):
        return run_fn(
            config=config,
            model_manager=None,
            state_manager=None,
            command_executor=_DummyExecutor(),
            logger=MagicMock(),
            args=self._args,
        )

    def test_cli_cli_passes_advisor_sink_when_enabled(self, monkeypatch):
        captured = {}
        self._patch_orchestrator(monkeypatch, captured)
        sentinel = object()
        monkeypatch.setattr(
            "chatty_commander.advisors.service.AdvisorsService",
            lambda cfg: sentinel,
        )
        rc = self._run(run_orchestrator_mode, _DummyConfigAdvisorsEnabled())
        assert rc == 0
        assert captured["advisor_sink"] is sentinel

    def test_cli_cli_passes_none_when_advisors_disabled(self, monkeypatch):
        captured = {}
        self._patch_orchestrator(monkeypatch, captured)
        rc = self._run(run_orchestrator_mode, _DummyConfig())
        assert rc == 0
        assert captured["advisor_sink"] is None

    def test_cli_cli_degrades_to_none_when_service_fails(self, monkeypatch):
        captured = {}
        self._patch_orchestrator(monkeypatch, captured)

        def _boom(cfg):
            raise RuntimeError("no llm deps")

        monkeypatch.setattr(
            "chatty_commander.advisors.service.AdvisorsService", _boom
        )
        logger = MagicMock()
        rc = run_orchestrator_mode(
            config=_DummyConfigAdvisorsEnabled(),
            model_manager=None,
            state_manager=None,
            command_executor=_DummyExecutor(),
            logger=logger,
            args=self._args,
        )
        assert rc == 0
        assert captured["advisor_sink"] is None
        logger.warning.assert_called_once()

    def test_cli_main_passes_advisor_sink_when_enabled(self, monkeypatch):
        from chatty_commander.cli.main import (
            run_orchestrator_mode as main_run_orchestrator_mode,
        )

        captured = {}
        self._patch_orchestrator(monkeypatch, captured)
        sentinel = object()
        monkeypatch.setattr(
            "chatty_commander.advisors.service.AdvisorsService",
            lambda cfg: sentinel,
        )
        rc = self._run(main_run_orchestrator_mode, _DummyConfigAdvisorsEnabled())
        assert rc == 0
        assert captured["advisor_sink"] is sentinel

    def test_cli_main_passes_none_when_advisors_disabled(self, monkeypatch):
        from chatty_commander.cli.main import (
            run_orchestrator_mode as main_run_orchestrator_mode,
        )

        captured = {}
        self._patch_orchestrator(monkeypatch, captured)
        rc = self._run(main_run_orchestrator_mode, _DummyConfig())
        assert rc == 0
        assert captured["advisor_sink"] is None


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
