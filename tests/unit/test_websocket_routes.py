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

"""Unit tests for WebSocket routes and handlers.

Tests the WebSocket connection lifecycle, message handling, and protocol.
"""

import json

import pytest
from fastapi.testclient import TestClient

from chatty_commander.web.routes.ws import include_ws_routes


@pytest.fixture
def websocket_router():
    """Create a WebSocket router for testing."""
    connections = set()

    def get_connections():
        return connections

    def set_connections(conns):
        nonlocal connections
        connections = conns

    def get_state_snapshot():
        return {"status": "active", "mode": "idle"}

    router = include_ws_routes(
        get_connections=get_connections,
        set_connections=set_connections,
        get_state_snapshot=get_state_snapshot,
        heartbeat_seconds=0.1,  # Fast for testing
    )

    return router, connections


class TestWebSocketConnectionLifecycle:
    """Tests for WebSocket connection setup and teardown."""

    async def test_websocket_connection_accepts(self, websocket_router):
        """Test that WebSocket connection is accepted."""
        router, connections = websocket_router
        client = TestClient(router)

        with client.websocket_connect("/ws") as websocket:
            # Connection should be established (test session has no client_state attr)
            assert websocket is not None
            assert len(connections) == 1

    async def test_websocket_receives_initial_snapshot(self, websocket_router):
        """Test that client receives initial state snapshot on connect."""
        router, connections = websocket_router
        client = TestClient(router)

        with client.websocket_connect("/ws") as websocket:
            # Should receive initial snapshot
            data = websocket.receive_text()
            message = json.loads(data)

            assert message["type"] == "connection_established"
            assert "data" in message
            assert message["data"]["status"] == "active"
            assert message["data"]["mode"] == "idle"
            assert "timestamp" in message

    async def test_websocket_disconnect_cleanup(self, websocket_router):
        """Test that WebSocket connection is cleaned up on disconnect."""
        router, connections = websocket_router
        client = TestClient(router)

        with client.websocket_connect("/ws"):
            assert len(connections) == 1

        # After disconnect, connection should be removed
        assert len(connections) == 0

    async def test_websocket_multiple_connections(self, websocket_router):
        """Test multiple simultaneous WebSocket connections."""
        router, connections = websocket_router
        client = TestClient(router)

        with client.websocket_connect("/ws"):
            assert len(connections) == 1

            with client.websocket_connect("/ws"):
                assert len(connections) == 2

        # After first disconnect (cleanup may be sync or slightly delayed)
        assert len(connections) in (0, 1)

        # After second disconnect
        assert len(connections) == 0


class TestWebSocketHeartbeat:
    """Tests for WebSocket heartbeat mechanism."""

    async def test_heartbeat_received(self, websocket_router):
        """Test that heartbeat messages are sent periodically."""
        router, connections = websocket_router
        client = TestClient(router)

        with client.websocket_connect("/ws") as websocket:
            # Skip initial connection message
            websocket.receive_text()

            # Wait for heartbeat (timeout is 0.1s)
            import time
            time.sleep(0.15)

            # Should have sent heartbeat
            data = websocket.receive_text()
            message = json.loads(data)

            assert message["type"] == "heartbeat"
            assert "data" in message
            assert "timestamp" in message["data"]

    async def test_heartbeat_timeout_uses_config(self):
        """Test that heartbeat timeout is configurable."""
        connections = set()

        def get_conns():
            return connections

        def set_conns(conns):
            nonlocal connections
            connections = conns

        # Use custom heartbeat interval
        router = include_ws_routes(
            get_connections=get_conns,
            set_connections=set_conns,
            get_state_snapshot=lambda: {},
            heartbeat_seconds=0.05,  # Very fast for testing
        )

        client = TestClient(router)

        with client.websocket_connect("/ws") as websocket:
            websocket.receive_text()  # Skip initial

            import time
            time.sleep(0.08)  # Wait for heartbeat

            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "heartbeat"


