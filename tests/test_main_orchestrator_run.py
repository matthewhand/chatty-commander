from types import SimpleNamespace

from chatty_commander.app.orchestrator import InputAdapter
from chatty_commander.main import run_orchestrator_mode


class DummyExecutor:
    def __init__(self):
        self.executed = []

    def execute_command(self, command_name: str):
        self.executed.append(command_name)
        return True


class DummyConfig:
    advisors = {"enabled": False}


def test_run_orchestrator_mode_returns_quickly_when_web_true():
<<<<<<< HEAD
    args = SimpleNamespace(
        enable_text=True,
        gui=False,
        web=True,
        enable_openwakeword=False,
        enable_computer_vision=False,
        enable_discord_bridge=False,
    )
    rc = run_orchestrator_mode(
        config=DummyConfig(),
        model_manager=None,
        state_manager=None,
        command_executor=DummyExecutor(),
        logger=SimpleNamespace(info=lambda *a, **k: None),
        args=args,
    )
    assert rc == 0
=======
    class TrackingWebAdapter(InputAdapter):
        name = "web"
        started = False
        stopped = False

        def on_start(self) -> None:  # pragma: no cover - simple
            type(self).started = True

        def on_stop(self) -> None:  # pragma: no cover - simple
            type(self).stopped = True

    original = InputAdapter.registry["web"]
    InputAdapter.registry["web"] = TrackingWebAdapter
    try:
        args = SimpleNamespace(
            enable_text=True,
            gui=False,
            web=True,
            enable_openwakeword=False,
            enable_computer_vision=False,
            enable_discord_bridge=False,
        )
        rc = run_orchestrator_mode(
            config=DummyConfig(),
            model_manager=None,
            state_manager=None,
            command_executor=DummyExecutor(),
            logger=SimpleNamespace(info=lambda *a, **k: None),
            args=args,
        )
        assert rc == 0
        assert TrackingWebAdapter.started is True
        assert TrackingWebAdapter.stopped is True
    finally:
        InputAdapter.registry["web"] = original
>>>>>>> 231e8853a6a87e434f7239c3dc0540d12f1f1a94
