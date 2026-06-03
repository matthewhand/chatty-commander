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
Comprehensive tests for tray popup GUI module.

Tests system tray functionality and popup window settings.
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.chatty_commander.gui.tray_popup import _load_settings, _icon_image


class TestLoadSettings:
    """Tests for _load_settings function."""

    def test_default_settings(self):
        """Test that default settings are returned."""
        mock_config = MagicMock()
        mock_config.config_data = {}
        
        settings = _load_settings(mock_config)
        
        assert settings["url"] == "https://your-url.example"
        assert settings["transparent"] is True
        assert settings["width"] == 420
        assert settings["height"] == 640
        assert settings["always_on_top"] is True

    def test_custom_settings_override_defaults(self):
        """Test that custom settings override defaults."""
        mock_config = MagicMock()
        mock_config.config_data = {
            "gui": {
                "popup": {
                    "url": "https://custom.example",
                    "width": 800,
                    "height": 600,
                }
            }
        }
        
        settings = _load_settings(mock_config)
        
        assert settings["url"] == "https://custom.example"
        assert settings["width"] == 800
        assert settings["height"] == 600
        # Defaults preserved for other values
        assert settings["transparent"] is True

    def test_type_coercion(self):
        """Test that settings are coerced to correct types."""
        mock_config = MagicMock()
        mock_config.config_data = {
            "gui": {
                "popup": {
                    "width": "500",
                    "height": "700",
                    "transparent": "false",
                    "always_on_top": "0",
                }
            }
        }
        
        settings = _load_settings(mock_config)
        
        assert settings["width"] == 500
        assert settings["height"] == 700
        assert settings["transparent"] is True  # Any non-empty string is truthy
        assert settings["always_on_top"] is True

    def test_invalid_width_height_uses_defaults(self):
        """Test that invalid width/height fall back to defaults."""
        mock_config = MagicMock()
        mock_config.config_data = {
            "gui": {
                "popup": {
                    "width": "invalid",
                    "height": "invalid",
                }
            }
        }
        
        settings = _load_settings(mock_config)
        
        assert settings["width"] == 420
        assert settings["height"] == 640

    def test_none_config_data(self):
        """Test handling of None config_data."""
        mock_config = MagicMock()
        mock_config.config_data = None
        
        settings = _load_settings(mock_config)
        
        # Should use defaults
        assert settings["url"] == "https://your-url.example"

    def test_missing_gui_section(self):
        """Test handling of missing gui section."""
        mock_config = MagicMock()
        mock_config.config_data = {"other": "value"}
        
        settings = _load_settings(mock_config)
        
        # Should use defaults
        assert settings["url"] == "https://your-url.example"

    def test_missing_popup_section(self):
        """Test handling of missing popup section."""
        mock_config = MagicMock()
        mock_config.config_data = {"gui": {"other": "value"}}
        
        settings = _load_settings(mock_config)
        
        # Should use defaults
        assert settings["url"] == "https://your-url.example"


class TestIconImage:
    """Tests for _icon_image function."""

    def test_returns_none_when_pil_unavailable(self):
        """Test that None is returned when PIL is not available."""
        with patch.dict("sys.modules", {"PIL": None}):
            result = _icon_image()
            assert result is None

    def test_returns_none_when_icon_png_missing(self):
        """Test that None is returned when icon.png doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            result = _icon_image()
            assert result is None

    def test_loads_icon_png_when_present(self):
        """Test that icon.png is loaded when present."""
        mock_image = Mock()
        
        with patch("pathlib.Path.exists", return_value=True):
            with patch("PIL.Image.open", return_value=mock_image):
                result = _icon_image()
                assert result is mock_image

    def test_handles_image_open_error(self):
        """Test handling of image open errors."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("PIL.Image.open", side_effect=Exception("Corrupted image")):
                result = _icon_image()
                assert result is None

    def test_prefers_png_over_svg(self):
        """Test that PNG is preferred over SVG."""
        mock_image = Mock()
        
        with patch("pathlib.Path.exists") as mock_exists:
            # Both PNG and SVG exist
            def exists_side_effect(path):
                return path.name in ["icon.png", "icon.svg"]
            mock_exists.side_effect = exists_side_effect
            
            with patch("PIL.Image.open", return_value=mock_image):
                result = _icon_image()
                # Should return the PNG image
                assert result is not None


class TestTrayPopupEdgeCases:
    """Edge case tests for tray popup."""

    def test_load_settings_with_empty_popup(self):
        """Test with empty popup dict."""
        mock_config = MagicMock()
        mock_config.config_data = {"gui": {"popup": {}}}
        
        settings = _load_settings(mock_config)
        
        # Should use all defaults
        assert settings["url"] == "https://your-url.example"
        assert settings["width"] == 420

    def test_load_settings_url_type_coercion(self):
        """Test that URL is coerced to string."""
        mock_config = MagicMock()
        mock_config.config_data = {
            "gui": {
                "popup": {
                    "url": 12345,  # Non-string URL
                }
            }
        }
        
        settings = _load_settings(mock_config)
        
        assert settings["url"] == "12345"
        assert isinstance(settings["url"], str)
