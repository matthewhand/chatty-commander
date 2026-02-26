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

import pytest
from unittest.mock import MagicMock
from chatty_commander.app.orchestrator import ModeOrchestrator, OrchestratorFlags

class MockCommandSink:
    def __init__(self):
        self.calls = []
        self.failures = set()

    def execute_command(self, command_name: str):
        self.calls.append(command_name)
        if command_name in self.failures:
            raise Exception(f"Command {command_name} failed")
        return True

class DummyConfig:
    advisors = {"enabled": False}

def test_handle_wake_word_success():
    """Test successful wake word handling."""
    sink = MockCommandSink()
    orch = ModeOrchestrator(
        config=DummyConfig(),
        command_sink=sink,
        flags=OrchestratorFlags()
    )

    orch._handle_wake_word("jarvis", 0.9)

    assert sink.calls == ["wake_word_jarvis"]

def test_handle_wake_word_fallback():
    """Test fallback to 'wake' command if specific wake word command fails."""
    sink = MockCommandSink()
    sink.failures.add("wake_word_jarvis")

    orch = ModeOrchestrator(
        config=DummyConfig(),
        command_sink=sink,
        flags=OrchestratorFlags()
    )

    orch._handle_wake_word("jarvis", 0.9)

    assert sink.calls == ["wake_word_jarvis", "wake"]

def test_handle_wake_word_all_fail():
    """Test graceful handling if both specific and generic wake commands fail."""
    sink = MockCommandSink()
    sink.failures.add("wake_word_jarvis")
    sink.failures.add("wake")

    orch = ModeOrchestrator(
        config=DummyConfig(),
        command_sink=sink,
        flags=OrchestratorFlags()
    )

    # Should not raise exception
    orch._handle_wake_word("jarvis", 0.9)

    assert sink.calls == ["wake_word_jarvis", "wake"]
