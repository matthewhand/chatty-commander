# Custom Modes, Wakewords, and Personas

This guide shows how to extend ChattyCommander with new modes, wakewords, personas (OpenAI‑Agents), and mode‑specific tools. We will use the real CLI outputs so you can follow along.

Prerequisites
- Installed package provides the `chatty` command (or use the repo’s local wrapper `./chatty`).
- Python 3.11+ environment for development.

1) Inspect current configuration via CLI
- List available commands:
```
$ chatty list
```
- Show top‑level help:
```
$ chatty --help
```
- Configuration help:
```
$ chatty config --help
```

2) Understand the default modes
The default config ships with three modes:
- idle: listens for wakewords like "hey_chat_tee", "hey_khum_puter", and "okay_stop"
- computer: listens for "oh_kay_screenshot" and "okay_stop"
- chatty: no wakewords (chatty stops listening), persona "chatty", tools [avatar_talkinghead, tts, stt]

To view the config file path and contents during development, open `config.json` in the repo root.

3) Add a custom mode
We’ll add a new mode "focus" with a custom wakeword and persona.

Example config snippet (merge into your `config.json`):
```json
{
  "modes": {
    "idle": {"wakewords": ["hey_chat_tee", "hey_khum_puter", "okay_stop"], "persona": null, "tools": ["keypress", "http"]},
    "computer": {"wakewords": ["oh_kay_screenshot", "okay_stop"], "persona": null, "tools": ["keypress"]},
    "chatty": {"wakewords": [], "persona": "chatty", "tools": ["avatar_talkinghead", "tts", "stt"]},
    "focus": {"wakewords": ["focus_on"], "persona": "analyst", "tools": ["browser"]}
  },
  "state_models": {
    "idle": ["hey_chat_tee", "hey_khum_puter", "okay_stop", "lights_on", "lights_off"],
    "computer": ["oh_kay_screenshot", "okay_stop"],
    "chatty": ["wax_poetic", "thanks_chat_tee", "that_ill_do", "okay_stop"],
    "focus": ["okay_stop"]
  }
}
```
Notes:
- You can add any mode name and associated wakewords.
- If a wakeword appears in multiple modes, the mapping is defined by the first occurrence in the `modes` dictionary.

4) Verify wakeword mapping
After editing `config.json`, run the app or use a small validation:
- Trigger a mode switch by wakeword (programmatic example):
```python
from src.chatty_commander.app.state_manager import StateManager
sm = StateManager()
print("Before:", sm.current_state)
sm.update_state("focus_on")
print("After:", sm.current_state)
```
You should see the state change to `focus`.

5) Personas and tools per mode
- Each mode can set a `persona` string key used by the advisors (OpenAI‑Agents) system.
- `tools` is a logical list of tool tags available in a mode (e.g., ["browser", "avatar_talkinghead"]).
- Advisors are enabled/configured via the `advisors` section in `config.json` (see docs/OPENAI_AGENTS_ADVISOR.md).

6) Switching modes from an advisor tool (preview)
- We include a static tool `switch_mode(mode)` that returns a directive string `SWITCH_MODE:<mode>`.
- AdvisorsService recognizes this directive and changes the app mode.
- In a real `openai-agents` setup, this function would be registered as an `as_tool` callable.

7) CLI examples (real outputs)
- Show system command help:
```
$ chatty system --help
usage: chatty-commander system [-h] {start-on-boot,updates} ...
```
- Start‑on‑boot help:
```
$ chatty system start-on-boot --help
usage: chatty-commander system start-on-boot [-h] {enable,disable,status}
```
- Config help:
```
$ chatty config --help
usage: chatty-commander config [-h] [--interactive] [--list] [--set-listen-for KEY VALUE] [--set-mode MODE VALUE] [--set-model-action MODEL ACTION] [--set-state-model STATE MODELS] [--show] [--validate] [--export PATH] {wizard} ...
```
- List commands (example):
```
$ chatty list
Available commands:
- cycle_window
- lights_off
- lights_on
- oh_kay_screenshot
- okay_send
- okay_stop
- paste
- submit
- take_screenshot
- thanks_chat_tee
- that_ill_do
- wax_poetic
```

8) Tips
- You can create multiple new modes and wire different personas. The StateManager reads the mode list dynamically so no code change is needed.
- Use the agents/blueprints REST routes to define teams of agents and wire handoff triggers (`/api/v1/agents/...`).
- For production, use the PyInstaller‑built `chatty` binary for a no‑Python install.

For more details, see:
- docs/OPENAI_AGENTS_ADVISOR.md (advisor, providers, and platform bridge design)
- src/chatty_commander/app/config.py (modes and advisors config handling)
- src/chatty_commander/advisors/providers.py (provider + openai-agents integration)
- src/chatty_commander/advisors/service.py (tool directive handling and switching modes)
