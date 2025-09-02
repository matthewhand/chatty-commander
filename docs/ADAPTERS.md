# Adapter and Plugin System

Adapters encapsulate mode‑specific input sources (text, web, GUI, etc.).
They all implement the lightweight `InputAdapter` protocol and are
managed by the `ModeOrchestrator`.

```python
class InputAdapter(Protocol):
    name: str
    def start(self) -> None: ...
    def stop(self) -> None: ...
```

The orchestrator selects adapters based on CLI flags and starts each one,
routing recognised commands to a shared `CommandExecutor`:

```python
orch = ModeOrchestrator(
    config=config,
    command_sink=executor,
    flags=OrchestratorFlags(enable_text=True)
)
orch.start()
```

## Writing a custom adapter

1. Subclass the protocol and implement `start`/`stop` plus any input loop.
1. Pass a callback that dispatches recognised commands to the orchestrator.

```python
class MQTTAdapter:
    name = "mqtt"
    def __init__(self, on_command: Callable[[str], None]):
        self._on_command = on_command
    def start(self) -> None:
        client.subscribe("commands/#")
    def stop(self) -> None:
        client.disconnect()
```

Enable it by appending an instance to `ModeOrchestrator.adapters` or by
extending `select_adapters` in your fork. Adapters are intentionally
simple so plugins can live in separate packages.
