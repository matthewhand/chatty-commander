# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Persona:
    name: str
    system: str


DEFAULT_PERSONAS: dict[str, str] = {
    "philosophy_advisor": "Answer concisely in the style of a Stoic philosopher. Cite relevant thinkers when helpful.",
}


def resolve_persona(
    name: str | None, personas_cfg: dict[str, str] | None = None
) -> Persona:
    personas_cfg = personas_cfg or {}
    name = name or "default"
    if name == "default":
        return Persona(name="default", system="Provide helpful, concise answers.")
    system = (
        personas_cfg.get(name)
        or DEFAULT_PERSONAS.get(name)
        or "Provide helpful, concise answers."
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
