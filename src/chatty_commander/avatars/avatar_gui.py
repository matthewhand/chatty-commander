"""
TalkingHead 3D Avatar Launcher (pywebview)

Purpose:
- Provide a transparent, frameless, always-on-top desktop window that hosts the web-based
  TalkingHead avatar UI for Chatty Commander.
- Keep GUI concerns decoupled from the Python backend by embedding a local index.html via pywebview.

Behavior:
- Prefers loading the built avatar UI from src/chatty_commander/webui/avatar/index.html.
- Prints a helpful error if the file is missing or pywebview is not installed.
- Designed to be headless-friendly when called from main.run_gui_mode which performs DISPLAY checks first.

Usage:
- from chatty_commander.gui.avatar_gui import run_avatar_gui
- run_avatar_gui()  # blocks until the window is closed

Notes:
- Replace the placeholder index.html with the real TalkingHead build output.
- Transparency support varies by OS and backend; the code falls back if needed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    import webview  # type: ignore
except Exception:  # pragma: no cover
    webview = None  # type: ignore


def _avatar_index_path() -> Path:
    # File location: src/chatty_commander/gui/avatar_gui.py
    # We want:      src/chatty_commander/webui/avatar/index.html
    here = Path(__file__).resolve()
    root = here.parent.parent  # up from gui/ to chatty_commander/
    return root / "webui" / "avatar" / "index.html"


def run_avatar_gui(debug: bool = True) -> Optional[int]:
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
