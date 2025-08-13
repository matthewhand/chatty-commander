"""
Avatar GUI Launcher (TalkingHead via pywebview)

Summary
- Provides a lightweight, transparent desktop surface for the Chatty Commander avatar using
  pywebview. The window is frameless, draggable, always-on-top, and attempts transparency for a
  seamless overlay experience.

Design goals
- Keep the avatar front-end (HTML/JS) decoupled from Python by loading a local index.html
  (src/chatty_commander/webui/avatar/index.html). This enables independent iteration on visuals.
- Fail gracefully in environments where transparency or the GUI backend is not supported, retrying
  without transparency.
- Remain headless-safe: run_gui_mode guards for DISPLAY and returns non-fatally on CI.

Usage
- from chatty_commander.avatars.avatar_gui import run_avatar_gui
- run_avatar_gui()  # opens the avatar window; returns 0 on success, 2 on dependency issues

Notes
- Replace the placeholder index.html with the real TalkingHead build output.
- Transparency and frameless support varies by OS/backend; code falls back when needed.
"""
from __future__ import annotations

from pathlib import Path

try:
    import webview  # type: ignore
except Exception:  # pragma: no cover
    webview = None  # type: ignore


def _avatar_index_path() -> Path:
    # File location: src/chatty_commander/avatars/avatar_gui.py
    # We want:      src/chatty_commander/webui/avatar/index.html
    here = Path(__file__).resolve()
    root = here.parent.parent  # up from avatars/ to chatty_commander/
    return root / "webui" / "avatar" / "index.html"


def run_avatar_gui(debug: bool = True) -> int | None:
    """Create and run the transparent pywebview window for the avatar.

    Returns 0 on success, 2 if missing dependencies, or None if silently skipped.
    """
    if webview is None:
        print("ERROR: pywebview is not installed; cannot launch the avatar GUI.")
        return 2

    index_html = _avatar_index_path()
    if not index_html.exists():
        print(f"ERROR: Could not find avatar entry point at {index_html}")
        return 2

    url = index_html.resolve().as_uri()
    try:
        webview.create_window(
            title="Chatty Commander Avatar",
            url=url,
            width=800,
            height=600,
            frameless=True,
            easy_drag=True,
            on_top=True,
            transparent=True,
        )
        webview.start(debug=debug, gui=None, http_server=False)
        return 0
    except Exception as e:
        print(f"WARNING: Transparent/frameless not supported or failed ({e}); retrying without it...")
        try:
            webview.create_window(
                title="Chatty Commander Avatar",
                url=url,
                width=800,
                height=600,
                frameless=False,
                on_top=False,
                transparent=False,
            )
            webview.start(debug=debug, gui=None, http_server=False)
            return 0
        except Exception as e2:
            print(f"ERROR: Failed to open avatar window: {e2}")
            return 2


if __name__ == "__main__":
    run_avatar_gui()
