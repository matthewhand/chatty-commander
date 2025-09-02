#!/usr/bin/env python3
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

"""
PyQt5-based transparent browser implementation for popup avatar.

This module provides a frameless, transparent window with QWebEngineView
for displaying web content as a desktop overlay, with system tray integration.
"""

import logging
import sys
from pathlib import Path
from typing import Any

try:
    from PyQt5.QtCore import Qt, QUrl, pyqtSignal
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    from PyQt5.QtWidgets import (
        QAction,
        QApplication,
        QMainWindow,
        QMenu,
        QSystemTrayIcon,
        QVBoxLayout,
        QWidget,
    )

    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False

    # Create dummy classes for type hints
    class QMainWindow:
        pass

    class QWebEngineView:
        pass

    class QSystemTrayIcon:
        pass

    class QApplication:
        pass


logger = logging.getLogger(__name__)


class TransparentBrowser(QMainWindow):
    """
    Transparent, frameless browser window for avatar display.

    Features:
    - Frameless window with transparency
    - Web content rendering via QWebEngineView
    - System tray integration
    - Configurable positioning and size
    - CSS injection for transparent backgrounds
    """

    # Signals
    window_closed = pyqtSignal()

    def __init__(self, config: dict[str, Any]):
        super().__init__()
        self.config = config
        self.tray_icon = None
        self.web_view = None

        self._setup_window()
        self._setup_web_view()
        self._setup_system_tray()

    def _setup_window(self):
        """Configure the main window properties."""
        # Window flags for frameless, transparent, always on top
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool  # Prevents taskbar entry
        )

        # Enable transparency
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        # Set window size and position
        width = self.config.get("width", 400)
        height = self.config.get("height", 600)
        x = self.config.get("x", 100)
        y = self.config.get("y", 100)

        self.setGeometry(x, y, width, height)
        self.setWindowTitle("Chatty Commander Avatar")

        # Make window draggable
        self._drag_position = None

    def _setup_web_view(self):
        """Setup the web engine view."""
        self.web_view = QWebEngineView()

        # Set transparent background
        self.web_view.setStyleSheet("background: transparent;")

        # Create central widget and layout
        central_widget = QWidget()
        central_widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web_view)

        self.setCentralWidget(central_widget)

        # Load the avatar page
        url = self.config.get(
            "url", "file:///src/chatty_commander/webui/avatar/index.html"
        )
        if url.startswith("file://") and not url.startswith("file:///"):
            # Convert relative file paths to absolute
            file_path = url[7:]  # Remove 'file://'
            if not file_path.startswith("/"):
                # Relative path, make it absolute
                base_path = Path(__file__).parent.parent.parent.parent
                file_path = str(base_path / file_path)
            url = f"file:///{file_path}"

        logger.info(f"Loading avatar URL: {url}")
        self.web_view.load(QUrl(url))

        # Inject CSS for transparency after page loads
        self.web_view.loadFinished.connect(self._inject_transparency_css)

    def _inject_transparency_css(self):
        """Inject CSS to make web page background transparent."""
        css_code = """
        document.body.style.backgroundColor = 'transparent';
        document.documentElement.style.backgroundColor = 'transparent';

        // Force transparency on common elements
        var style = document.createElement('style');
        style.textContent = `
            body, html {
                background-color: transparent !important;
                background: transparent !important;
            }
            * {
                background-color: transparent !important;
            }
        `;
        document.head.appendChild(style);
        """

        self.web_view.page().runJavaScript(css_code)

    def _setup_system_tray(self):
        """Setup system tray icon and menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray is not available")
            return

        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self)

        # Load icon
        icon_path = self._get_icon_path()
        if icon_path and icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            # Fallback to default icon
            self.tray_icon.setIcon(
                self.style().standardIcon(self.style().SP_ComputerIcon)
            )

        # Create context menu
        tray_menu = QMenu()

        # Show/Hide action
        self.show_action = QAction("Show Avatar", self)
        self.show_action.triggered.connect(self.toggle_visibility)
        tray_menu.addAction(self.show_action)

        tray_menu.addSeparator()

        # Reload action
        reload_action = QAction("Reload", self)
        reload_action.triggered.connect(self.reload_page)
        tray_menu.addAction(reload_action)

        tray_menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("Chatty Commander Avatar")

        # Double-click to toggle visibility
        self.tray_icon.activated.connect(self._tray_icon_activated)

        # Show tray icon
        self.tray_icon.show()

    def _get_icon_path(self) -> Path | None:
        """Get the path to the application icon."""
        # Try different icon locations
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "icon.svg",
            Path(__file__).parent.parent.parent.parent / "icon.png",
            Path(__file__).parent.parent / "assets" / "icon.png",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return None

    def _tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_visibility()

    def toggle_visibility(self):
        """Toggle window visibility."""
        if self.isVisible():
            self.hide()
            self.show_action.setText("Show Avatar")
        else:
            self.show()
            self.raise_()
            self.activateWindow()
            self.show_action.setText("Hide Avatar")

    def reload_page(self):
        """Reload the web page."""
        if self.web_view:
            self.web_view.reload()

    def quit_application(self):
        """Quit the application."""
        if self.tray_icon:
            self.tray_icon.hide()
        self.window_closed.emit()
        QApplication.quit()

    def mousePressEvent(self, event):
        """Handle mouse press for window dragging."""
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging."""
        if event.buttons() == Qt.LeftButton and self._drag_position:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def closeEvent(self, event):
        """Handle window close event."""
        # Hide to tray instead of closing
        if self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self.window_closed.emit()
            event.accept()


def _load_settings() -> dict[str, Any]:
    """Load PyQt5 avatar settings from configuration."""
    try:
        from chatty_commander.app.config import Config

        config = Config.load()

        # Get PyQt5 avatar settings
        pyqt5_config = getattr(config, "pyqt5_avatar", {})
        if isinstance(pyqt5_config, dict):
            return pyqt5_config

        # Fallback to general avatar settings
        avatar_config = getattr(config, "avatar", {})
        if isinstance(avatar_config, dict):
            return avatar_config

    except Exception as e:
        logger.warning(f"Failed to load configuration: {e}")

    # Default settings
    return {
        "url": "file:///src/chatty_commander/webui/avatar/index.html",
        "width": 400,
        "height": 600,
        "x": 100,
        "y": 100,
        "transparent": True,
        "always_on_top": True,
        "frameless": True,
    }


def run_pyqt5_avatar() -> bool:
    """
    Run the PyQt5-based transparent avatar browser.

    Returns:
        bool: True if successful, False if failed or PyQt5 not available
    """
    if not PYQT5_AVAILABLE:
        logger.warning(
            "PyQt5 is not available. Install with: pip install PyQt5 PyQtWebEngine"
        )
        return False

    try:
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Load settings
        settings = _load_settings()

        # Create and show the transparent browser
        browser = TransparentBrowser(settings)

        # Show window initially (can be hidden via tray)
        browser.show()

        logger.info("PyQt5 avatar browser started successfully")

        # Run the application
        return app.exec_() == 0

    except Exception as e:
        logger.error(f"Failed to start PyQt5 avatar browser: {e}")
        return False


if __name__ == "__main__":
    # Direct execution for testing
    logging.basicConfig(level=logging.INFO)
    success = run_pyqt5_avatar()
    sys.exit(0 if success else 1)
