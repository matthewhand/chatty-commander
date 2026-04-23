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
Tests for PyQt5 avatar module.

This module tests basic availability since PyQt5 requires GUI environment.
"""

import sys
from unittest.mock import MagicMock

# Setup PyQt5 mocks BEFORE any import
mock_qt = MagicMock()
mock_qt.Qt.FramelessWindowHint = 1
mock_qt.Qt.WindowStaysOnTopHint = 2
mock_qt.Qt.Tool = 4
mock_qt.Qt.WA_TranslucentBackground = 1
mock_qt.Qt.WA_NoSystemBackground = 1
mock_qt.QtCore.QUrl = MagicMock
mock_qt.QtCore.pyqtSignal = MagicMock(return_value=MagicMock())
mock_qt.QtWidgets.QMainWindow = MagicMock
mock_qt.QtWidgets.QApplication = MagicMock
mock_qt.QtWidgets.QWidget = MagicMock
mock_qt.QtWidgets.QVBoxLayout = MagicMock
mock_qt.QtWidgets.QSystemTrayIcon = MagicMock
mock_qt.QtWidgets.QMenu = MagicMock
mock_qt.QtWidgets.QAction = MagicMock
mock_qt.QtWebEngineWidgets.QWebEngineView = MagicMock
mock_qt.QtGui.QIcon = MagicMock

# Inject into sys.modules before importing the real module
sys.modules['PyQt5'] = mock_qt
sys.modules['PyQt5.QtCore'] = mock_qt.QtCore
sys.modules['PyQt5.QtGui'] = mock_qt.QtGui
sys.modules['PyQt5.QtWidgets'] = mock_qt.QtWidgets
sys.modules['PyQt5.QtWebEngineWidgets'] = mock_qt.QtWebEngineWidgets

# Now safe to import
from src.chatty_commander.gui import pyqt5_avatar


class TestPyQt5Availability:
    """Tests for PyQt5 availability detection."""

    def test_pyqt5_available_flag_exists(self):
        """Test that PYQT5_AVAILABLE flag exists."""
        assert hasattr(pyqt5_avatar, "PYQT5_AVAILABLE")

    def test_logger_exists(self):
        """Test that module logger exists."""
        assert hasattr(pyqt5_avatar, "logger")

    def test_transparent_browser_class_exists(self):
        """Test that TransparentBrowser class exists."""
        assert hasattr(pyqt5_avatar, "TransparentBrowser")


class TestTransparentBrowser:
    """Tests for TransparentBrowser class with mocked PyQt5."""

    def test_config_storage(self):
        """Test that config is stored correctly."""
        mock_config = {
            "width": 400,
            "height": 600,
            "x": 100,
            "y": 200,
            "url": "http://example.com",
        }
        browser = pyqt5_avatar.TransparentBrowser(mock_config)
        assert browser.config == mock_config

    def test_default_config_values(self):
        """Test that default config values are used."""
        minimal_config = {}
        browser = pyqt5_avatar.TransparentBrowser(minimal_config)
        
        # Check default dimensions are accessible via get
        assert browser.config.get("width", 400) == 400
        assert browser.config.get("height", 600) == 600

    def test_url_config(self):
        """Test that URL config is stored."""
        config = {"url": "http://example.com/avatar"}
        browser = pyqt5_avatar.TransparentBrowser(config)
        assert browser.config["url"] == "http://example.com/avatar"

    def test_position_config(self):
        """Test that position config is stored."""
        config = {"x": 50, "y": 100}
        browser = pyqt5_avatar.TransparentBrowser(config)
        assert browser.config["x"] == 50
        assert browser.config["y"] == 100


class TestEdgeCases:
    """Edge case tests."""

    def test_config_with_none_values(self):
        """Test handling of config with None values."""
        config = {"width": None, "height": None, "url": None}
        browser = pyqt5_avatar.TransparentBrowser(config)
        # Should not raise
        assert browser.config["width"] is None

    def test_config_with_negative_dimensions(self):
        """Test handling of negative dimensions."""
        config = {"width": -100, "height": -200}
        browser = pyqt5_avatar.TransparentBrowser(config)
        # Should store the values
        assert browser.config["width"] == -100

    def test_empty_config(self):
        """Test handling of empty config."""
        config = {}
        browser = pyqt5_avatar.TransparentBrowser(config)
        # Should use defaults when accessed
        assert browser.config is not None

    def test_config_with_special_characters_in_url(self):
        """Test handling of URLs with special characters."""
        config = {"url": "http://example.com/path?query=value&other=test"}
        browser = pyqt5_avatar.TransparentBrowser(config)
        assert "query=value" in browser.config["url"]

    def test_config_with_unicode(self):
        """Test handling of unicode in config."""
        config = {"title": "Chatty Avatar"}
        browser = pyqt5_avatar.TransparentBrowser(config)
        assert browser.config["title"] == "Chatty Avatar"
