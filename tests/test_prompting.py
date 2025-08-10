from chatty_commander.advisors.prompting import (
    Persona,
    build_prompt,
    build_provider_prompt,
    resolve_persona,
)


def test_build_prompt_envelopes_text():
    persona = Persona(name="philosophy_advisor", system="Answer like a Stoic philosopher.")
    p = build_prompt(persona, "What is virtue?")
    assert "[system:philosophy_advisor]" in p
    assert "Stoic philosopher" in p
    assert "[user] What is virtue?" in p


def test_build_provider_prompt_modes():
    persona = Persona(name="p1", system="S")
    c = build_provider_prompt("completion", persona, "x")
    r = build_provider_prompt("responses", persona, "x")
    assert c.startswith("[mode:completion]")
    assert r.startswith("[mode:responses]")


def test_resolve_persona_uses_defaults():
    p = resolve_persona("philosophy_advisor")
    assert "Stoic" in p.system


