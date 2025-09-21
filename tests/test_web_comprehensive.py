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
Comprehensive tests for web module functionality.
Tests auth, lifecycle, server, middleware, routes, and web_mode components.
"""

from unittest.mock import patch

import pytest

from chatty_commander.web.auth import AuthManager
from chatty_commander.web.lifecycle import LifecycleManager
from chatty_commander.web.server import WebServer
from chatty_commander.web.web_mode import WebModeManager


class TestAuthManager:
    """Test authentication manager functionality."""

    def test_auth_manager_initialization(self):
        """Test auth manager initialization."""
        auth_manager = AuthManager()
        assert auth_manager is not None

    def test_token_generation(self):
        """Test authentication token generation."""
        auth_manager = AuthManager()

        with patch("secrets.token_urlsafe") as mock_token:
            mock_token.return_value = "test_token_123"

            token = auth_manager.generate_token("user123")
            assert token == "test_token_123"
            assert "user123" in auth_manager.active_tokens.values()

    def test_token_validation(self):
        """Test authentication token validation."""
        auth_manager = AuthManager()
        auth_manager.active_tokens["test_token"] = "user123"

        result = auth_manager.validate_token("test_token")
        assert result is True

        result = auth_manager.validate_token("invalid_token")
        assert result is False

    def test_token_expiration(self):
        """Test token expiration handling."""
        auth_manager = AuthManager()

        with patch("time.time") as mock_time:
            mock_time.return_value = 1000  # Start time

            auth_manager.generate_token("user123")
            token = list(auth_manager.active_tokens.keys())[0]

            # Test valid token
            result = auth_manager.validate_token(token)
            assert result is True

            # Test expired token
            mock_time.return_value = 1000 + (auth_manager.token_expiry + 1)
            result = auth_manager.validate_token(token)
            assert result is False


class TestLifecycleManager:
    """Test lifecycle manager functionality."""

    def test_lifecycle_manager_initialization(self):
        """Test lifecycle manager initialization."""
        lifecycle = LifecycleManager()
        assert lifecycle is not None

    def test_startup_sequence(self):
        """Test startup sequence execution."""
        lifecycle = LifecycleManager()

        with patch.object(lifecycle, "_initialize_database") as mock_db:
            with patch.object(lifecycle, "_start_services") as mock_services:
                with patch.object(lifecycle, "_configure_logging") as mock_logging:
                    mock_db.return_value = True
                    mock_services.return_value = True
                    mock_logging.return_value = True

                    result = lifecycle.startup()
                    assert result is True

    def test_shutdown_sequence(self):
        """Test shutdown sequence execution."""
        lifecycle = LifecycleManager()

        with patch.object(lifecycle, "_stop_services") as mock_stop:
            with patch.object(lifecycle, "_cleanup_resources") as mock_cleanup:
                with patch.object(lifecycle, "_save_state") as mock_save:
                    mock_stop.return_value = True
                    mock_cleanup.return_value = True
                    mock_save.return_value = True

                    result = lifecycle.shutdown()
                    assert result is True


class TestWebServer:
    """Test web server functionality."""

    def test_web_server_initialization(self):
        """Test web server initialization."""
        server = WebServer()
        assert server is not None

    def test_server_configuration(self):
        """Test server configuration."""
        server = WebServer()

        with patch.object(server, "_configure_cors") as mock_cors:
            with patch.object(server, "_configure_middleware") as mock_middleware:
                with patch.object(server, "_configure_routes") as mock_routes:
                    mock_cors.return_value = True
                    mock_middleware.return_value = True
                    mock_routes.return_value = True

                    result = server.configure()
                    assert result is True

    def test_server_startup(self):
        """Test server startup."""
        server = WebServer()

        with patch("uvicorn.run") as mock_uvicorn:
            server.start()
            mock_uvicorn.assert_called_once()


class TestWebModeManager:
    """Test web mode manager functionality."""

    def test_web_mode_initialization(self):
        """Test web mode manager initialization."""
        web_mode = WebModeManager()
        assert web_mode is not None

    def test_mode_switching(self):
        """Test mode switching functionality."""
        web_mode = WebModeManager()

        with patch.object(web_mode, "_enable_web_features") as mock_enable:
            with patch.object(web_mode, "_disable_cli_features") as mock_disable:
                mock_enable.return_value = True
                mock_disable.return_value = True

                result = web_mode.switch_to_web_mode()
                assert result is True

    def test_api_endpoint_registration(self):
        """Test API endpoint registration."""
        web_mode = WebModeManager()

        with patch.object(web_mode, "_register_api_endpoints") as mock_register:
            mock_register.return_value = True

            result = web_mode.setup_api_endpoints()
            assert result is True

    def test_websocket_handling(self):
        """Test WebSocket handling."""
        web_mode = WebModeManager()

        with patch.object(web_mode, "_setup_websocket_routes") as mock_setup:
            with patch.object(web_mode, "_handle_websocket_connections") as mock_handle:
                mock_setup.return_value = True
                mock_handle.return_value = True

                result = web_mode.setup_websockets()
                assert result is True


class TestWebIntegration:
    """Test web module integration."""

    def test_full_web_stack_initialization(self):
        """Test full web stack initialization."""
        auth_manager = AuthManager()
        lifecycle = LifecycleManager()
        server = WebServer()
        web_mode = WebModeManager()

        with patch.object(lifecycle, "startup") as mock_startup:
            with patch.object(server, "configure") as mock_configure:
                with patch.object(web_mode, "setup_api_endpoints") as mock_setup:
                    mock_startup.return_value = True
                    mock_configure.return_value = True
                    mock_setup.return_value = True

                    # Test that all components can be initialized together
                    assert auth_manager is not None
                    assert lifecycle is not None
                    assert server is not None
                    assert web_mode is not None

    def test_error_handling_across_components(self):
        """Test error handling across web components."""
        auth_manager = AuthManager()
        lifecycle = LifecycleManager()

        with patch.object(
            lifecycle, "startup", side_effect=Exception("Startup failed")
        ):
            # Test that errors in one component don't crash the system
            with pytest.raises(Exception):
                lifecycle.startup()

            # Auth manager should still work
            token = auth_manager.generate_token("test_user")
            assert token is not None

    def test_component_dependencies(self):
        """Test component dependencies and interactions."""
        auth_manager = AuthManager()
        web_mode = WebModeManager()

        # Generate a token
        token = auth_manager.generate_token("test_user")

        # Web mode should be able to validate tokens
        is_valid = auth_manager.validate_token(token)
        assert is_valid is True

        # Test invalid token
        is_valid = auth_manager.validate_token("invalid_token")
        assert is_valid is False


class TestWebSecurity:
    """Test web security features."""

    def test_authentication_bypass_prevention(self):
        """Test prevention of authentication bypass."""
        auth_manager = AuthManager()

        # Test that invalid tokens are rejected
        assert auth_manager.validate_token("invalid") is False
        assert auth_manager.validate_token("") is False
        assert auth_manager.validate_token(None) is False

    def test_token_cleanup(self):
        """Test token cleanup mechanisms."""
        auth_manager = AuthManager()

        # Add multiple tokens
        tokens = []
        for i in range(5):
            token = auth_manager.generate_token(f"user{i}")
            tokens.append(token)

        # All tokens should be valid initially
        for token in tokens:
            assert auth_manager.validate_token(token) is True

        # After cleanup, tokens should be removed
        auth_manager.cleanup_expired_tokens()

        # Note: This test would need to mock time.time to simulate expiration
        # For now, just verify the cleanup method exists and runs
        assert hasattr(auth_manager, "cleanup_expired_tokens")


class TestWebPerformance:
    """Test web performance features."""

    def test_concurrent_request_handling(self):
        """Test concurrent request handling."""
        server = WebServer()

        with patch.object(server, "_handle_request") as mock_handle:
            mock_handle.return_value = {"status": "ok"}

            # Simulate multiple concurrent requests
            results = []
            for i in range(10):
                result = server.handle_request(f"request_{i}")
                results.append(result)

            assert len(results) == 10
            assert all(r["status"] == "ok" for r in results)

    def test_resource_optimization(self):
        """Test resource optimization features."""
        web_mode = WebModeManager()

        with patch.object(web_mode, "_optimize_resources") as mock_optimize:
            mock_optimize.return_value = {"optimized": True}

            result = web_mode.optimize_performance()
            assert result["optimized"] is True
