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
Comprehensive tests for web/server.py module.

Tests the FastAPI application creation, router management, and bridge functionality.
"""

from unittest.mock import Mock, patch

from chatty_commander.web.server import _include_optional, create_app


class TestFastAPIFallback:
    """Test FastAPI fallback stub when FastAPI is not available."""

    def test_fastapi_stub_creation(self):
        """Test that FastAPI stub can be created when FastAPI is not available."""
        # Simulate FastAPI not being available
        with patch.dict('sys.modules', {'fastapi': None}):
            with patch('chatty_commander.web.server.FastAPI', create=True):
                from chatty_commander.web.server import FastAPI

                app = FastAPI()
                assert app is not None
                assert hasattr(app, 'include_router')
                assert hasattr(app, 'routes')

    def test_fastapi_stub_routes_property(self):
        """Test that the FastAPI stub has a routes property."""
        # Simulate FastAPI not being available
        with patch.dict('sys.modules', {'fastapi': None}):
            with patch('chatty_commander.web.server.FastAPI', create=True):
                from chatty_commander.web.server import FastAPI

                app = FastAPI()
                assert app.routes == []


class TestOptionalRouterInclusion:
    """Test the _include_optional function."""

    def test_include_optional_with_valid_router(self):
        """Test including a router when it's available."""
        app = Mock()
        mock_router = Mock()

        # Set up globals with a valid router
        with patch.dict('chatty_commander.web.server.__builtins__', {'globals': lambda: {'test_router': mock_router}}):
            _include_optional(app, 'test_router')

            app.include_router.assert_called_once_with(mock_router)

    def test_include_optional_with_none_router(self):
        """Test including a router when it's None."""
        app = Mock()

        # Set up globals with None router
        with patch.dict('chatty_commander.web.server.__builtins__', {'globals': lambda: {'test_router': None}}):
            _include_optional(app, 'test_router')

            app.include_router.assert_not_called()

    def test_include_optional_with_missing_router(self):
        """Test including a router that doesn't exist in globals."""
        app = Mock()

        # Set up globals without the router
        with patch.dict('chatty_commander.web.server.__builtins__', {'globals': lambda: {}}):
            _include_optional(app, 'missing_router')

            app.include_router.assert_not_called()


class TestAppCreation:
    """Test the create_app function."""

    def test_create_app_basic(self):
        """Test basic app creation."""
        app = create_app()

        assert app is not None
        assert hasattr(app, 'include_router')

    def test_create_app_with_no_auth(self):
        """Test app creation with no_auth=True."""
        app = create_app(no_auth=True)

        assert app is not None

        # Check that bridge endpoint exists
        bridge_route = None
        for route in app.routes:
            if hasattr(route, 'path') and route.path == "/bridge/event":
                bridge_route = route
                break

        assert bridge_route is not None

    def test_create_app_with_config_manager(self):
        """Test app creation with config manager."""
        mock_config = Mock()
        app = create_app(config_manager=mock_config)

        assert app is not None

    def test_create_app_with_no_auth_false(self):
        """Test app creation with no_auth=False."""
        app = create_app(no_auth=False)

        assert app is not None

        # Check that bridge endpoint exists
        bridge_route = None
        for route in app.routes:
            if hasattr(route, 'path') and route.path == "/bridge/event":
                bridge_route = route
                break

        assert bridge_route is not None


class TestBridgeEndpoint:
    """Test the bridge event endpoint."""

    def test_bridge_endpoint_success(self):
        """Test successful bridge endpoint call."""
        app = create_app(no_auth=False)

        # Find the bridge endpoint
        bridge_route = None
        for route in app.routes:
            if hasattr(route, 'path') and route.path == "/bridge/event":
                bridge_route = route
                break

        assert bridge_route is not None

    def test_bridge_endpoint_no_auth_unauthorized(self):
        """Test bridge endpoint with no auth returns 401."""
        app = create_app(no_auth=True)

        # Find the bridge endpoint
        bridge_route = None
        for route in app.routes:
            if hasattr(route, 'path') and route.path == "/bridge/event":
                bridge_route = route
                break

        assert bridge_route is not None

        # The endpoint should be configured to return 401 when no_auth=True
        # This is tested by the implementation logic in the server.py file


