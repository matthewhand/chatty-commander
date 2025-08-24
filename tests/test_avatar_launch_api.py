"""Tests for the avatar launch API endpoint."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.routes.avatar_api import router as avatar_router


class TestAvatarLaunchAPI:
    """Test suite for the avatar launch API endpoint."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with avatar router."""
        app = FastAPI()
        app.include_router(avatar_router)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @patch('asyncio.create_subprocess_exec')
    def test_launch_avatar_success(self, mock_subprocess, client):
        """Test successful avatar launch."""
        # Mock successful process creation
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None  # Process is still running
        mock_subprocess.return_value = mock_process

        response = client.post("/avatar/launch")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Avatar launched successfully"
        assert data["pid"] == 12345

        # Verify subprocess was called with correct arguments
        mock_subprocess.assert_called_once()
        args, kwargs = mock_subprocess.call_args

        # Check command arguments
        assert args[0] == sys.executable
        assert args[1] == "-m"
        assert args[2] == "src.chatty_commander.main"
        assert args[3] == "--gui"

        # Check subprocess options
        assert kwargs["stdout"] == asyncio.subprocess.PIPE
        assert kwargs["stderr"] == asyncio.subprocess.PIPE
        assert kwargs["start_new_session"] is True
        assert "cwd" in kwargs

    @patch('asyncio.create_subprocess_exec')
    def test_launch_avatar_process_exits_immediately(self, mock_subprocess, client):
        """Test avatar launch when process exits immediately."""
        # Mock process that exits immediately with error
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = 1  # Process exited with error
        mock_process.communicate.return_value = (b"", b"Error: GUI not available")
        mock_subprocess.return_value = mock_process

        response = client.post("/avatar/launch")

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Avatar failed to start" in data["detail"]
        assert "Error: GUI not available" in data["detail"]

    @patch('asyncio.create_subprocess_exec')
    def test_launch_avatar_subprocess_exception(self, mock_subprocess, client):
        """Test avatar launch when subprocess creation fails."""
        # Mock subprocess creation failure
        mock_subprocess.side_effect = OSError("Permission denied")

        response = client.post("/avatar/launch")

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to launch avatar" in data["detail"]
        assert "Permission denied" in data["detail"]

    @patch('asyncio.create_subprocess_exec')
    def test_launch_avatar_working_directory(self, mock_subprocess, client):
        """Test that avatar is launched from correct working directory."""
        # Mock successful process creation
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None
        mock_subprocess.return_value = mock_process

        response = client.post("/avatar/launch")

        assert response.status_code == 200

        # Verify working directory is set correctly
        args, kwargs = mock_subprocess.call_args
        cwd = Path(kwargs["cwd"])

        # Should be project root (4 levels up from avatar_api.py)
        expected_root = Path(__file__).resolve().parents[1]  # Go up to project root
        assert cwd.resolve() == expected_root.resolve()

    @patch('asyncio.create_subprocess_exec')
    @patch('asyncio.sleep')
    def test_launch_avatar_startup_delay(self, mock_sleep, mock_subprocess, client):
        """Test that there's a startup delay to check process status."""
        # Mock successful process creation
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None
        mock_subprocess.return_value = mock_process

        response = client.post("/avatar/launch")

        assert response.status_code == 200

        # Verify sleep was called to allow process to start
        mock_sleep.assert_called_once_with(0.1)

    @patch('asyncio.create_subprocess_exec')
    def test_launch_avatar_multiple_calls(self, mock_subprocess, client):
        """Test multiple avatar launch calls."""
        # Mock successful process creation
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None
        mock_subprocess.return_value = mock_process

        # First call
        response1 = client.post("/avatar/launch")
        assert response1.status_code == 200

        # Second call should also succeed (new process)
        mock_process.pid = 12346  # Different PID
        response2 = client.post("/avatar/launch")
        assert response2.status_code == 200

        data2 = response2.json()
        assert data2["pid"] == 12346

        # Verify subprocess was called twice
        assert mock_subprocess.call_count == 2

    @patch('asyncio.create_subprocess_exec')
    def test_launch_avatar_command_construction(self, mock_subprocess, client):
        """Test that the launch command is constructed correctly."""
        # Mock successful process creation
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None
        mock_subprocess.return_value = mock_process

        response = client.post("/avatar/launch")

        assert response.status_code == 200

        # Verify command construction
        args, kwargs = mock_subprocess.call_args
        command_parts = args

        assert len(command_parts) == 4
        assert command_parts[0] == sys.executable
        assert command_parts[1] == "-m"
        assert command_parts[2] == "src.chatty_commander.main"
        assert command_parts[3] == "--gui"

    @patch('asyncio.create_subprocess_exec')
    def test_launch_avatar_process_detachment(self, mock_subprocess, client):
        """Test that the avatar process is properly detached."""
        # Mock successful process creation
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None
        mock_subprocess.return_value = mock_process

        response = client.post("/avatar/launch")

        assert response.status_code == 200

        # Verify process detachment settings
        args, kwargs = mock_subprocess.call_args
        assert kwargs["start_new_session"] is True
        assert kwargs["stdout"] == asyncio.subprocess.PIPE
        assert kwargs["stderr"] == asyncio.subprocess.PIPE

    @patch('asyncio.create_subprocess_exec')
    def test_launch_avatar_error_handling_with_stderr(self, mock_subprocess, client):
        """Test error handling when process fails with stderr output."""
        # Mock process that exits with detailed error
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = 1
        mock_process.communicate.return_value = (
            b"Starting avatar...",
            b"ImportError: No module named 'PyQt5'",
        )
        mock_subprocess.return_value = mock_process

        response = client.post("/avatar/launch")

        assert response.status_code == 500
        data = response.json()
        assert "No module named 'PyQt5'" in data["detail"]

    @patch('asyncio.create_subprocess_exec')
    def test_launch_avatar_error_handling_no_stderr(self, mock_subprocess, client):
        """Test error handling when process fails without stderr output."""
        # Mock process that exits without stderr
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b"", b"")
        mock_subprocess.return_value = mock_process

        response = client.post("/avatar/launch")

        assert response.status_code == 500
        data = response.json()
        assert "Unknown error" in data["detail"]

    def test_launch_avatar_endpoint_exists(self, client):
        """Test that the avatar launch endpoint is properly registered."""
        # Test with invalid method to confirm endpoint exists
        response = client.get("/avatar/launch")
        assert response.status_code == 405  # Method Not Allowed

        # Test with correct method
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.pid = 12345
            mock_process.returncode = None
            mock_subprocess.return_value = mock_process

            response = client.post("/avatar/launch")
            assert response.status_code == 200
