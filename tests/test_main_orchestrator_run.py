from types import SimpleNamespace

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