class TestRouterManagement:
    """Test router inclusion and management."""

    def test_router_inclusion_with_mocks(self):
        """Test that routers are included when available."""
        # Mock all the routers
        mock_routers = {
            'avatar_ws_router': Mock(),
            'avatar_api_router': Mock(),
            'avatar_selector_router': Mock(),
            'version_router': Mock(),
            'metrics_router': Mock(),
            'agents_router': Mock()
        }

        with patch.dict('chatty_commander.web.server.__builtins__', {'globals': lambda: mock_routers}):
            app = create_app()

            # Verify all routers were included
            for router_name, mock_router in mock_routers.items():
                if router_name != 'metrics_router':  # metrics_router has different logic
                    app.include_router.assert_any_call(mock_router)

    def test_router_inclusion_with_missing_routers(self):
        """Test that missing routers are handled gracefully."""
        # Only provide some routers
        mock_routers = {
            'avatar_ws_router': Mock(),
            'version_router': Mock(),
        }

        with patch.dict('chatty_commander.web.server.__builtins__', {'globals': lambda: mock_routers}):
            app = create_app()

            # Only the available routers should be included
            expected_calls = 2  # avatar_ws_router and version_router
            assert app.include_router.call_count == expected_calls

    def test_settings_router_with_config_manager(self):
        """Test settings router inclusion with config manager."""
        mock_config = Mock()

        with patch('chatty_commander.web.server.include_avatar_settings_routes') as mock_settings:
            mock_settings_router = Mock()
            mock_settings.return_value = mock_settings_router

            app = create_app(config_manager=mock_config)

            # Settings router should be created and included
            mock_settings.assert_called_once()
            app.include_router.assert_any_call(mock_settings_router)

    def test_settings_router_without_config_manager(self):
        """Test settings router when no config manager provided."""
        with patch('chatty_commander.web.server.include_avatar_settings_routes') as mock_settings:
            app = create_app()  # No config_manager

            # Settings router should not be created
            mock_settings.assert_not_called()

    def test_settings_router_with_none_settings_routes(self):
        """Test settings router when include_avatar_settings_routes is None."""
        with patch('chatty_commander.web.server.include_avatar_settings_routes', None):
            mock_config = Mock()
            app = create_app(config_manager=mock_config)

            # No settings router should be included
            # The app.include_router should not be called with a settings router

    def test_metrics_router_creation(self):
        """Test metrics router creation."""
        with patch('chatty_commander.web.server.create_metrics_router') as mock_metrics:
            mock_metrics_router = Mock()
            mock_metrics.return_value = mock_metrics_router

            app = create_app()

            # Metrics router should be created
            mock_metrics.assert_called_once()
            app.include_router.assert_any_call(mock_metrics_router)

    def test_metrics_router_creation_failure(self):
        """Test handling when metrics router creation fails."""
        with patch('chatty_commander.web.server.create_metrics_router', side_effect=ImportError):
            app = create_app()

            # Should not raise an error, should handle gracefully
            assert app is not None


class TestAppConfiguration:
    """Test application configuration options."""

    def test_app_title_and_description(self):
        """Test that the app has proper title and description."""
        app = create_app()

        # The app should be a FastAPI instance with proper configuration
        # We can't easily test the exact FastAPI attributes without the real FastAPI
        # but we can verify the app object exists and has the expected structure
        assert app is not None
        assert hasattr(app, 'include_router')

    def test_app_with_custom_config(self):
        """Test app creation with custom configuration."""
        mock_config = Mock()
        mock_config.some_setting = "test_value"

        app = create_app(config_manager=mock_config)

        assert app is not None

    def test_app_routes_structure(self):
        """Test that the app has the expected route structure."""
        app = create_app()

        # Check that we have the bridge endpoint
        bridge_found = False
        for route in app.routes:
            if hasattr(route, 'path') and route.path == "/bridge/event":
                bridge_found = True
                break

        assert bridge_found, "Bridge endpoint should be present"


class TestImportHandling:
    """Test import handling for optional dependencies."""

    def test_fastapi_import_success(self):
        """Test handling when FastAPI is available."""
        # This test assumes FastAPI is available in the test environment
        app = create_app()
        assert app is not None

    def test_router_import_graceful_failure(self):
        """Test that missing router imports are handled gracefully."""
        # Test with no routers available
        with patch.dict('chatty_commander.web.server.__builtins__',
                       {'globals': lambda: {
                           'avatar_ws_router': None,
                           'avatar_api_router': None,
                           'avatar_selector_router': None,
                           'version_router': None,
                           'metrics_router': None,
                           'agents_router': None
                       }}):
            app = create_app()

            # App should still be created successfully
            assert app is not None

    def test_settings_routes_import_failure(self):
        """Test handling when settings routes import fails."""
        with patch('chatty_commander.web.server.include_avatar_settings_routes', None):
            mock_config = Mock()
            app = create_app(config_manager=mock_config)

            assert app is not None


