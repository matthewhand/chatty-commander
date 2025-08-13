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
    # Test that orchestrator mode returns quickly when web=True
    args = SimpleNamespace(web=True, no_auth=True, port=8100)
    config = DummyConfig()
    executor = DummyExecutor()

    # Should return quickly without blocking
    result = run_orchestrator_mode(args, config, executor)
    assert result is None  # Function completes without error
