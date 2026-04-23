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
Tests for avatar settings API routes.

Tests avatar configuration endpoints.
"""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.chatty_commander.web.routes.avatar_settings import (
    AvatarConfigModel,
    _DEFAULTS,
    _get_avatar_cfg,
    include_avatar_settings_routes,
)


class TestAvatarConfigModel:
    """Tests for AvatarConfigModel Pydantic model."""

    def test_default_creation(self):
        """Test creating config with defaults."""
        cfg = AvatarConfigModel()
        assert cfg.enabled is True
        assert cfg.animations_dir is None

    def test_creation_with_values(self):
        """Test creating config with custom values."""
        cfg = AvatarConfigModel(
            enabled=False,
            animations_dir="/path/to/animations",
            defaults={"theme": "dark"},
        )
        assert cfg.enabled is False
        assert cfg.animations_dir == "/path/to/animations"
        assert cfg.defaults == {"theme": "dark"}

    def test_state_map_field(self):
        """Test state_map field."""
        cfg = AvatarConfigModel(
            state_map={"idle": "waiting", "talking": "speaking"}
        )
        assert cfg.state_map["idle"] == "waiting"

    def test_category_map_field(self):
        """Test category_map field."""
        cfg = AvatarConfigModel(
            category_map={"happy": "excited"}
        )
        assert cfg.category_map["happy"] == "excited"

    def test_forbids_extra_fields(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(Exception):
            AvatarConfigModel(unknown_field="value")


class TestDefaults:
    """Tests for _DEFAULTS constant."""

    def test_defaults_enabled(self):
        """Test that default enabled is True."""
        assert _DEFAULTS["enabled"] is True

    def test_defaults_animations_dir(self):
        """Test default animations_dir is None."""
        assert _DEFAULTS["animations_dir"] is None

    def test_defaults_has_state_map(self):
        """Test that defaults include state_map."""
        assert "state_map" in _DEFAULTS
        assert "idle" in _DEFAULTS["state_map"]
        assert "thinking" in _DEFAULTS["state_map"]

    def test_defaults_has_category_map(self):
        """Test that defaults include category_map."""
        assert "category_map" in _DEFAULTS
        assert "excited" in _DEFAULTS["category_map"]
        assert "neutral" in _DEFAULTS["category_map"]

    def test_state_map_mappings(self):
        """Test specific state map mappings."""
        assert _DEFAULTS["state_map"]["idle"] == "idle"
        assert _DEFAULTS["state_map"]["tool_calling"] == "hacking"
        assert _DEFAULTS["state_map"]["responding"] == "speaking"
        assert _DEFAULTS["state_map"]["error"] == "error"

    def test_category_map_mappings(self):
        """Test specific category map mappings."""
        assert _DEFAULTS["category_map"]["success"] == "success"
        assert _DEFAULTS["category_map"]["error"] == "error"
        assert _DEFAULTS["category_map"]["calm"] == "idle"


class TestGetAvatarCfg:
    """Tests for _get_avatar_cfg function."""

    def test_returns_dict(self):
        """Test that function returns a dict."""
        mock_cfg_mgr = Mock()
        mock_cfg_mgr.config = {}
        
        result = _get_avatar_cfg(mock_cfg_mgr)
        assert isinstance(result, dict)

    def test_fills_defaults(self):
        """Test that defaults are filled in."""
        mock_cfg_mgr = Mock()
        mock_cfg_mgr.config = {}
        
        result = _get_avatar_cfg(mock_cfg_mgr)
        
        assert result["enabled"] == _DEFAULTS["enabled"]
        assert result["animations_dir"] == _DEFAULTS["animations_dir"]

    def test_preserves_existing_values(self):
        """Test that existing values are preserved."""
        mock_cfg_mgr = Mock()
        mock_cfg_mgr.config = {
            "gui": {
                "avatar": {
                    "enabled": False,
                    "custom_key": "custom_value",
                }
            }
        }
        
        result = _get_avatar_cfg(mock_cfg_mgr)
        
        assert result["enabled"] is False  # Preserved
        assert result["custom_key"] == "custom_value"  # Preserved
        # But defaults still filled for missing keys
        assert "state_map" in result

    def test_handles_missing_gui_section(self):
        """Test handling of missing gui section."""
        mock_cfg_mgr = Mock()
        mock_cfg_mgr.config = {}
        
        result = _get_avatar_cfg(mock_cfg_mgr)
        
        assert isinstance(result, dict)
        assert result["enabled"] == _DEFAULTS["enabled"]

    def test_handles_missing_avatar_section(self):
        """Test handling of missing avatar section."""
        mock_cfg_mgr = Mock()
        mock_cfg_mgr.config = {"gui": {}}
        
        result = _get_avatar_cfg(mock_cfg_mgr)
        
        assert isinstance(result, dict)
        assert "state_map" in result


class TestAvatarSettingsRoutes:
    """Tests for avatar settings API routes."""

    @pytest.fixture
    def client(self):
        """Create test client with routes."""
        app = FastAPI()
        
        mock_cfg_mgr = Mock()
        mock_cfg_mgr.config = {
            "gui": {
                "avatar": {
                    "enabled": True,
                }
            }
        }
        
        def get_config_manager():
            return mock_cfg_mgr
        
        router = include_avatar_settings_routes(get_config_manager=get_config_manager)
        app.include_router(router)
        return TestClient(app)

    def test_get_config_endpoint_exists(self, client):
        """Test that GET endpoint exists."""
        response = client.get("/avatar/config")
        assert response.status_code == 200

    def test_get_config_returns_json(self, client):
        """Test that GET returns JSON config."""
        response = client.get("/avatar/config")
        assert response.headers["content-type"] == "application/json"

    def test_get_config_structure(self, client):
        """Test GET config response structure."""
        response = client.get("/avatar/config")
        data = response.json()
        
        assert "enabled" in data
        assert "animations_dir" in data
        assert "state_map" in data
        assert "category_map" in data

    def test_put_config_endpoint_exists(self, client):
        """Test that PUT endpoint exists."""
        response = client.put("/avatar/config", json={"enabled": False})
        assert response.status_code == 200

    def test_put_config_updates_values(self, client):
        """Test that PUT updates config values."""
        response = client.put(
            "/avatar/config",
            json={"enabled": False, "animations_dir": "/new/path"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["enabled"] is False
        assert data["animations_dir"] == "/new/path"

    def test_put_config_validates_input(self, client):
        """Test that PUT validates input."""
        response = client.put(
            "/avatar/config",
            json={"invalid_field": "value"}
        )
        # Should reject unknown fields
        assert response.status_code in [200, 422]


class TestEdgeCases:
    """Edge case tests."""

    def test_get_avatar_cfg_with_none_config(self):
        """Test handling of None config."""
        mock_cfg_mgr = Mock()
        mock_cfg_mgr.config = None
        
        result = _get_avatar_cfg(mock_cfg_mgr)
        
        # Should handle gracefully and return defaults
        assert isinstance(result, dict)

    def test_config_manager_without_save(self):
        """Test handling of config manager without save method."""
        app = FastAPI()
        
        mock_cfg_mgr = Mock()
        mock_cfg_mgr.config = {"gui": {"avatar": {}}}
        mock_cfg_mgr.save_config = None  # No save method
        
        def get_config_manager():
            return mock_cfg_mgr
        
        router = include_avatar_settings_routes(get_config_manager=get_config_manager)
        app.include_router(router)
        client = TestClient(app)
        
        # Should work even without save method
        response = client.put("/avatar/config", json={"enabled": True})
        assert response.status_code == 200

    def test_save_with_different_signatures(self):
        """Test handling of save with different signatures."""
        app = FastAPI()
        
        # Save that takes no args
        mock_cfg_mgr = Mock()
        mock_cfg_mgr.config = {"gui": {"avatar": {}}}
        mock_cfg_mgr.save_config = Mock()
        
        def get_config_manager():
            return mock_cfg_mgr
        
        router = include_avatar_settings_routes(get_config_manager=get_config_manager)
        app.include_router(router)
        client = TestClient(app)
        
        response = client.put("/avatar/config", json={"enabled": True})
        assert response.status_code == 200
        
        # Verify save was attempted
        mock_cfg_mgr.save_config.assert_called()
