from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol


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
        selected: list[InputAdapter] = []

        if self.flags.enable_text:
            selected.append(TextInputAdapter(on_command=self._dispatch_command))

        if self.flags.enable_gui:
            selected.append(DummyAdapter("gui"))

        if self.flags.enable_web:
            selected.append(DummyAdapter("web"))

        if self.flags.enable_openwakeword:
            selected.append(DummyAdapter("openwakeword"))

        if self.flags.enable_computer_vision:
            selected.append(DummyAdapter("computer_vision"))

        if self.flags.enable_discord_bridge and getattr(self.config, "advisors", {}).get(
            "enabled", False
        ):
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