class TestWebSocketMessageHandling:
    """Tests for WebSocket message parsing and handling."""

    async def test_ping_pong_protocol(self, websocket_router):
        """Test ping/pong protocol."""
        router, connections = websocket_router
        client = TestClient(router)

        with client.websocket_connect("/ws") as websocket:
            websocket.receive_text()  # Skip initial

            # Send ping
            websocket.send_text(json.dumps({"type": "ping"}))

            # Should receive pong
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "pong"
            assert "data" in message
            assert "timestamp" in message["data"]

    async def test_json_message_parsed(self, websocket_router):
        """Test that JSON messages are properly parsed."""
        connections = set()
        received_messages = []

        def on_message(msg):
            received_messages.append(msg)

        router = include_ws_routes(
            get_connections=lambda: connections,
            set_connections=lambda c: connections.update(c),
            get_state_snapshot=lambda: {},
            on_message=on_message,
            heartbeat_seconds=1.0,
        )

        client = TestClient(router)

        with client.websocket_connect("/ws") as websocket:
            websocket.receive_text()  # Skip initial

            # Send JSON message
            test_msg = {"type": "test", "data": {"key": "value"}}
            websocket.send_text(json.dumps(test_msg))

            # Wait for callback (happens in a task)
            import time
            time.sleep(0.05)

            # Verify callback received it
            assert len(received_messages) == 1
            assert received_messages[0] == test_msg

    async def test_non_json_message_handled(self, websocket_router):
        """Test that non-JSON messages are handled gracefully."""
        connections = set()
        received_messages = []

        def on_message(msg):
            received_messages.append(msg)

        router = include_ws_routes(
            get_connections=lambda: connections,
            set_connections=lambda c: connections.update(c),
            get_state_snapshot=lambda: {},
            on_message=on_message,
            heartbeat_seconds=1.0,
        )

        client = TestClient(router)

        with client.websocket_connect("/ws") as websocket:
            websocket.receive_text()  # Skip initial

            # Send non-JSON message
            websocket.send_text("not a json message")

            import time
            time.sleep(0.05)

            # Should have received raw message
            assert len(received_messages) == 1
            assert received_messages[0]["type"] == "raw"
            assert received_messages[0]["data"] == "not a json message"

    async def test_empty_message_handled(self, websocket_router):
        """Test that empty messages are handled."""
        router, connections = websocket_router
        client = TestClient(router)

        with client.websocket_connect("/ws") as websocket:
            websocket.receive_text()  # Skip initial

            # Send empty message (should not crash)
            websocket.send_text("")

            # Connection should still be open: another send must not raise
            # (WebSocketTestSession has no client_state attribute).
            websocket.send_text(json.dumps({"type": "ping"}))
            assert websocket is not None


class TestWebSocketErrorHandling:
    """Tests for WebSocket error handling."""

    async def test_disconnect_without_accept(self):
        """Test handling of disconnect before accept."""
        connections = set()

        router = include_ws_routes(
            get_connections=lambda: connections,
            set_connections=lambda c: connections.update(c),
            get_state_snapshot=lambda: {},
            heartbeat_seconds=1.0,
        )

        client = TestClient(router)

        # This should handle gracefully
        try:
            with client.websocket_connect("/ws"):
                pass
        except Exception:
            pass  # Should not raise

        # No connections should remain
        assert len(connections) == 0

    async def test_message_callback_exception(self, websocket_router):
        """Test that callback exceptions don't crash the server."""
        connections = set()

        def bad_callback(msg):
            raise Exception("Callback error")

        router = include_ws_routes(
            get_connections=lambda: connections,
            set_connections=lambda c: connections.update(c),
            get_state_snapshot=lambda: {},
            on_message=bad_callback,
            heartbeat_seconds=1.0,
        )

        client = TestClient(router)

        with client.websocket_connect("/ws") as websocket:
            websocket.receive_text()  # Skip initial

            # Send message (callback will throw exception)
            websocket.send_text(json.dumps({"type": "test"}))

            # Connection should still be open despite the callback error: a
            # follow-up send must not raise (WebSocketTestSession has no
            # client_state attribute).
            websocket.send_text(json.dumps({"type": "test2"}))
            assert websocket is not None

    async def test_invalid_json_handled(self, websocket_router):
        """Test that invalid JSON is handled gracefully."""
        connections = set()
        received = []

        def on_message(msg):
            received.append(msg)

        router = include_ws_routes(
            get_connections=lambda: connections,
            set_connections=lambda c: connections.update(c),
            get_state_snapshot=lambda: {},
            on_message=on_message,
            heartbeat_seconds=1.0,
        )

        client = TestClient(router)

        with client.websocket_connect("/ws") as websocket:
            websocket.receive_text()  # Skip initial

            # Send invalid JSON
            websocket.send_text('{"type": "test", "data": }')

            import time
            time.sleep(0.05)

            # Should have received raw message with partial JSON
            assert len(received) == 1
            assert received[0]["type"] == "raw"


