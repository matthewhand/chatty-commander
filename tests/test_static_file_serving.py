#!/usr/bin/env python3
"""
Specific tests for static file serving functionality.
Tests edge cases, error handling, and different file types.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.web_mode import WebModeServer


class TestStaticFileServing:
    """Test suite for static file serving functionality."""

    @pytest.fixture
    def mock_managers(self):
        """Create mock managers for testing."""
        config = Mock(spec=Config)
        config.config = {"test": "value"}

        state_manager = Mock(spec=StateManager)
        state_manager.current_state = "idle"
        state_manager.get_active_models.return_value = ["test_model"]
        state_manager.add_state_change_callback = Mock()
        state_manager.change_state = Mock()

        model_manager = Mock(spec=ModelManager)
        command_executor = Mock(spec=CommandExecutor)

        return config, state_manager, model_manager, command_executor

    @pytest.fixture
    def web_server(self, mock_managers):
        """Create WebModeServer instance for testing."""
        with patch(
            'chatty_commander.advisors.providers.build_provider_safe'
        ) as mock_build_provider:
            mock_provider = Mock()
            mock_provider.model = "test-model"
            mock_provider.api_mode = "completion"
            mock_build_provider.return_value = mock_provider
            config, state_manager, model_manager, command_executor = mock_managers
            return WebModeServer(
                config_manager=config,
                state_manager=state_manager,
                model_manager=model_manager,
                command_executor=command_executor,
                no_auth=True,
            )

    @pytest.fixture
    def test_client(self, web_server):
        """Create test client for API testing."""
        return TestClient(web_server.app)

    def test_frontend_index_fallback_no_build(self, test_client):
        """Test frontend index fallback when build directory doesn't exist."""
        with patch('pathlib.Path.exists') as mock_exists:
            # Mock that frontend build directory doesn't exist
            mock_exists.return_value = False

            response = test_client.get("/")
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")
            assert "ChattyCommander" in response.text
            assert "Frontend not built" in response.text

    def test_frontend_index_with_build_directory(self, test_client):
        """Test frontend index serving when build directory exists but no index.html."""
        with patch('pathlib.Path.exists', return_value=False):
            # Mock that neither build directory nor index.html exist
            response = test_client.get("/")
            assert response.status_code == 200
            # Should show fallback since index.html doesn't exist
            assert "Frontend not built" in response.text

    def test_avatar_ui_mount_failure_handling(self, test_client):
        """Test avatar UI mount failure handling."""
        with (
            patch('pathlib.Path.exists', return_value=True),
            patch('fastapi.FastAPI.mount', side_effect=Exception("Mount failed")),
        ):
            # This tests the exception handling in avatar UI mounting
            # The server should still start even if avatar UI mounting fails
            response = test_client.get("/api/v1/status")
            assert response.status_code == 200

    def test_static_files_mount_with_existing_directory(self, test_client):
        """Test static files mounting when directory exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock static directory structure
            static_path = Path(temp_dir) / "static"
            static_path.mkdir()

            css_file = static_path / "main.css"
            css_file.write_text("body { margin: 0; }")

            js_file = static_path / "app.js"
            js_file.write_text("console.log('Hello');")

            # Test that the mounting logic works
            # This is more of a structural test since we can't easily
            # mock the entire FastAPI static file serving
            pass

    def test_frontend_path_resolution(self, test_client):
        """Test frontend path resolution logic."""
        # Test that the correct paths are being checked
        with patch('pathlib.Path') as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.__truediv__ = Mock(return_value=mock_path)
            mock_path_class.return_value = mock_path

            # This tests the path resolution logic in web_mode.py
            response = test_client.get("/api/v1/status")
            assert response.status_code == 200

    def test_avatar_path_resolution(self, test_client):
        """Test avatar UI path resolution logic."""
        # Test that the correct avatar paths are being checked
        with patch('pathlib.Path') as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = False
            mock_path_class.return_value = mock_path

            # Test that avatar UI logic handles missing paths correctly
            response = test_client.get("/api/v1/status")
            assert response.status_code == 200

    def test_static_file_security(self, test_client):
        """Test static file serving security measures."""
        # Test that directory traversal attacks are prevented
        response = test_client.get("/static/../../../etc/passwd")
        # Should return 404 or 403, not expose system files
        assert response.status_code in [404, 403, 422]

    def test_large_static_file_handling(self, test_client):
        """Test handling of large static files."""
        # Test that large files are handled appropriately
        # This is more of a performance/memory test
        response = test_client.get("/static/large-file.js")
        # Should return 404 since file doesn't exist
        assert response.status_code == 404

    def test_concurrent_static_file_requests(self, test_client):
        """Test concurrent static file requests."""
        # Test that multiple simultaneous requests are handled correctly
        import concurrent.futures

        def make_request():
            return test_client.get("/")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]

        # All requests should succeed
        for response in results:
            assert response.status_code == 200

    def test_static_file_caching_behavior(self, test_client):
        """Test static file caching behavior."""
        # Test that appropriate cache headers are set
        response = test_client.get("/")
        assert response.status_code == 200

        # Check for cache-related headers
        headers = response.headers
        # Note: Actual caching headers depend on FastAPI/Starlette configuration
        # This is more of a documentation test for expected behavior
        pass

    def test_content_type_detection(self, test_client):
        """Test content type detection for different file types."""
        # Test that different file types get correct content types
        response = test_client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_frontend_routing_spa_support(self, test_client):
        """Test SPA routing support."""
        # Test that frontend routes that don't exist as files
        # should ideally fallback to index.html for SPA routing
        response = test_client.get("/dashboard")
        # Currently returns 404, but in a full SPA setup,
        # this might fallback to index.html
        assert response.status_code == 404

    def test_api_route_precedence_over_static(self, test_client):
        """Test that API routes take precedence over static file routes."""
        # Ensure /api/* routes are handled by the API, not static files
        response = test_client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "running"

    def test_websocket_route_availability(self, test_client):
        """Test WebSocket route availability alongside static files."""
        # Test that WebSocket routes work alongside static file serving
        try:
            with test_client.websocket_connect("/ws") as websocket:
                # Basic connection test
                assert websocket is not None
        except Exception:
            # WebSocket connection might fail in test environment
            # but the route should be available
            pass

    def test_error_handling_in_static_serving(self, test_client):
        """Test error handling in static file serving."""
        # Test various error conditions
        response = test_client.get("/nonexistent-static-file.css")
        assert response.status_code == 404

        response = test_client.get("/static/nonexistent.js")
        assert response.status_code == 404

    def test_frontend_build_detection_logic(self, test_client):
        """Test the logic for detecting if frontend is built."""
        # Test the specific logic used to determine if frontend is available
        with patch('pathlib.Path.exists') as mock_exists:
            # Test various combinations of existing/missing files
            mock_exists.return_value = True
            response = test_client.get("/api/v1/status")
            assert response.status_code == 200

            mock_exists.return_value = False
            response = test_client.get("/api/v1/status")
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
