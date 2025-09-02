# OpenAI-Agents Advisor Design

## Design summary

- **Core SDK**: `openai-agents` (local), derived from OpenAI Swarm; supports MCP, handoff, and `as_tool` with BYO‑LLM.
- **LLM API mode**: Default to `completion` for broad compatibility (e.g., GPT‑OSS20B and other local/uncensored models). `responses` has limited third‑party support.
- **Platforms**: Modular adapters for Discord and Slack first; extensible to other messengers.
- **Advisors**: Per‑app/system prompts (e.g., philosophy‑focused) with tab‑aware context switching and persistent identity across apps.
- **Avatar (optional)**: 3D anime‑style avatar with lip‑sync via TalkingHead.
- **Browser/analyst**: Built‑in analyst/browser capability “baked in as a feature”.
- **Goal**: Personal AI advisors with modular multi‑platform UI and LLM backend; hackathon/contest‑ready.

## Why `completion` by default

`openai-agents` defaults to the `responses` API which currently has limited third‑party implementations. Switching the default to `completion` mode enables immediate compatibility with a wide range of local models and providers.

## Components

- **Agent core**: `openai-agents` with MCP, handoff, and tool invocation
- **LLM providers**: BYO‑LLM (local), default API = `completion`
- **Platform adapters**: External Node.js bridge for Discord/Slack (shared contract)
- **Context manager**: Tab/app‑aware identity and system prompt selection
- **Tools**: Browser/analyst toolset available to advisors
- **Avatar (opt‑in)**: TalkingHead runtime for 3D avatar + lip‑sync
- **Orchestrator**: Mode orchestrator unifies text, GUI, WebUI, wakeword, CV, and Discord bridge

## MVP scope

- Integrate `openai-agents` and enable MCP, handoff, and `as_tool`
- Default to `completion` API; config flag to switch to `responses`
- BYO‑LLM wiring for local models (e.g., GPT‑OSS20B)
- Node.js bridge API for Discord and Slack adapters (external repo)
- Tab‑aware context switching with per‑app/system prompts
- Built‑in browser/analyst tool available to advisors

## Enhancements

- Optional 3D avatar via TalkingHead with runtime toggle
- Persona library (e.g., philosophy‑focused) and quick switching
- Local model prompt templates and safety/policy toggles
- Rich platform presence/features across Discord/Slack

## Quickstart (preview)

1. Configure advisors (planned keys):

```json
{
  "advisors": {
    "enabled": true,
    "llm_api_mode": "completion",
    "model": "gpt-oss20b",
    "platforms": ["discord", "slack"],
    "personas": { "default": "philosophy_advisor" },
    "features": { "browser_analyst": true, "avatar_talkinghead": false }
  }
}
```

2. Run the web/CLI as usual; platform adapters will register when configured.

1. Toggle avatar and personas via settings (to be wired to config/state manager).

### Node.js bridge API (contract preview)

- Transport: HTTP + optional WebSocket
- Inbound event → Python: `POST /bridge/event`
  - Payload: `{ platform: "discord"|"slack", type, channel, user, text, attachments? }`
- Outbound message ← Python: `POST /bridge/reply`
  - Payload: `{ platform, channel, thread_ts?, text, attachments? }`
- Auth: shared secret header (e.g., `X-Bridge-Token`)
- Retries/backoff: documented in Node side; Python treats delivery as best-effort

Note: Implementation is tracked in `TODO.md` under “OpenAI‑Agents advisor (MVP/Enhancements)”.

## Usage examples

- Enable advisors at runtime with web server and Discord bridge:

  ```bash
  export ADVISORS_BRIDGE_TOKEN=secret
  export ADVISORS_BRIDGE_URL=http://localhost:3001
  uv run python main.py --orchestrate --web --enable-discord-bridge --advisors --port 8100
  ```

- Persona configuration (philosophy advisor):

  ```json
  {
    "advisors": {
      "enabled": true,
      "llm_api_mode": "completion",
      "model": "gpt-oss20b",
      "personas": { "default": "philosophy_advisor" }
    }
  }
  ```

- Summarize via API:

  ```bash
  curl -s -X POST http://localhost:8100/api/v1/advisors/message \
    -H 'Content-Type: application/json' \
    -d '{"platform":"discord","channel":"c1","user":"u1","text":"summarize https://example.com"}'
  ```
