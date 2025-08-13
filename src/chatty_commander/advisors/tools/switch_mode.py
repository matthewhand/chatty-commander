from __future__ import annotations


def switch_mode(mode: str) -> str:
    """Tool: Request a mode switch.

    Returns a structured directive that orchestration layers can intercept.
    Example return: "SWITCH_MODE:idle"
    """
    mode = (mode or "").strip()
    if not mode:
        return "SWITCH_MODE:invalid"
    return f"SWITCH_MODE:{mode}"
