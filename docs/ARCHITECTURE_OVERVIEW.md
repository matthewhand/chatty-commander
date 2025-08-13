# Architecture Overview

## Modes and unification

- **CLI (voice)**: Default mode; continuous listening triggers state transitions and executes actions.
- **Shell (text)**: Interactive text input; simulates voice commands and executes actions.
- **GUI**: Desktop UI for configuration and control; same backend services and config.
- **WebUI**: FastAPI backend + optional React frontend; real-time via WebSocket.

All modes are unified by the `ModeOrchestrator` which selects and starts adapters: text, GUI, Web, OpenWakeWord (opt), Computer Vision (opt), and the Discord/Slack bridge (opt). Each adapter routes recognized commands to the same `CommandExecutor` and shares `StateManager`, `ModelManager`, and `Config`.

## Shared components

- **Config**: Single source of truth for model paths, state models, commands, and advisor settings.
- **StateManager**: Consistent state transitions across modes (idle/computer/chatty).
- **ModelManager**: Loads and swaps active models per state.
- **CommandExecutor**: Executes keypress/URL/system actions; used by all modes.
- **Web API**: Exposes status, config, state, command, advisors, and memory endpoints.
- **Advisors**: `AdvisorsService` with context memory and tools (e.g., browser analyst); accessible via Web API and bridge.
- **Bridge**: External Node.js integration for Discord/Slack; shared-secret auth, HTTP/WebSocket contract.

## Module interactions and state transitions

1. **Adapters** feed recognized text into the shared `CommandExecutor`.
2. `StateManager.update_state()` reacts to wake words and toggles between `idle`, `computer`, and `chatty`.
3. `ModelManager` activates the model list provided by `StateManager` for the new state.
4. `CommandExecutor` performs the configured action for the command.

### State transition map

| Command                                       | New state             |
| --------------------------------------------- | --------------------- |
| `hey_chat_tee`                                | `chatty`              |
| `hey_khum_puter`                              | `computer`            |
| `okay_stop`, `thanks_chat_tee`, `that_ill_do` | `idle`                |
| `toggle_mode`                                 | cycles through states |

## Adapter architecture

Adapters implement a tiny protocol (`start`/`stop` and a `name`) and are registered by the `ModeOrchestrator`. Custom adapters can live in separate packages and plug in without modifying core logic. This plugin model keeps mode-specific code isolated while sharing a common command sink and configuration.

## Solution design mitigations

- **Single business logic path**: Commands flow into `CommandExecutor` from all modes to avoid duplication.
- **Adapters over forks**: Mode-specific behavior isolated in adapters; core logic remains shared.
- **Feature flags**: Config/CLI flags enable optional OpenWakeWord, CV, advisors, and bridge.
- **Consistent config**: One config surface consumed by CLI, GUI, WebUI; docs and examples aligned.
- **Auth isolation**: Web mode can disable auth for local dev (`--no-auth`); production expects auth middleware.
- **Robust testing**: Unit tests for services and APIs; integration tests for Web mode; orchestrator unit tests; coverage targets enforced.
- **Failure containment**: Bridge and tools treated as best-effort; timeouts and allowlists for external calls (browser analyst); graceful degradation.
- **Cross-mode telemetry**: Unified logging; future enhancement includes correlation IDs for tracing across adapters.

## Data flow (high level)

1. Input (voice/text/web/bridge) → Adapter → `StateManager` (optional) → `CommandExecutor` (actions)
2. Advisors input (web/bridge) → `AdvisorsService` → tools/LLM → reply + memory → Web/bridge

## References

- `src/chatty_commander/app/orchestrator.py`
- `src/chatty_commander/web/web_mode.py`
- `src/chatty_commander/advisors/` (service, memory)
- `src/chatty_commander/app/{config,state_manager,model_manager,command_executor}.py`
- `README.md`, `WEBUI_PLAN.md`, `WEBUI_IMPLEMENTATION.md`, `TODO.md`
