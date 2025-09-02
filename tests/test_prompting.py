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

from chatty_commander.advisors.prompting import (
    Persona,
    build_prompt,
    build_provider_prompt,
    resolve_persona,
)


def test_build_prompt_envelopes_text():
    persona = Persona(
        name="philosophy_advisor", system="Answer like a Stoic philosopher."
    )
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
