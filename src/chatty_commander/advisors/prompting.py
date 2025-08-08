from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Persona:
    name: str
    system: str


def build_prompt(persona: Persona, user_text: str) -> str:
    """Create a deterministic prompt envelope; stubbed for tests.

    Real implementation would format for a given provider model.
    """
    return f"[system:{persona.name}] {persona.system}\n[user] {user_text}"


def build_provider_prompt(api_mode: str, persona: Persona, user_text: str) -> str:
    """Envelope that varies slightly by provider API mode for testing.

    Without making real provider calls, we distinguish completion vs responses.
    """
    base = build_prompt(persona, user_text)
    if api_mode.lower() == "responses":
        return f"[mode:responses]\n{base}"
    return f"[mode:completion]\n{base}"


