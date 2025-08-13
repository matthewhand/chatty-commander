# Agent Blueprint Management & Team Orchestration

This document outlines the blueprint schema, APIs, and UI integration for managing agent personas and teams.

## Blueprint Schema (initial)
- Fields: name, description, persona_prompt, capabilities[], team_role?, handoff_triggers[]
- Natural language parser: placeholder heuristic parser; will be replaced by LLM-based extractor.

## API Endpoints
- POST /api/v1/agents/blueprints: create from structured blueprint or NL description
- GET /api/v1/agents/blueprints: list all
- PUT /api/v1/agents/blueprints/{agent_id}: update
- DELETE /api/v1/agents/blueprints/{agent_id}: delete (with simple safety checks)
- GET /api/v1/agents/team: team roles/agents overview
- POST /api/v1/agents/team/handoff: acknowledge handoff (future: orchestrate)

## UI Integration
- Settings section: manage agents, create/destroy, visualize relationships
- Real-time status via avatar WS; theme mapping via persona -> theme mapping

## Next
- Persist blueprints and team state
- Integrate with openai-agents to dynamically create/destroy agents
- Add LLM-based parser with constrained outputs
