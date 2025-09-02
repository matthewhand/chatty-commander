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

"""Comprehensive tests for avatar WebSocket functionality."""

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

try:
    from fastapi import WebSocket, WebSocketDisconnect
    from fastapi.testclient import TestClient
except ImportError:
    pytest.skip("FastAPI not available", allow_module_level=True)

from src.chatty_commander.web.routes.avatar_ws import (
    AvatarAudioQueue,
    AvatarWSConnectionManager,
    audio_queue,
    avatar_ws_endpoint,
    interrupt_avatar_queue,
    manager,
    queue_avatar_message,
)


class TestAvatarWSConnectionManager:
    """Test AvatarWSConnectionManager functionality."""

    @patch("src.chatty_commander.web.routes.avatar_ws.get_thinking_manager")
    def test_init_without_theme_resolver(self, mock_get_thinking_manager):
        """Test manager initialization without theme resolver."""
        mock_get_thinking_manager.return_value = None
        mgr = AvatarWSConnectionManager()
        assert mgr.active_connections == []
        assert mgr.theme_resolver is None
        assert mgr._registered_manager is None

    def test_init_with_theme_resolver(self):
        """Test manager initialization with theme resolver."""
        theme_resolver = Mock(return_value="dark")
        mgr = AvatarWSConnectionManager(theme_resolver=theme_resolver)
        assert mgr.theme_resolver == theme_resolver

    @patch("src.chatty_commander.web.routes.avatar_ws.get_thinking_manager")
    def test_ensure_manager_first_time(self, mock_get_thinking_manager):
        """Test _ensure_manager when called for the first time."""
        mock_thinking_manager = Mock()
        mock_get_thinking_manager.return_value = mock_thinking_manager

        mgr = AvatarWSConnectionManager()
        result = mgr._ensure_manager()

        assert result == mock_thinking_manager
        mock_thinking_manager.add_broadcast_callback.assert_called_once_with(
            mgr.broadcast_state_change
        )
        assert mgr._registered_manager == mock_thinking_manager

    @patch("src.chatty_commander.web.routes.avatar_ws.get_thinking_manager")
    def test_ensure_manager_with_existing_registration(self, mock_get_thinking_manager):
        """Test _ensure_manager when manager changes."""
        old_manager = Mock()
        new_manager = Mock()
        mock_get_thinking_manager.return_value = new_manager

        # Create manager without calling constructor's _ensure_manager
        mgr = AvatarWSConnectionManager.__new__(AvatarWSConnectionManager)
        mgr.active_connections = []
        mgr.theme_resolver = None
        mgr._registered_manager = old_manager

        result = mgr._ensure_manager()

        # Should remove from old manager and add to new
        old_manager.remove_broadcast_callback.assert_called_once_with(
            mgr.broadcast_state_change
        )
        new_manager.add_broadcast_callback.assert_called_once_with(
            mgr.broadcast_state_change
        )
        assert mgr._registered_manager == new_manager

    @patch("src.chatty_commander.web.routes.avatar_ws.get_thinking_manager")
    def test_ensure_manager_with_exception(self, mock_get_thinking_manager):
        """Test _ensure_manager handles exceptions gracefully."""
        mock_thinking_manager = Mock()
        mock_thinking_manager.add_broadcast_callback.side_effect = Exception(
            "Test error"
        )
        mock_get_thinking_manager.return_value = mock_thinking_manager

        mgr = AvatarWSConnectionManager()
        result = mgr._ensure_manager()

        # Should still return the manager despite the exception
        assert result == mock_thinking_manager

    @pytest.mark.asyncio
    async def test_connect_websocket(self):
        """Test WebSocket connection."""
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_thinking_manager = Mock()
        mock_thinking_manager.get_all_states.return_value = {
            "agent1": Mock(
                to_dict=Mock(return_value={"state": "thinking", "persona_id": "chatty"})
            )
        }

        with patch(
            "src.chatty_commander.web.routes.avatar_ws.get_thinking_manager",
            return_value=mock_thinking_manager,
        ):
            mgr = AvatarWSConnectionManager()
            await mgr.connect(mock_websocket)

            mock_websocket.accept.assert_called_once()
            assert mock_websocket in mgr.active_connections
            mock_websocket.send_text.assert_called_once()

            # Verify snapshot message structure
            call_args = mock_websocket.send_text.call_args[0][0]
            snapshot = json.loads(call_args)
            assert snapshot["type"] == "agent_states_snapshot"
            assert "data" in snapshot

    @pytest.mark.asyncio
    async def test_connect_with_theme_resolver(self):
        """Test WebSocket connection with theme resolver."""
        mock_websocket = AsyncMock(spec=WebSocket)
        theme_resolver = Mock(return_value="dark")
        mock_thinking_manager = Mock()
        mock_thinking_manager.get_all_states.return_value = {
            "agent1": Mock(
                to_dict=Mock(return_value={"state": "thinking", "persona_id": "chatty"})
            )
        }

        with patch(
            "src.chatty_commander.web.routes.avatar_ws.get_thinking_manager",
            return_value=mock_thinking_manager,
        ):
            mgr = AvatarWSConnectionManager(theme_resolver=theme_resolver)
            await mgr.connect(mock_websocket)

            # Verify theme was added
            call_args = mock_websocket.send_text.call_args[0][0]
            snapshot = json.loads(call_args)
            assert snapshot["data"]["agent1"]["theme"] == "dark"
            theme_resolver.assert_called_once_with("chatty")

    @pytest.mark.asyncio
    async def test_connect_with_send_error(self):
        """Test WebSocket connection when send fails."""
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.send_text.side_effect = Exception("Send failed")
        mock_thinking_manager = Mock()
        mock_thinking_manager.get_all_states.return_value = {}

        with patch(
            "src.chatty_commander.web.routes.avatar_ws.get_thinking_manager",
            return_value=mock_thinking_manager,
        ):
            mgr = AvatarWSConnectionManager()
            # Should not raise exception
            await mgr.connect(mock_websocket)
            assert mock_websocket in mgr.active_connections

    def test_disconnect_websocket(self):
        """Test WebSocket disconnection."""
        mock_websocket = Mock(spec=WebSocket)
        mgr = AvatarWSConnectionManager()
        mgr.active_connections.append(mock_websocket)

        mgr.disconnect(mock_websocket)
        assert mock_websocket not in mgr.active_connections

    def test_disconnect_nonexistent_websocket(self):
        """Test disconnecting a WebSocket that's not in the list."""
        mock_websocket = Mock(spec=WebSocket)
        mgr = AvatarWSConnectionManager()

        # Should not raise exception
        mgr.disconnect(mock_websocket)
        assert len(mgr.active_connections) == 0

    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending personal message to WebSocket."""
        mock_websocket = AsyncMock(spec=WebSocket)
        mgr = AvatarWSConnectionManager()

        message = {"type": "test", "data": "hello"}
        await mgr.send_personal_message(message, mock_websocket)

        mock_websocket.send_text.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_send_personal_message_with_error(self):
        """Test sending personal message when send fails."""
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.send_text.side_effect = Exception("Send failed")
        mgr = AvatarWSConnectionManager()

        message = {"type": "test", "data": "hello"}
        # Should not raise exception
        await mgr.send_personal_message(message, mock_websocket)

    def test_broadcast_state_change_with_theme_resolver(self):
        """Test broadcast with theme resolver."""
        theme_resolver = Mock(return_value="light")
        mgr = AvatarWSConnectionManager(theme_resolver=theme_resolver)

        message = {
            "type": "state_change",
            "data": {"persona_id": "computer", "state": "responding"},
        }

        with patch.object(mgr, "active_connections", []):
            mgr.broadcast_state_change(message)

            # Verify theme was added to message data
            assert message["data"]["theme"] == "light"
            theme_resolver.assert_called_once_with("computer")

    def test_broadcast_state_change_with_theme_resolver_error(self):
        """Test broadcast when theme resolver raises exception."""
        theme_resolver = Mock(side_effect=Exception("Theme error"))
        mgr = AvatarWSConnectionManager(theme_resolver=theme_resolver)

        message = {
            "type": "state_change",
            "data": {"persona_id": "computer", "state": "responding"},
        }

        with patch.object(mgr, "active_connections", []):
            # Should not raise exception
            mgr.broadcast_state_change(message)

    @pytest.mark.asyncio
    async def test_broadcast_state_change_with_connections(self):
        """Test broadcast to multiple WebSocket connections."""
        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)
        mock_ws3 = AsyncMock(spec=WebSocket)
        mock_ws3.send_text.side_effect = Exception("Send failed")

        mgr = AvatarWSConnectionManager()
        mgr.active_connections = [mock_ws1, mock_ws2, mock_ws3]

        message = {"type": "test", "data": "broadcast"}

        with patch("asyncio.get_running_loop") as mock_get_loop:
            mock_loop = Mock()
            mock_get_loop.return_value = mock_loop

            mgr.broadcast_state_change(message)

            # Verify task was created
            mock_loop.create_task.assert_called_once()

    def test_broadcast_state_change_no_event_loop(self):
        """Test broadcast when no event loop is running."""
        mgr = AvatarWSConnectionManager()
        mgr.active_connections = []

        message = {"type": "test", "data": "broadcast"}

        with patch("asyncio.get_running_loop", side_effect=RuntimeError("No loop")):
            with patch("asyncio.run") as mock_run:
                mgr.broadcast_state_change(message)
                mock_run.assert_called_once()


class TestAvatarAudioQueue:
    """Test AvatarAudioQueue functionality."""

    def test_init(self):
        """Test audio queue initialization."""
        mock_manager = Mock()
        queue = AvatarAudioQueue(mock_manager)

        assert queue.manager == mock_manager
        assert isinstance(queue.queue, asyncio.Queue)
        assert queue._processor_task is None
        assert queue._current_play_task is None

    def test_is_speaking_false(self):
        """Test is_speaking property when not speaking."""
        mock_manager = Mock()
        queue = AvatarAudioQueue(mock_manager)

        assert queue.is_speaking is False

    def test_is_speaking_true(self):
        """Test is_speaking property when speaking."""
        mock_manager = Mock()
        queue = AvatarAudioQueue(mock_manager)

        mock_task = Mock()
        mock_task.done.return_value = False
        queue._current_play_task = mock_task

        assert queue.is_speaking is True

    @pytest.mark.asyncio
    async def test_play_audio_with_audio(self):
        """Test audio playback with audio data."""
        mock_manager = Mock()
        queue = AvatarAudioQueue(mock_manager)

        audio_data = b"fake audio data" * 100  # 1500 bytes

        with patch("asyncio.sleep") as mock_sleep:
            await queue._play_audio(audio_data)
            # Should sleep for 1.5 seconds (1500 bytes / 1000)
            mock_sleep.assert_called_once_with(1.5)

    @pytest.mark.asyncio
    async def test_play_audio_without_audio(self):
        """Test audio playback without audio data."""
        mock_manager = Mock()
        queue = AvatarAudioQueue(mock_manager)

        with patch("asyncio.sleep") as mock_sleep:
            await queue._play_audio(None)
            mock_sleep.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_enqueue_message(self):
        """Test enqueueing a message."""
        mock_manager = Mock()
        queue = AvatarAudioQueue(mock_manager)

        with patch.object(queue, "_ensure_processor") as mock_ensure:
            await queue.enqueue("agent1", "Hello", b"audio")
            mock_ensure.assert_called_once()

    @pytest.mark.asyncio
    async def test_interrupt_message(self):
        """Test interrupting with a priority message."""
        mock_manager = Mock()
        queue = AvatarAudioQueue(mock_manager)

        # Add some items to queue first
        await queue.queue.put(("agent1", "msg1", None))
        await queue.queue.put(("agent2", "msg2", None))

        # Mock current playing task
        mock_task = Mock()
        mock_task.done.return_value = False
        mock_task.cancel = Mock()
        queue._current_play_task = mock_task

        with patch.object(queue, "_ensure_processor") as mock_ensure:
            await queue.interrupt("agent3", "Priority message", b"priority_audio")

            # Should cancel current task
            mock_task.cancel.assert_called_once()

            # Queue should be cleared and new message added
            assert queue.queue.qsize() == 1
            mock_ensure.assert_called_once()

    def test_ensure_processor_creates_task(self):
        """Test _ensure_processor creates a new task."""
        mock_manager = Mock()
        queue = AvatarAudioQueue(mock_manager)

        with patch("asyncio.get_running_loop") as mock_get_loop:
            mock_loop = Mock()
            mock_get_loop.return_value = mock_loop

            queue._ensure_processor()

            mock_loop.create_task.assert_called_once()

    def test_ensure_processor_no_event_loop(self):
        """Test _ensure_processor when no event loop is running."""
        mock_manager = Mock()
        queue = AvatarAudioQueue(mock_manager)

        with patch("asyncio.get_running_loop", side_effect=RuntimeError("No loop")):
            with patch("asyncio.run") as mock_run:
                queue._ensure_processor()
                mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_queue_item(self):
        """Test processing a single queue item."""
        mock_manager = Mock()
        queue = AvatarAudioQueue(mock_manager)

        # Add item to queue
        await queue.queue.put(("agent1", "Hello", b"audio"))

        with patch.object(queue, "_play_audio", new_callable=AsyncMock) as mock_play:
            await queue._process()

            # Should broadcast start and end events
            assert mock_manager.broadcast_state_change.call_count == 2

            # Check start event
            start_call = mock_manager.broadcast_state_change.call_args_list[0][0][0]
            assert start_call["type"] == "avatar_audio_start"
            assert start_call["data"]["agent_id"] == "agent1"
            assert start_call["data"]["message"] == "Hello"

            # Check end event
            end_call = mock_manager.broadcast_state_change.call_args_list[1][0][0]
            assert end_call["type"] == "avatar_audio_end"
            assert end_call["data"]["agent_id"] == "agent1"
            assert "interrupted" not in end_call["data"]

    @pytest.mark.asyncio
    async def test_process_queue_item_cancelled(self):
        """Test processing a queue item that gets cancelled."""
        mock_manager = Mock()
        queue = AvatarAudioQueue(mock_manager)

        # Add item to queue
        await queue.queue.put(("agent1", "Hello", b"audio"))

        with patch.object(queue, "_play_audio", new_callable=AsyncMock) as mock_play:
            mock_play.side_effect = asyncio.CancelledError()

            await queue._process()

            # Should broadcast start and interrupted end events
            assert mock_manager.broadcast_state_change.call_count == 2

            # Check interrupted end event
            end_call = mock_manager.broadcast_state_change.call_args_list[1][0][0]
            assert end_call["type"] == "avatar_audio_end"
            assert end_call["data"]["interrupted"] is True


class TestAvatarWSHelpers:
    """Test helper functions and WebSocket endpoint."""

    @pytest.mark.asyncio
    async def test_queue_avatar_message(self):
        """Test queue_avatar_message helper function."""
        with patch.object(
            audio_queue, "enqueue", new_callable=AsyncMock
        ) as mock_enqueue:
            await queue_avatar_message("agent1", "Hello", b"audio")
            mock_enqueue.assert_called_once_with("agent1", "Hello", b"audio")

    @pytest.mark.asyncio
    async def test_interrupt_avatar_queue(self):
        """Test interrupt_avatar_queue helper function."""
        with patch.object(
            audio_queue, "interrupt", new_callable=AsyncMock
        ) as mock_interrupt:
            await interrupt_avatar_queue("agent1", "Priority", b"audio")
            mock_interrupt.assert_called_once_with("agent1", "Priority", b"audio")

    @pytest.mark.asyncio
    async def test_avatar_ws_endpoint_normal_flow(self):
        """Test WebSocket endpoint normal message flow."""
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.receive_text.side_effect = [
            json.dumps({"type": "avatar_ready"}),
            WebSocketDisconnect(),
        ]

        with patch.object(manager, "connect", new_callable=AsyncMock) as mock_connect:
            with patch.object(
                manager, "send_personal_message", new_callable=AsyncMock
            ) as mock_send:
                with patch.object(manager, "disconnect") as mock_disconnect:
                    await avatar_ws_endpoint(mock_websocket)

                    mock_connect.assert_called_once_with(mock_websocket)
                    mock_send.assert_called_once_with(
                        {"type": "ack", "data": "ok"}, mock_websocket
                    )
                    mock_disconnect.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_avatar_ws_endpoint_invalid_json(self):
        """Test WebSocket endpoint with invalid JSON."""
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.receive_text.side_effect = [
            "invalid json",
            WebSocketDisconnect(),
        ]

        with patch.object(manager, "connect", new_callable=AsyncMock):
            with patch.object(manager, "disconnect") as mock_disconnect:
                await avatar_ws_endpoint(mock_websocket)
                mock_disconnect.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_avatar_ws_endpoint_unknown_message_type(self):
        """Test WebSocket endpoint with unknown message type."""
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.receive_text.side_effect = [
            json.dumps({"type": "unknown_type", "data": "test"}),
            WebSocketDisconnect(),
        ]

        with patch.object(manager, "connect", new_callable=AsyncMock):
            with patch.object(manager, "disconnect") as mock_disconnect:
                await avatar_ws_endpoint(mock_websocket)
                mock_disconnect.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_avatar_ws_endpoint_general_exception(self):
        """Test WebSocket endpoint with general exception."""
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.receive_text.side_effect = Exception("Connection error")

        with patch.object(manager, "connect", new_callable=AsyncMock):
            with patch.object(manager, "disconnect") as mock_disconnect:
                await avatar_ws_endpoint(mock_websocket)
                mock_disconnect.assert_called_once_with(mock_websocket)


class TestGlobalInstances:
    """Test global manager and audio_queue instances."""

    def test_global_manager_instance(self):
        """Test that global manager instance exists."""
        assert isinstance(manager, AvatarWSConnectionManager)

    def test_global_audio_queue_instance(self):
        """Test that global audio_queue instance exists."""
        assert isinstance(audio_queue, AvatarAudioQueue)
        assert audio_queue.manager == manager