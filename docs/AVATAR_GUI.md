# Avatar GUI Protocol and Configuration

This document describes how the avatar UI (TalkingHead) integrates with Chatty Commander.

## WebSocket Endpoint

- URL: `/avatar/ws`
- Messages:
  - `agent_state_change`: `{ data: { agent_id, persona_id, state, message?, progress?, timestamp }, timestamp }`
  - `tool_call_start`: `{ data: { agent_id, tool? }, timestamp }`
  - `tool_call_end`: `{ data: { agent_id, tool? }, timestamp }`
  - `handoff_start`: `{ data: { agent_id, to_persona, reason? }, timestamp }`
  - `handoff_complete`: `{ data: { agent_id, persona_id }, timestamp }`

States include: `idle`, `thinking`, `processing`, `tool_calling`, `responding`, `error`, `handoff`.

## Animation Discovery

- HTTP: `GET /avatar/animations?dir=...`
  - Scans a directory for animation assets and infers a category by filename hints.
  - Response: `{ root, count, animations: [{ name, file, ext, size?, category }] }`

## Settings API

- HTTP: `GET /avatar/config`, `PUT /avatar/config`
  - Schema includes: `animations_dir`, `enabled`, `defaults`, `state_map`, `category_map`.
  - Settings persist via the Config manager.

## UI Behavior (Reference)

- The UI subscribes to `/avatar/ws` and maps messages to animations:
  - `agent_state_change` -> state animation
  - `tool_call_start`/`tool_call_end` -> hacking/processing animations
  - `handoff_start` / `handoff_complete` -> transition animation and theme swap
- The UI fetches `GET /avatar/animations` to list available animations and `GET /avatar/config` to apply mappings.

## Intelligent Animation Selection (Optional)

- Future endpoint: `POST /avatar/animation/choose` that returns `{ label, confidence, rationale? }` for a given text.
- UI uses labels to suggest animation hints with graceful fallback.

## Local Development Tips

- Launch server in web mode: `uv run python -m src.chatty_commander.main --web --no-auth`
- Launch avatar UI via GUI: `uv run python -m src.chatty_commander.main --gui`
- Default client script in `webui/avatar/index.html` attempts WS connection to `ws://localhost:8100/avatar/ws`.
