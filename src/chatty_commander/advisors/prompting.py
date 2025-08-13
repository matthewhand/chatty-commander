from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Persona:
    name: str
    system: str


DEFAULT_PERSONAS: dict[str, str] = {
    "philosophy_advisor": "Answer concisely in the style of a Stoic philosopher. Cite relevant thinkers when helpful.",
}


def resolve_persona(name: str | None, personas_cfg: dict[str, str] | None = None) -> Persona:
    personas_cfg = personas_cfg or {}
    name = name or "default"
    if name == "default":
        return Persona(name="default", system="Provide helpful, concise answers.")
    system = (
        personas_cfg.get(name) or DEFAULT_PERSONAS.get(name) or "Provide helpful, concise answers."
    )
    return Persona(name=name, system=system)


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
