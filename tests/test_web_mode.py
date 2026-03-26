"""Consolidated web-mode tests: server init, endpoints, WebSocket, Pydantic models."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.web_mode import (
    CommandRequest,
    StateChangeRequest,
    SystemStatus,
    WebModeServer,
)
from conftest import TestDataFactory

# ── Mock-based server initialization (TestDataFactory) ───────────────────


class TestWebModeInit:
    """Tests for WebModeServer initialization with various configurations."""

    @pytest.fixture
    def mock_state_manager(self):
        mock = MagicMock()
        mock.current_state = "idle"
        mock.add_state_change_callback = MagicMock()
        return mock

    @pytest.fixture
    def mock_model_manager(self):
        return MagicMock()

    @pytest.fixture
    def mock_command_executor(self):
        return MagicMock()

    @pytest.mark.parametrize("no_auth", [True, False])
    def test_web_mode_server_initialization(
        self, no_auth, mock_state_manager, mock_model_manager, mock_command_executor
    ):
        """Test WebModeServer initialization with auth settings."""
        config = TestDataFactory.create_mock_config(
            {
                "web_server": {
                    "host": "0.0.0.0",
                    "port": 8000,
                    "auth_enabled": not no_auth,
                }
            }
        )
        server = WebModeServer(
            config,
            mock_state_manager,
            mock_model_manager,
            mock_command_executor,
            no_auth=no_auth,
        )
        assert isinstance(server, WebModeServer)

    @pytest.mark.parametrize("host", ["0.0.0.0", "127.0.0.1", "localhost", ""])
    def test_web_mode_server_host_configuration(
        self, host, mock_state_manager, mock_model_manager, mock_command_executor
    ):
        config = TestDataFactory.create_mock_config(
            {"web_server": {"host": host, "port": 8000, "auth_enabled": False}}
        )
        server = WebModeServer(
            config, mock_state_manager, mock_model_manager, mock_command_executor
        )
        assert isinstance(server, WebModeServer)

    @pytest.mark.parametrize("port", [8000, 3000, 5000, 0, 65535, None])
    def test_web_mode_server_port_configuration(
        self, port, mock_state_manager, mock_model_manager, mock_command_executor
    ):
        config = TestDataFactory.create_mock_config(
            {"web_server": {"host": "0.0.0.0", "port": port, "auth_enabled": False}}
        )
        server = WebModeServer(
            config, mock_state_manager, mock_model_manager, mock_command_executor
        )
        assert isinstance(server, WebModeServer)

    def test_web_mode_server_cors_configuration(
        self, mock_state_manager, mock_model_manager, mock_command_executor
    ):
        config = TestDataFactory.create_mock_config()
        server = WebModeServer(
            config, mock_state_manager, mock_model_manager, mock_command_executor
        )
        assert isinstance(server, WebModeServer)

    def test_web_mode_server_websocket_management(
        self, mock_state_manager, mock_model_manager, mock_command_executor
    ):
        config = TestDataFactory.create_mock_config()
        server = WebModeServer(
            config, mock_state_manager, mock_model_manager, mock_command_executor
        )
        assert isinstance(server, WebModeServer)

    def test_web_mode_server_cache_management(
        self, mock_state_manager, mock_model_manager, mock_command_executor
    ):
        config = TestDataFactory.create_mock_config()
        server = WebModeServer(
            config, mock_state_manager, mock_model_manager, mock_command_executor
        )
        assert isinstance(server, WebModeServer)

    @pytest.mark.parametrize("uptime_seconds", [0, 60, 3600, 86400, 604800])
    def test_web_mode_server_uptime_formatting(
        self,
        uptime_seconds,
        mock_state_manager,
        mock_model_manager,
        mock_command_executor,
    ):
        config = TestDataFactory.create_mock_config()
        server = WebModeServer(
            config, mock_state_manager, mock_model_manager, mock_command_executor
        )
        assert isinstance(server, WebModeServer)


# ── Endpoint tests (TestClient) ──────────────────────────────────────────


class TestWebModeServer:
    """Test suite for WebModeServer endpoints and callbacks."""

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
        with patch(
            "chatty_commander.advisors.providers.build_provider_safe"
        ) as mock_build_provider:
            mock_provider = MagicMock()
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
        return TestClient(web_server.app)

    def test_server_initialization(self, web_server, mock_managers):
        config, state_manager, model_manager, command_executor = mock_managers

        assert web_server.config_manager == config
        assert web_server.state_manager == state_manager
        assert web_server.model_manager == model_manager
        assert web_server.command_executor == command_executor
        assert web_server.no_auth is True
        assert isinstance(web_server.active_connections, set)
        assert len(web_server.active_connections) == 0

    def test_get_status_endpoint(self, test_client, mock_managers):
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
        response = test_client.get("/api/v1/config")
        assert response.status_code == 200

        data = response.json()
        assert data["test"] == "value"
        assert "_env_overrides" in data

    def test_update_config_endpoint(self, test_client, mock_managers):
        config, _, _, _ = mock_managers
        config.save_config = Mock()

        new_config = {"new_key": "new_value"}
        response = test_client.put("/api/v1/config", json=new_config)
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Configuration updated successfully"
        config.save_config.assert_called_once()

    def test_get_state_endpoint(self, test_client, web_server):
        response = test_client.get("/api/v1/state")
        assert response.status_code == 200

        data = response.json()
        assert data["current_state"] == "idle"
        assert data["active_models"] == ["test_model"]
        assert data["last_command"] is None
        assert "timestamp" in data

    def test_change_state_endpoint(self, test_client, mock_managers):
        _, state_manager, _, _ = mock_managers

        state_request = {"state": "chatty"}
        response = test_client.post("/api/v1/state", json=state_request)
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "State changed to chatty"
        state_manager.change_state.assert_called_once_with("chatty")

    def test_invalid_state_change(self, test_client):
        invalid_request = {"state": "invalid_state"}
        response = test_client.post("/api/v1/state", json=invalid_request)
        assert response.status_code == 422

    def test_format_uptime(self, web_server):
        assert web_server._format_uptime(30) == "0h 0m 30s"
        assert web_server._format_uptime(90) == "0h 1m 30s"
        assert web_server._format_uptime(3661) == "1h 1m 1s"
        assert web_server._format_uptime(90061) == "1d 1h 1m 1s"

    def test_broadcast_message(self, web_server):
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        web_server.active_connections.add(mock_ws1)
        web_server.active_connections.add(mock_ws2)

        from chatty_commander.web.web_mode import WebSocketMessage

        message = WebSocketMessage(type="test", data={"key": "value"})

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(web_server._broadcast_message(message))
            mock_ws1.send_text.assert_called_once()
            mock_ws2.send_text.assert_called_once()
        finally:
            loop.close()

    def test_on_state_change_callback(self, web_server):
        web_server._broadcast_message = AsyncMock()

        async def test_callback():
            web_server._on_state_change("idle", "chatty")
            await asyncio.sleep(0.01)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_callback())
            web_server._broadcast_message.assert_called_once()
        finally:
            loop.close()

    def test_on_command_detected(self, web_server):
        web_server._broadcast_message = AsyncMock()

        async def test_callback():
            web_server.on_command_detected("test_command", 0.95)
            assert web_server.last_command == "test_command"
            await asyncio.sleep(0.01)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_callback())
            web_server._broadcast_message.assert_called_once()
        finally:
            loop.close()

    def test_on_system_event(self, web_server):
        web_server._broadcast_message = AsyncMock()

        async def test_callback():
            web_server.on_system_event("test_event", "test_details")
            await asyncio.sleep(0.01)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_callback())
            web_server._broadcast_message.assert_called_once()
        finally:
            loop.close()


# ── Additional endpoint edge cases ───────────────────────────────────────


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
        with patch(
            "chatty_commander.advisors.providers.build_provider_safe"
        ) as mock_build_provider:
            mock_provider = MagicMock()
            mock_provider.model = "test-model"
            mock_provider.api_mode = "completion"
            mock_build_provider.return_value = mock_provider
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


# ── Pydantic models ──────────────────────────────────────────────────────


class TestPydanticModels:
    """Test Pydantic model validation."""

    def test_system_status_model(self):
        status = SystemStatus(
            status="running",
            current_state="idle",
            active_models=["model1", "model2"],
            uptime="1h 30m",
        )

        assert status.status == "running"
        assert status.current_state == "idle"
        assert status.active_models == ["model1", "model2"]
        assert status.uptime == "1h 30m"
        assert status.version == "0.2.0"

    def test_state_change_request_validation(self):
        for state in ["idle", "computer", "chatty"]:
            request = StateChangeRequest(state=state)
            assert request.state == state

        with pytest.raises(ValueError):
            StateChangeRequest(state="invalid")

    def test_command_request_model(self):
        request = CommandRequest(command="test_command")
        assert request.command == "test_command"
        assert request.parameters is None

        params = {"key": "value", "number": 42}
        request = CommandRequest(command="test_command", parameters=params)
        assert request.command == "test_command"
        assert request.parameters == params

    def test_command_response_model(self):
        from chatty_commander.web.web_mode import CommandResponse

        response = CommandResponse(
            success=True, message="Command executed successfully", execution_time=123.45
        )

        assert response.success is True
        assert response.message == "Command executed successfully"
        assert response.execution_time == 123.45
