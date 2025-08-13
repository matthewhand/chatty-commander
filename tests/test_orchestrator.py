from chatty_commander.app.orchestrator import (
    InputAdapter,
    ModeOrchestrator,
    OrchestratorFlags,
)


class DummyCommandSink:
    def __init__(self) -> None:
        self.received = []

    def execute_command(self, command_name: str):
        self.received.append(command_name)
        return True


class DummyConfig:
    advisors = {"enabled": True}


def test_orchestrator_selects_adapters_by_flags():
    sink = DummyCommandSink()
    orch = ModeOrchestrator(
        config=DummyConfig(),
        command_sink=sink,
        flags=OrchestratorFlags(
            enable_text=True,
            enable_gui=True,
            enable_web=True,
            enable_openwakeword=True,
            enable_computer_vision=True,
            enable_discord_bridge=True,
        ),
    )
    names = orch.select_adapters()
    assert set(names) == {
        "text",
        "gui",
        "web",
        "openwakeword",
        "computer_vision",
        "discord_bridge",
    }


def test_orchestrator_text_adapter_dispatches_to_sink():
    sink = DummyCommandSink()
    orch = ModeOrchestrator(
        config=DummyConfig(),
        command_sink=sink,
        flags=OrchestratorFlags(enable_text=True),
    )

    # Start and feed text
    orch.start()
    # Access the text adapter and feed a command
    text_adapter = next(a for a in orch.adapters if getattr(a, "name", "") == "text")
    text_adapter.feed("okay_stop")

    assert sink.received == ["okay_stop"]

def test_orchestrator_omits_discord_when_disabled():
    sink = DummyCommandSink()

    class DisabledConfig:
        advisors = {"enabled": False}

    orch = ModeOrchestrator(
        config=DisabledConfig(),
        command_sink=sink,
        flags=OrchestratorFlags(enable_discord_bridge=True),
    )
    names = orch.select_adapters()
    assert "discord_bridge" not in names


def test_adapter_lifecycle():
    sink = DummyCommandSink()
    orch = ModeOrchestrator(
        config=DummyConfig(),
        command_sink=sink,
        flags=OrchestratorFlags(enable_text=True),
    )
    orch.start()
    adapter = orch.adapters[0]
    assert getattr(adapter, "_started", False) is True
    orch.stop()
    assert getattr(adapter, "_started", False) is False


def test_dynamic_registry_override_and_lifecycle():
    """Adapters can be swapped via the registry and respect lifecycle hooks."""

    original_cls = InputAdapter.registry["gui"]

    class TestGUIAdapter(InputAdapter):
        name = "gui"

        def __init__(self) -> None:
            super().__init__()
            self.started = False
            self.stopped = False

        def on_start(self) -> None:
            self.started = True

        def on_stop(self) -> None:
            self.stopped = True

    try:
        sink = DummyCommandSink()
        orch = ModeOrchestrator(
            config=DummyConfig(),
            command_sink=sink,
            flags=OrchestratorFlags(enable_gui=True),
        )
        orch.select_adapters()
        assert isinstance(orch.adapters[0], TestGUIAdapter)

        orch.start()
        assert orch.adapters[0].started
        orch.stop()
        assert orch.adapters[0].stopped
    finally:
        InputAdapter.registry["gui"] = original_cls

    orch.select_adapters()
    assert all(getattr(a, "_started", False) is False for a in orch.adapters)
    orch.start()
    assert all(getattr(a, "_started", False) is True for a in orch.adapters)
    orch.stop()
    assert all(getattr(a, "_started", False) is False for a in orch.adapters)

