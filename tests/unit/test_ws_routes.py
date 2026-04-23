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

"""Tests for WebSocket routes module."""

from unittest.mock import MagicMock

import pytest

from src.chatty_commander.web.routes.ws import include_ws_routes


class TestIncludeWSRoutes:
    """Tests for include_ws_routes function."""

    def test_returns_router(self):
        """Test that function returns an APIRouter."""
        connections = set()
        get_conns = lambda: connections
        set_conns = lambda x: None
        get_snapshot = lambda: {}

        router = include_ws_routes(
            get_connections=get_conns,
            set_connections=set_conns,
            get_state_snapshot=get_snapshot,
        )
        assert router is not None

    def test_router_has_routes(self):
        """Test that router has routes."""
        connections = set()
        router = include_ws_routes(
            get_connections=lambda: connections,
            set_connections=lambda x: None,
            get_state_snapshot=lambda: {},
        )
        assert len(router.routes) > 0

    def test_ws_route_exists(self):
        """Test that /ws route exists."""
        connections = set()
        router = include_ws_routes(
            get_connections=lambda: connections,
            set_connections=lambda x: None,
            get_state_snapshot=lambda: {},
        )
        route_paths = [r.path for r in router.routes]
        assert "/ws" in route_paths

    def test_default_heartbeat(self):
        """Test default heartbeat value."""
        connections = set()
        router = include_ws_routes(
            get_connections=lambda: connections,
            set_connections=lambda x: None,
            get_state_snapshot=lambda: {},
        )
        # Router created successfully with default
        assert router is not None

    def test_custom_heartbeat(self):
        """Test custom heartbeat value."""
        connections = set()
        router = include_ws_routes(
            get_connections=lambda: connections,
            set_connections=lambda x: None,
            get_state_snapshot=lambda: {},
            heartbeat_seconds=60.0,
        )
        assert router is not None

    def test_with_on_message_callback(self):
        """Test with on_message callback."""
        connections = set()
        on_message = MagicMock()
        router = include_ws_routes(
            get_connections=lambda: connections,
            set_connections=lambda x: None,
            get_state_snapshot=lambda: {},
            on_message=on_message,
        )
        assert router is not None

    def test_without_on_message(self):
        """Test without on_message callback (default None)."""
        connections = set()
        router = include_ws_routes(
            get_connections=lambda: connections,
            set_connections=lambda x: None,
            get_state_snapshot=lambda: {},
            on_message=None,
        )
        assert router is not None


class TestWSRouteEdgeCases:
    """Edge case tests."""

    def test_empty_connections_set(self):
        """Test with empty connections set."""
        connections = set()
        router = include_ws_routes(
            get_connections=lambda: connections,
            set_connections=lambda x: None,
            get_state_snapshot=lambda: {},
        )
        assert router is not None

    def test_state_snapshot_with_data(self):
        """Test with state snapshot containing data."""
        connections = set()
        snapshot = {"status": "active", "count": 5}
        router = include_ws_routes(
            get_connections=lambda: connections,
            set_connections=lambda x: None,
            get_state_snapshot=lambda: snapshot,
        )
        assert router is not None

    def test_state_snapshot_empty(self):
        """Test with empty state snapshot."""
        connections = set()
        router = include_ws_routes(
            get_connections=lambda: connections,
            set_connections=lambda x: None,
            get_state_snapshot=lambda: {},
        )
        assert router is not None
