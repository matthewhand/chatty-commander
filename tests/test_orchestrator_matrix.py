from chatty_commander.app.orchestrator import ModeOrchestrator, OrchestratorFlags


class DummyCommandSink:
    def execute_command(self, command_name: str):  # pragma: no cover - not used here
        return True


class DummyConfig:
    advisors = {"enabled": True}


def test_orchestrator_selects_text_only():
    orch = ModeOrchestrator(
        config=DummyConfig(),
        command_sink=DummyCommandSink(),
        flags=OrchestratorFlags(enable_text=True),
    )
    names = orch.select_adapters()
    assert names == ["text"]


def test_orchestrator_selects_web_only():
    orch = ModeOrchestrator(
        config=DummyConfig(),
        command_sink=DummyCommandSink(),
        flags=OrchestratorFlags(enable_web=True),
    )
    names = orch.select_adapters()
    assert names == ["web"]


def test_orchestrator_selects_text_web_discord():
    orch = ModeOrchestrator(
        config=DummyConfig(),
        command_sink=DummyCommandSink(),
        flags=OrchestratorFlags(enable_text=True, enable_web=True, enable_discord_bridge=True),
    )
    names = orch.select_adapters()
    assert set(names) == {"text", "web", "discord_bridge"}


