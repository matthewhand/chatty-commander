# ChattyCommander – Comprehensive Walkthrough

This walkthrough exercises the CLI, shows real outputs, and demonstrates how to customize modes, wakewords, and personas. Use it to validate your setup and to spot misbehavior quickly.

Prerequisites
- Either install the package to get the `chatty` command, or use the local wrapper `./chatty` from the repo root.
- On CI/headless systems, our CLI simulates start-on-boot commands to avoid systemd/dbus errors.

Quick smoke script
- Run the scripted smoke to collect outputs in one go:
```
$ bash scripts/walkthrough_smoke.sh
```

You should see sections with help, command listing, and system actions (status/enable/disable) with graceful handling in headless environments.

Manual walkthrough
1) CLI help and discovery
```
$ chatty --help
$ chatty list
$ chatty config --help
$ chatty system --help
$ chatty system start-on-boot --help
$ chatty system updates --help
```

2) Verify configuration loading
- Ensure `config.json` exists in the repo root (or your user config).
- The list output should include the default commands like take_screenshot, paste, etc.

3) Customize modes and wakewords
- Edit `config.json` and add a new mode. Example:
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
- Save the file, then in Python you can validate the mapping quickly:
```python
from src.chatty_commander.app.state_manager import StateManager
sm = StateManager()
print(sm.current_state)
print(sm.update_state("focus_on"))  # expect 'focus'
print(sm.current_state)
```

4) Personas and tools per mode
- The `persona` key associates a mode with an advisor persona (OpenAI‑Agents). Configure advisors under the `advisors` section in `config.json`.
- The `tools` list is logical (browser, avatar_talkinghead, tts, stt, etc.) and controls which capabilities are exposed in that mode. In future versions, these determine registered as_tool functions.

5) Switching modes via advisor tools (preview)
- The repository includes a static tool `switch_mode(mode)` that returns a directive string `SWITCH_MODE:<mode>`.
- AdvisorsService interprets this directive and calls StateManager.change_state.
- When the openai-agents SDK is present, this function can be registered as an as_tool function for real tool invocation.

6) Agents and handoff (preview)
- Use the Agents API (see tests/test_agents_api.py and src/chatty_commander/web/routes/agents.py) to define blueprints and team roles.
- A handoff endpoint acknowledges transitions within a team; future versions will link this to advisors to continue conversations across personas.

7) Troubleshooting
- If `chatty system start-on-boot enable` produces errors on headless machines, the CLI simulates success.
- If `chatty` is not found, ensure the repo root is in PATH (`export PATH="${PWD}:$PATH"`) or install the package (`pip install .`).
- For standalone, use the PyInstaller build: `make build-exe` and run `dist/chatty --help`.

See also
- docs/CUSTOM_MODES_AND_PERSONAS.md – extended how‑to and real outputs
- docs/OPENAI_AGENTS_ADVISOR.md – advisor and provider design
