# MIT License
#
# Copyright (c) 2024 mhand
#
# Tests for GUI optional-dependency degradation (PyQt5 / pystray / pywebview).
"""Regression tests for the GUI modules' optional-dependency handling.

PyQt5, pystray and pywebview are all OPTIONAL. These tests ensure the modules
import cleanly (degrade, not crash) when those libraries are absent, that the
tray icon is resolved relative to the package rather than the process CWD, and
that quitting the tray tears the webview window down instead of leaking the
worker thread.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def test_pyqt5_avatar_imports_without_pyqt5(monkeypatch):
    """The module must import with PyQt5 absent without raising NameError.

    Previously ``TransparentBrowser`` referenced ``pyqtSignal`` at class
    definition time while the ImportError fallback only stubbed a handful of
    classes, so importing the module crashed with NameError when PyQt5 was not
    installed.
    """
    # Simulate PyQt5 (and its submodules) being unavailable.
    for name in list(sys.modules):
        if name == "PyQt5" or name.startswith("PyQt5."):
            monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.setitem(sys.modules, "PyQt5", None)
    monkeypatch.delitem(
        sys.modules, "chatty_commander.gui.pyqt5_avatar", raising=False
    )

    module = importlib.import_module("chatty_commander.gui.pyqt5_avatar")

    # Imports cleanly and reports PyQt5 as unavailable.
    assert module.PYQT5_AVAILABLE is False
    # The class object exists (definition succeeded) and its signal attribute
    # was stubbed rather than blowing up.
    assert module.TransparentBrowser is not None
    # run_pyqt5_avatar degrades to a clean False rather than crashing.
    assert module.run_pyqt5_avatar() is False


def test_tray_popup_imports_without_optional_deps(monkeypatch):
    """tray_popup imports with pystray/pywebview absent and reports failure."""
    for name in ("pystray", "webview"):
        monkeypatch.setitem(sys.modules, name, None)
    monkeypatch.delitem(
        sys.modules, "chatty_commander.gui.tray_popup", raising=False
    )

    module = importlib.import_module("chatty_commander.gui.tray_popup")

    # pystray is treated as missing -> return code 2 (deps missing).
    rc = module.run_tray_popup(SimpleNamespace(config_data={}), logger=_DummyLogger())
    assert rc == 2


def test_tray_icon_paths_are_package_relative():
    """Icon candidate paths must be resolved relative to the package, not CWD."""
    from chatty_commander.gui import tray_popup

    paths = tray_popup._icon_candidate_paths()
    assert paths, "expected at least one candidate icon path"
    pkg_dir = Path(tray_popup.__file__).resolve().parent
    for p in paths:
        assert p.is_absolute()
        # None of the candidates should be a bare CWD-relative "icon.png".
        assert p != Path("icon.png")
    # At least one candidate lives under the package tree.
    assert any(str(pkg_dir.parent) in str(p) or str(pkg_dir) in str(p) for p in paths)


def test_icon_image_resolves_relative_to_package(monkeypatch, tmp_path):
    """_icon_image loads from a package-relative path regardless of CWD."""
    pytest.importorskip("PIL")
    from PIL import Image

    from chatty_commander.gui import tray_popup

    # Create a fake icon at a controlled candidate location.
    fake_icon = tmp_path / "icon.png"
    Image.new("RGBA", (4, 4)).save(fake_icon)
    monkeypatch.setattr(
        tray_popup, "_icon_candidate_paths", lambda: [fake_icon]
    )

    # Change CWD to somewhere without an icon.png to prove CWD is irrelevant.
    monkeypatch.chdir(tmp_path / "..")

    img = tray_popup._icon_image()
    assert img is not None


def test_on_quit_destroys_webview_before_join(monkeypatch):
    """Quitting signals pywebview to close so the worker thread is not leaked.

    The worker thread runs a blocking ``_open_window`` (emulating
    ``webview.start()``). ``on_quit`` must destroy the webview window so the
    worker returns and the subsequent ``join`` completes, leaving no live
    daemon thread behind.
    """
    import threading

    from chatty_commander.gui import tray_popup

    destroyed = {"called": False}
    stop_event = threading.Event()

    class _FakeWindow:
        def destroy(self):
            destroyed["called"] = True
            stop_event.set()

    fake_webview = SimpleNamespace(
        windows=[_FakeWindow()],
        destroy_window=lambda: None,
    )
    monkeypatch.setattr(tray_popup, "webview", fake_webview)

    worker_done = threading.Event()

    # Replace _open_window with a blocking stub that returns only once the
    # window is destroyed (mirrors webview.start() blocking semantics).
    def _blocking_open(_settings, _logger):
        try:
            stop_event.wait(timeout=5.0)
        finally:
            worker_done.set()

    monkeypatch.setattr(tray_popup, "_open_window", _blocking_open)

    captured: dict[str, object] = {}

    class _FakeMenuItem:
        def __init__(self, text, callback=None, default=False):
            self.text = text
            self.callback = callback

    class _FakeMenu:
        def __init__(self, *items):
            self.items = items

    class _FakeIcon:
        def __init__(self, *a, **k):
            self.menu = k.get("menu")

        def run(self):
            for item in self.menu.items:
                if item.text == "Open":
                    captured["open"] = item.callback
                if item.text == "Quit":
                    captured["quit"] = item.callback

        def stop(self):
            pass

    fake_pystray = SimpleNamespace(Icon=_FakeIcon)
    monkeypatch.setattr(tray_popup, "pystray", fake_pystray)
    # Menu / MenuItem only exist as module globals when pystray imported
    # successfully; inject them for this test (raising=False handles absence).
    monkeypatch.setattr(tray_popup, "Menu", _FakeMenu, raising=False)
    monkeypatch.setattr(tray_popup, "MenuItem", _FakeMenuItem, raising=False)

    rc = tray_popup.run_tray_popup(SimpleNamespace(config_data={}), _DummyLogger())
    assert rc == 0

    open_handler = captured["open"]
    quit_handler = captured["quit"]

    # Open a popup -> spawns the blocking worker thread.
    open_handler(_FakeIcon(), None)

    # Quit -> must destroy the window and join the worker cleanly.
    quit_handler(_FakeIcon(), None)

    assert destroyed["called"] is True
    # The worker returned (was not abandoned): its finally-block fired.
    assert worker_done.wait(timeout=2.0) is True


class _DummyLogger:
    def info(self, *a, **k):
        pass

    def warning(self, *a, **k):
        pass

    def error(self, *a, **k):
        pass
