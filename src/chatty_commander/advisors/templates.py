from __future__ import annotations

from typing import Dict


_TEMPLATES: Dict[str, str] = {
    # key format: persona|api_mode|model (wildcards allowed with *)
    "philosophy_advisor|completion|*": "[tpl:stoic:completion] [sys] {system}\n[user] {text}",
    "philosophy_advisor|responses|*": "[tpl:stoic:responses] [sys] {system}\n[user] {text}",
    "default|completion|*": "[tpl:default:completion] [sys] {system}\n[user] {text}",
    "default|responses|*": "[tpl:default:responses] [sys] {system}\n[user] {text}",
}


def get_prompt_template(model: str, persona_name: str, api_mode: str) -> str:
    persona_name = persona_name or "default"
    api_mode = (api_mode or "completion").lower()
    model = model or "*"
    # Exact match
    key_exact = f"{persona_name}|{api_mode}|{model}"
    if key_exact in _TEMPLATES:
        return _TEMPLATES[key_exact]
    # Fallback persona/api wildcard
    key_wild = f"{persona_name}|{api_mode}|*"
    if key_wild in _TEMPLATES:
        return _TEMPLATES[key_wild]
    # Default persona
    key_def = f"default|{api_mode}|*"
    return _TEMPLATES.get(key_def, "[sys] {system}\n[user] {text}")


def render_with_template(template: str, *, system: str, text: str) -> str:
    return template.format(system=system, text=text)