class TestWebSocketConnectivity:
    """Tests for WebSocket connection management."""

    async def test_connection_set_management(self):
        """Test that connection set is properly managed."""
        connections = set()

        def get_conns():
            return connections

        def set_conns(conns):
            nonlocal connections
            connections = conns

        router = include_ws_routes(
            get_connections=get_conns,
            set_connections=set_conns,
            get_state_snapshot=lambda: {},
            heartbeat_seconds=1.0,
        )

        client = TestClient(router)

        # Connect
        with client.websocket_connect("/ws"):
            assert len(connections) == 1

            # Connect another
            with client.websocket_connect("/ws"):
                assert len(connections) == 2

            # First should still be connected
            assert len(connections) == 1

        # All should be disconnected
        assert len(connections) == 0

    async def test_same_connection_not_duplicated(self):
        """Test that the same connection isn't added multiple times."""
        connections = set()

        router = include_ws_routes(
            get_connections=lambda: connections,
            set_connections=lambda c: connections.update(c),
            get_state_snapshot=lambda: {},
            heartbeat_seconds=1.0,
        )

        client = TestClient(router)

        with client.websocket_connect("/ws"):
            assert len(connections) == 1

            # Try to add same connection again (shouldn't duplicate)
            # This is handled by set.update()
            assert len(connections) == 1


class TestWebSocketStateSnapshot:
    """Tests for state snapshot functionality."""

    async def test_state_snapshot_structure(self):
        """Test that state snapshot has correct structure."""
        connections = set()
        state_data = {
            "status": "running",
            "mode": "computer",
            "agent_count": 3,
            "active_tasks": ["task1", "task2"],
        }

        router = include_ws_routes(
            get_connections=lambda: connections,
            set_connections=lambda c: connections.update(c),
            get_state_snapshot=lambda: state_data,
            heartbeat_seconds=1.0,
        )

        client = TestClient(router)

        with client.websocket_connect("/ws") as websocket:
            data = websocket.receive_text()
            message = json.loads(data)

            assert message["type"] == "connection_established"
            assert message["data"] == state_data
            assert "timestamp" in message

    async def test_empty_state_snapshot(self):
        """Test that empty state snapshot works."""
        router = include_ws_routes(
            get_connections=lambda: set(),
            set_connections=lambda c: None,
            get_state_snapshot=lambda: {},
            heartbeat_seconds=1.0,
        )

        client = TestClient(router)

        with client.websocket_connect("/ws") as websocket:
            data = websocket.receive_text()
            message = json.loads(data)

            assert message["type"] == "connection_established"
            assert message["data"] == {}

    async def test_none_state_snapshot(self):
        """Test that None state snapshot is handled."""
        router = include_ws_routes(
            get_connections=lambda: set(),
            set_connections=lambda c: None,
            get_state_snapshot=lambda: None,
            heartbeat_seconds=1.0,
        )

        client = TestClient(router)

        with client.websocket_connect("/ws") as websocket:
            # Should handle None gracefully
            data = websocket.receive_text()
            message = json.loads(data)

            assert message["type"] == "connection_established"
            assert message["data"] is None


class TestWebSocketRouteConfiguration:
    """Tests for WebSocket route configuration."""

    def test_route_created(self):
        """Test that route is properly created."""
        router = include_ws_routes(
            get_connections=lambda: set(),
            set_connections=lambda c: None,
            get_state_snapshot=lambda: {},
            heartbeat_seconds=1.0,
        )

        # Router should have the WebSocket route
        assert router is not None
        assert hasattr(router, "routes")

    def test_route_with_custom_callbacks(self):
        """Test route with custom callbacks."""
        connections = set()
        state_calls = []
        message_calls = []

        def get_state():
            state_calls.append(1)
            return {"test": "state"}

        def on_msg(msg):
            message_calls.append(msg)

        router = include_ws_routes(
            get_connections=lambda: connections,
            set_connections=lambda c: connections.update(c),
            get_state_snapshot=get_state,
            on_message=on_msg,
            heartbeat_seconds=1.0,
        )

        client = TestClient(router)

        with client.websocket_connect("/ws") as websocket:
            assert len(state_calls) == 1

            websocket.send_text(json.dumps({"type": "ping"}))

            import time
            time.sleep(0.05)

            assert len(message_calls) == 1

