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
        flags=OrchestratorFlags(
            enable_text=True, enable_web=True, enable_discord_bridge=True
        ),
    )
    names = orch.select_adapters()
    assert set(names) == {"text", "web", "discord_bridge"}
