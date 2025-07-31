#!/usr/bin/env python3
"""
Unit tests for web_mode.py module.
Tests FastAPI endpoints, WebSocket functionality, and server configuration.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from web_mode import WebModeServer, SystemStatus, StateChangeRequest, CommandRequest
from config import Config
from state_manager import StateManager
from model_manager import ModelManager
from command_executor import CommandExecutor


class TestWebModeServer:
    """Test suite for WebModeServer class."""
    
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
        config, state_manager, model_manager, command_executor = mock_managers
        return WebModeServer(
            config_manager=config,
            state_manager=state_manager,
            model_manager=model_manager,
            command_executor=command_executor,
            no_auth=True
        )
    
    @pytest.fixture
    def test_client(self, web_server):
        """Create test client for API testing."""
        return TestClient(web_server.app)
    
    def test_server_initialization(self, web_server, mock_managers):
        """Test server initialization."""
        config, state_manager, model_manager, command_executor = mock_managers
        
        assert web_server.config_manager == config
        assert web_server.state_manager == state_manager
        assert web_server.model_manager == model_manager
        assert web_server.command_executor == command_executor
        assert web_server.no_auth is True
        assert isinstance(web_server.active_connections, set)
        assert len(web_server.active_connections) == 0
    
    def test_get_status_endpoint(self, test_client, mock_managers):
        """Test /api/v1/status endpoint."""
        _, state_manager, _, _ = mock_managers
        
        response = test_client.get("/api/v1/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "running"
        assert data["current_state"] == "idle"
        assert data["active_models"] == ["test_model"]
        assert "uptime" in data
        assert data["version"] == "0.2.0"
    
    def test_get_config_endpoint(self, test_client):
        """Test /api/v1/config endpoint."""
        response = test_client.get("/api/v1/config")
        assert response.status_code == 200
        
        data = response.json()
        assert data == {"test": "value"}
    
    def test_update_config_endpoint(self, test_client, mock_managers):
        """Test PUT /api/v1/config endpoint."""
        config, _, _, _ = mock_managers
        config.save_config = Mock()
        
        new_config = {"new_key": "new_value"}
        response = test_client.put("/api/v1/config", json=new_config)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Configuration updated successfully"
        config.save_config.assert_called_once()
    
    def test_get_state_endpoint(self, test_client, web_server):
        """Test /api/v1/state endpoint."""
        response = test_client.get("/api/v1/state")
        assert response.status_code == 200
        
        data = response.json()
        assert data["current_state"] == "idle"
        assert data["active_models"] == ["test_model"]
        assert data["last_command"] is None
        assert "timestamp" in data
    
    def test_change_state_endpoint(self, test_client, mock_managers):
        """Test POST /api/v1/state endpoint."""
        _, state_manager, _, _ = mock_managers
        
        state_request = {"state": "chatty"}
        response = test_client.post("/api/v1/state", json=state_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "State changed to chatty"
        state_manager.change_state.assert_called_once_with("chatty")
    
    def test_invalid_state_change(self, test_client):
        """Test invalid state change request."""
        invalid_request = {"state": "invalid_state"}
        response = test_client.post("/api/v1/state", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    def test_format_uptime(self, web_server):
        """Test uptime formatting."""
        # Test various uptime values
        assert web_server._format_uptime(30) == "0h 0m 30s"
        assert web_server._format_uptime(90) == "0h 1m 30s"
        assert web_server._format_uptime(3661) == "1h 1m 1s"
        assert web_server._format_uptime(90061) == "1d 1h 1m 1s"
    
    def test_broadcast_message(self, web_server):
        """Test WebSocket message broadcasting."""
        # Create mock WebSocket connections
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        
        web_server.active_connections.add(mock_ws1)
        web_server.active_connections.add(mock_ws2)
        
        from web_mode import WebSocketMessage
        message = WebSocketMessage(type="test", data={"key": "value"})
        
        # Test the broadcast method exists and can be called
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(web_server._broadcast_message(message))
            # Verify both connections received the message
            mock_ws1.send_text.assert_called_once()
            mock_ws2.send_text.assert_called_once()
        finally:
            loop.close()
    
    def test_on_state_change_callback(self, web_server):
        """Test state change callback."""
        # Mock the broadcast method
        web_server._broadcast_message = AsyncMock()
        
        # Create and run event loop to test callback
        import asyncio
        async def test_callback():
            web_server._on_state_change("idle", "chatty")
            # Give time for the task to be created
            await asyncio.sleep(0.01)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_callback())
            # Verify broadcast was called
            web_server._broadcast_message.assert_called_once()
        finally:
            loop.close()
    
    def test_on_command_detected(self, web_server):
        """Test command detection callback."""
        # Mock the broadcast method
        web_server._broadcast_message = AsyncMock()
        
        # Create and run event loop to test callback
        import asyncio
        async def test_callback():
            web_server.on_command_detected("test_command", 0.95)
            assert web_server.last_command == "test_command"
            # Give time for the task to be created
            await asyncio.sleep(0.01)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_callback())
            # Verify broadcast was called
            web_server._broadcast_message.assert_called_once()
        finally:
            loop.close()
    
    def test_on_system_event(self, web_server):
        """Test system event callback."""
        # Mock the broadcast method
        web_server._broadcast_message = AsyncMock()
        
        # Create and run event loop to test callback
        import asyncio
        async def test_callback():
            web_server.on_system_event("test_event", "test_details")
            # Give time for the task to be created
            await asyncio.sleep(0.01)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_callback())
            # Verify broadcast was called
            web_server._broadcast_message.assert_called_once()
        finally:
            loop.close()


class TestPydanticModels:
    """Test Pydantic model validation."""
    
    def test_system_status_model(self):
        """Test SystemStatus model validation."""
        status = SystemStatus(
            status="running",
            current_state="idle",
            active_models=["model1", "model2"],
            uptime="1h 30m"
        )
        
        assert status.status == "running"
        assert status.current_state == "idle"
        assert status.active_models == ["model1", "model2"]
        assert status.uptime == "1h 30m"
        assert status.version == "0.2.0"  # Default value
    
    def test_state_change_request_validation(self):
        """Test StateChangeRequest validation."""
        # Valid states
        for state in ["idle", "computer", "chatty"]:
            request = StateChangeRequest(state=state)
            assert request.state == state
        
        # Invalid state should raise validation error
        with pytest.raises(ValueError):
            StateChangeRequest(state="invalid")
    
    def test_command_request_model(self):
        """Test CommandRequest model."""
        # Without parameters
        request = CommandRequest(command="test_command")
        assert request.command == "test_command"
        assert request.parameters is None
        
        # With parameters
        params = {"key": "value", "number": 42}
        request = CommandRequest(command="test_command", parameters=params)
        assert request.command == "test_command"
        assert request.parameters == params
    
    def test_command_response_model(self):
        """Test CommandResponse model."""
        from web_mode import CommandResponse
        
        response = CommandResponse(
            success=True,
            message="Command executed successfully",
            execution_time=123.45
        )
        
        assert response.success is True
        assert response.message == "Command executed successfully"
        assert response.execution_time == 123.45


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
    """Test update config endpoint failure when config saving fails."""
    config, _, _, _ = mock_managers
    config.save_config = Mock(side_effect=Exception("Save failed"))
    new_config = {"new_key": "new_value"}
    response = test_client.put("/api/v1/config", json=new_config)
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
class TestWebModeAdditional:
    @pytest.fixture
    def mock_managers(self):
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
        config, state_manager, model_manager, command_executor = mock_managers
        return WebModeServer(config, state_manager, model_manager, command_executor)

    @pytest.fixture
    def test_client(self, web_server):
        return TestClient(web_server.app)

    def test_update_config_failure(self, test_client, mock_managers):
        """Test update config endpoint failure when config saving fails."""
        config, _, _, _ = mock_managers
        config.save_config = Mock(side_effect=Exception("Save failed"))
        new_config = {"new_key": "new_value"}
        response = test_client.put("/api/v1/config", json=new_config)
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_non_existent_endpoint(self, test_client):
        """Test accessing a non-existent endpoint returns a 404 error."""
        response = test_client.get("/api/v1/non_existent")
        assert response.status_code == 404

if __name__ == "__main__":
    pytest.main([__file__, "-v"])