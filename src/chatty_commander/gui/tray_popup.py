from __future__ import annotations

"""
Tray popup GUI using pystray (system tray) and pywebview (embedded browser).
Best-effort transparency and frameless window with OS fallbacks.
"""

import threading
from pathlib import Path
from typing import Any, Optional

try:
    import pystray
    from pystray import Menu, MenuItem
except Exception:  # pragma: no cover
    pystray = None  # type: ignore

try:
    import webview
except Exception:  # pragma: no cover
    webview = None  # type: ignore


def _load_settings(config: Any) -> dict[str, Any]:
    defaults = {
        "url": "https://your-url.example",
        "transparent": True,
        "width": 420,
        "height": 640,
        "always_on_top": True,
    }
    data = getattr(config, "config_data", {}) or {}
    gui = data.get("gui", {})
    popup = gui.get("popup", {})
    settings = {**defaults, **popup}
    # Coerce types
    settings["url"] = str(settings.get("url", defaults["url"]))
    settings["transparent"] = bool(settings.get("transparent", defaults["transparent"]))
    settings["always_on_top"] = bool(
        settings.get("always_on_top", defaults["always_on_top"])
    )
    try:
        settings["width"] = int(settings.get("width", defaults["width"]))
        settings["height"] = int(settings.get("height", defaults["height"]))
    except Exception:
        settings["width"], settings["height"] = defaults["width"], defaults["height"]
    return settings


def _icon_image() -> Optional["Image.Image"]:
    """
    Try to load a tray icon image.

    - Prefer icon.png if present (since PIL cannot rasterize SVG without extra deps).
    - If only icon.svg exists, skip and allow default OS tray icon.
    """
    try:
        from PIL import Image  # type: ignore
    except Exception:
        return None

    icon_path_png = Path("icon.png")
    if icon_path_png.exists():
        try:
            return Image.open(icon_path_png)
        except Exception:
            return None
    # If only SVG exists, we skip rasterization here (no cairosvg dependency in core)
    return None


def _open_window(settings: dict[str, Any], logger) -> None:
    if webview is None:
        logger.error("pywebview is not installed; cannot open browser window")
        return

    url = settings["url"]
    width = settings["width"]
    height = settings["height"]
    transparent = settings["transparent"]
    always_on_top = settings["always_on_top"]

    # Best-effort transparency/frameless
    frameless = True
    enable_transparency = transparent

    try:
        # Some backends support transparency better with the "qt" GUI; if not available, webview.start will fallback.
        webview.create_window(
            title="ChattyCommander",
            url=url,
            width=width,
            height=height,
            frameless=frameless,
            easy_drag=True,  # allow dragging a frameless window
            on_top=always_on_top,
            transparent=enable_transparency,
        )
        webview.start(gui=None, http_server=False)
    except Exception as e:
        # Fallback: retry without transparency/frameless
        try:
            logger.warning(f"Transparent/frameless not supported, falling back: {e}")
            webview.create_window(
                title="ChattyCommander",
                url=url,
                width=width,
                height=height,
                frameless=False,
                on_top=always_on_top,
                transparent=False,
            )
            webview.start(gui=None, http_server=False)
        except Exception as e2:
            logger.error(f"Failed to open webview window: {e2}")


def run_tray_popup(config: Any, logger) -> int:
    """
    Start a system tray icon that can open a popup browser window showing
    config.gui.popup.url.

    Returns:
        int: 0 on normal exit, 2 if dependencies are missing.
    """
    if pystray is None:
        logger.error("pystray is not installed; cannot create system tray icon")
        return 2

    icon_img = _icon_image()

    def on_open(_icon, _item):
        # open window on a background thread to avoid blocking the tray loop
        settings = _load_settings(config)
        threading.Thread(target=_open_window, args=(settings, logger), daemon=True).start()

    def on_quit(_icon, _item):
        _icon.stop()

    menu = Menu(
        MenuItem("Open", on_open, default=True),
        MenuItem("Quit", on_quit),
    )
    icon = pystray.Icon("chatty_commander", icon=icon_img, title="ChattyCommander", menu=menu)

    # Run tray loop in foreground until quit selected
    icon.run()
    return 0