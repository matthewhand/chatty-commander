from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from importlib import metadata
from typing import Any, ClassVar


class CommandSink:
    """Protocol for executing commands from adapters."""

    def execute_command(self, command_name: str) -> Any:  # pragma: no cover - interface
        raise NotImplementedError


class AdvisorSink:
    """Protocol for forwarding advisor messages."""

    def handle_message(self, message: Any) -> Any:  # pragma: no cover - interface
        raise NotImplementedError


class InputAdapter:
    """Base class for all input adapters.

    Adapters register themselves via ``__init_subclass__`` so the orchestrator can
    discover them dynamically.  Subclasses can override :meth:`on_start` and
    :meth:`on_stop` to implement custom lifecycle behaviour.
    """

    # Registry of available adapters
    registry: ClassVar[dict[str, type[InputAdapter]]] = {}

    # Unique name for the adapter used in configuration/flags
    name: ClassVar[str]

    def __init_subclass__(cls, **kwargs: Any) -> None:  # pragma: no cover - simple
        super().__init_subclass__(**kwargs)
        if getattr(cls, "name", None):
            InputAdapter.registry[cls.name] = cls

    def __init__(self, *, metadata: dict[str, Any] | None = None) -> None:
        self.metadata = metadata or {}
        self._started = False

    # Public API -----------------------------------------------------------
    def start(self) -> None:
        self._started = True
        self.on_start()

    def stop(self) -> None:
        try:
            self.on_stop()
        finally:
            self._started = False

    # Hooks for subclasses -------------------------------------------------
    def on_start(self) -> None:  # pragma: no cover - default no-op
        pass

    def on_stop(self) -> None:  # pragma: no cover - default no-op
        pass


# Built-in adapters ---------------------------------------------------------


class TextInputAdapter(InputAdapter):
    name = "text"

    def __init__(self, on_command: Callable[[str], None]) -> None:
        super().__init__()
        self._on_command = on_command

    # Helper for tests/manual feeding
    def feed(self, text: str) -> None:
        if self._started:
            self._on_command(text)


class GUIAdapter(InputAdapter):
    name = "gui"


class WebServerAdapter(InputAdapter):
    name = "web"


class WakeWordAdapter(InputAdapter):
    name = "openwakeword"


class ComputerVisionAdapter(InputAdapter):
    name = "computer_vision"


class DiscordBridgeAdapter(InputAdapter):
    name = "discord_bridge"


def load_entry_point_adapters(group: str = "chatty_commander.adapters") -> None:
    """Load adapters exposed via package entry points."""

    try:
        entries = metadata.entry_points()
        for ep in entries.select(group=group):  # type: ignore[attr-defined]
            try:
                ep.load()
            except Exception:
                # Silently ignore failing entry points to keep startup robust
                continue
    except Exception:
        # Older Python may not have entry points API or environment may forbid
        pass


@dataclass
class OrchestratorFlags:
    enable_text: bool = False
    enable_gui: bool = False
    enable_web: bool = False
    enable_openwakeword: bool = False
    enable_computer_vision: bool = False
    enable_discord_bridge: bool = False


class ModeOrchestrator:
    """Unifies multiple operating modes by selecting and starting adapters."""

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
        """Select adapter instances based on flags and registry."""

        load_entry_point_adapters()  # ensure any external adapters are loaded
        selected: list[InputAdapter] = []

        registry = InputAdapter.registry

        flag_map: dict[str, tuple[str, Callable[[type[InputAdapter]], InputAdapter], Callable[[], bool]]] = {
            "enable_text": (
                "text",
                lambda cls: cls(on_command=self._dispatch_command),
                lambda: True,
            ),
            "enable_gui": ("gui", lambda cls: cls(), lambda: True),
            "enable_web": ("web", lambda cls: cls(), lambda: True),
            "enable_openwakeword": ("openwakeword", lambda cls: cls(), lambda: True),
            "enable_computer_vision": ("computer_vision", lambda cls: cls(), lambda: True),
            "enable_discord_bridge": (
                "discord_bridge",
                lambda cls: cls(),
                lambda: getattr(self.config, "advisors", {}).get("enabled", False),
            ),
        }

        for flag_attr, (adapter_name, factory, condition) in flag_map.items():
            if getattr(self.flags, flag_attr) and adapter_name in registry and condition():
                selected.append(factory(registry[adapter_name]))

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

    # Routing -------------------------------------------------------------
    def _dispatch_command(self, command_name: str) -> Any:
        return self.command_sink.execute_command(command_name)
