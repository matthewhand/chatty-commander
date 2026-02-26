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

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

import logging

try:
    from chatty_commander.voice.wakeword import MockWakeWordDetector, WakeWordDetector

    VOICE_AVAILABLE = True
except ImportError:
    MockWakeWordDetector = None  # type: ignore
    WakeWordDetector = None  # type: ignore
    VOICE_AVAILABLE = False


logger = logging.getLogger(__name__)


class CommandSink(Protocol):
    def execute_command(self, command_name: str) -> Any:  # pragma: no cover - protocol
        ...


class AdvisorSink(Protocol):
    def handle_message(self, message: Any) -> Any:  # pragma: no cover - protocol
        ...


class InputAdapter(Protocol):
    name: str

    def start(self) -> None:  # pragma: no cover - protocol
        ...

    def stop(self) -> None:  # pragma: no cover - protocol
        ...


@dataclass
class OrchestratorFlags:
    enable_text: bool = False
    enable_gui: bool = False
    enable_web: bool = False
    enable_openwakeword: bool = False
    enable_computer_vision: bool = False
    enable_discord_bridge: bool = False


class TextInputAdapter:
    name = "text"

    def __init__(self, on_command: Callable[[str], None]) -> None:
        self._on_command = on_command
        self._started = False

    def start(self) -> None:
        self._started = True

    def stop(self) -> None:
        self._started = False

    # Helper for tests/manual feeding
    def feed(self, text: str) -> None:
        if self._started:
            self._on_command(text)


class DummyAdapter:
    """Placeholder adapters for GUI/WEB/CV/WakeWord/Discord bridge.

    Real implementations exist or will be provided elsewhere (e.g., WebMode server, Node bridge).
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._started = False

    def start(self) -> None:
        self._started = True

    def stop(self) -> None:
        self._started = False


class OpenWakeWordAdapter:
    """Adapter for OpenWakeWord wake word detection."""

    name = "openwakeword"

    def __init__(
        self, on_wake_word: Callable[[str, float], None], config: Any = None
    ) -> None:
        self._on_wake_word = on_wake_word
        self._config = config
        self._detector = None
        self._started = False

    def start(self) -> None:
        if not VOICE_AVAILABLE:
            raise ImportError("Voice dependencies not available. Install with: uv sync")

        if self._started:
            return

        # Get wake word configuration from config
        wake_words = getattr(self._config, "wake_words", None) or [
            "hey_jarvis",
            "alexa",
        ]
        threshold = getattr(self._config, "wake_word_threshold", 0.5)

        # Use MockWakeWordDetector if no audio hardware available
        if WakeWordDetector is not None and MockWakeWordDetector is not None:
            try:
                self._detector = WakeWordDetector(
                    wake_words=wake_words, threshold=threshold
                )
            except Exception:
                # Fallback to mock detector
                self._detector = MockWakeWordDetector()
        else:
            self._detector = None

        # Add callback for wake word detection
        if self._detector is not None:
            self._detector.add_callback(self._handle_wake_word)
            self._detector.start_listening()
        self._started = True

    def stop(self) -> None:
        if self._detector and self._started:
            self._detector.stop_listening()
        self._started = False

    def _handle_wake_word(self, wake_word: str, confidence: float) -> None:
        """Handle wake word detection by calling the callback."""
        self._on_wake_word(wake_word, confidence)


class ModeOrchestrator:
    """Unifies multiple operating modes by selecting and starting adapters.

    - Text mode: stdin-like commands or injected strings
    - GUI mode: placeholder until GUI module provides an adapter
    - Web mode: placeholder referencing existing FastAPI server lifecycle
    - OpenWakeWord: optional adapter placeholder
    - Computer Vision: optional adapter placeholder
    - Discord bridge: optional adapter placeholder for Node.js bridge
    """

    def __init__(
        self,
        *,
        config: Any,
        command_sink: CommandSink,
        advisor_sink: AdvisorSink | None = None,
        flags: OrchestratorFlags | None = None,
    ) -> None:
        self.config = config
        self.command_sink = command_sink
        self.advisor_sink = advisor_sink
        self.flags = flags or OrchestratorFlags()
        self.adapters: list[InputAdapter] = []

    def select_adapters(self) -> list[str]:
        selected: list[Any] = []

        if self.flags.enable_text:
            selected.append(TextInputAdapter(on_command=self._dispatch_command))

        if self.flags.enable_gui:
            selected.append(DummyAdapter("gui"))

        if self.flags.enable_web:
            selected.append(DummyAdapter("web"))

        if self.flags.enable_openwakeword:
            if VOICE_AVAILABLE:
                try:
                    adapter = OpenWakeWordAdapter(self._handle_wake_word, self.config)  # type: ignore
                    selected.append(adapter)
                except Exception:
                    selected.append(DummyAdapter("openwakeword"))
            else:
                selected.append(DummyAdapter("openwakeword"))

        if self.flags.enable_computer_vision:
            selected.append(DummyAdapter("computer_vision"))

        if self.flags.enable_discord_bridge and getattr(
            self.config, "advisors", {}
        ).get("enabled", False):
            selected.append(DummyAdapter("discord_bridge"))

        self.adapters = selected
        return [a.name for a in selected]

    def start(self) -> list[str]:
        if not self.adapters:
            self.select_adapters()
        for adapter in self.adapters:
            adapter.start()
        return [a.name for a in self.adapters]

    def stop(self) -> None:
        for adapter in self.adapters:
            try:
                adapter.stop()
            except Exception:
                pass

    # Routing
    def _dispatch_command(self, command_name: str) -> Any:
        return self.command_sink.execute_command(command_name)

    def _handle_wake_word(self, wake_word: str, confidence: float) -> None:
        """Handle wake word detection."""
        # For now, treat wake word as a command trigger
        # In the future, this could activate voice input or advisor mode
        command_name = f"wake_word_{wake_word}"
        try:
            self._dispatch_command(command_name)
        except Exception:
            # If no specific wake word command, try a generic wake command
            try:
                self._dispatch_command("wake")
            except Exception as e:
                # If no wake command, log the detection
                logger.warning(
                    f"Wake word '{wake_word}' detected but no 'wake_word_{wake_word}' "
                    f"or generic 'wake' command found, or execution failed: {e}"
                )