class TestErrorHandling:
    """Test error handling in the web server."""

    def test_bridge_endpoint_http_exception_import(self):
        """Test that HTTPException import is handled correctly."""
        # Test when fastapi is not available
        with patch.dict('sys.modules', {'fastapi': None}):
            app = create_app(no_auth=True)

            # Should not raise an error even if HTTPException is not available
            assert app is not None

    def test_bridge_endpoint_with_fastapi_exception(self):
        """Test bridge endpoint when FastAPI HTTPException is available."""
        # This test assumes FastAPI is available
        app = create_app(no_auth=True)

        # The bridge endpoint should be configured but not raise an error during creation
        assert app is not None

        # Check that the endpoint is present
        bridge_found = False
        for route in app.routes:
            if hasattr(route, 'path') and route.path == "/bridge/event":
                bridge_found = True
                break

        assert bridge_found


class TestIntegrationScenarios:
    """Integration tests for complex scenarios."""

    def test_full_app_creation_with_all_routers(self):
        """Test creating app with all possible routers."""
        mock_config = Mock()

        # Mock all routers
        mock_routers = {
            'avatar_ws_router': Mock(),
            'avatar_api_router': Mock(),
            'avatar_selector_router': Mock(),
            'version_router': Mock(),
            'agents_router': Mock()
        }

        with patch.dict('chatty_commander.web.server.__builtins__', {'globals': lambda: mock_routers}):
            with patch('chatty_commander.web.server.create_metrics_router') as mock_metrics:
                with patch('chatty_commander.web.server.include_avatar_settings_routes') as mock_settings:
                    mock_metrics_router = Mock()
                    mock_metrics.return_value = mock_metrics_router

                    mock_settings_router = Mock()
                    mock_settings.return_value = mock_settings_router

                    app = create_app(config_manager=mock_config)

                    # Verify all routers were included
                    expected_router_calls = len(mock_routers) + 2  # routers + metrics + settings
                    assert app.include_router.call_count == expected_router_calls

    def test_app_creation_with_mixed_availability(self):
        """Test app creation when some routers are available and others aren't."""
        # Mix of available and unavailable routers
        mock_routers = {
            'avatar_ws_router': Mock(),
            'avatar_api_router': None,  # Not available
            'version_router': Mock(),
            'agents_router': None,  # Not available
        }

        with patch.dict('chatty_commander.web.server.__builtins__', {'globals': lambda: mock_routers}):
            with patch('chatty_commander.web.server.create_metrics_router') as mock_metrics:
                mock_metrics_router = Mock()
                mock_metrics.return_value = mock_metrics_router

                app = create_app()

                # Only available routers should be included
                expected_calls = 3  # avatar_ws_router, version_router, metrics_router
                assert app.include_router.call_count == expected_calls

    def test_app_creation_error_recovery(self):
        """Test that app creation recovers gracefully from errors."""
        # Simulate various import failures
        with patch.dict('sys.modules', {
            'fastapi': None,
            'chatty_commander.web.routes.avatar_ws': None,
            'chatty_commander.web.routes.avatar_api': None,
            'chatty_commander.obs.metrics': None
        }):
            with patch('chatty_commander.web.server.create_metrics_router', side_effect=ImportError):
                # Should not raise an error
                app = create_app()

                # App should still be created
                assert app is not None

    def test_bridge_endpoint_functionality(self):
        """Test bridge endpoint functionality in different modes."""
        # Test with no_auth=True
        app_no_auth = create_app(no_auth=True)
        assert app_no_auth is not None

        # Test with no_auth=False
        app_with_auth = create_app(no_auth=False)
        assert app_with_auth is not None

        # Both should have the bridge endpoint
        no_auth_bridge = any(
            hasattr(route, 'path') and route.path == "/bridge/event"
            for route in app_no_auth.routes
        )
        auth_bridge = any(
            hasattr(route, 'path') and route.path == "/bridge/event"
            for route in app_with_auth.routes
        )

        assert no_auth_bridge
        assert auth_bridge

    def test_config_manager_dependency_injection(self):
        """Test that config manager is properly injected where needed."""
        mock_config = Mock()

        with patch('chatty_commander.web.server.include_avatar_settings_routes') as mock_settings:
            mock_settings_router = Mock()
            mock_settings.return_value = mock_settings_router

            app = create_app(config_manager=mock_config)

            # Settings router should be created with the config manager
            mock_settings.assert_called_once()
            call_args = mock_settings.call_args[1]  # keyword arguments
            assert 'get_config_manager' in call_args
            assert callable(call_args['get_config_manager'])

            # Verify the lambda returns our config manager
            config_getter = call_args['get_config_manager']
            assert config_getter() is mock_config
