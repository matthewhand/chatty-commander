
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch
from chatty_commander.web.routes.core import include_core_routes
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from datetime import datetime

# Setup minimal app with the route
app = FastAPI()

state_manager = MagicMock()
state_manager.current_state = "idle"
state_manager.get_active_models.return_value = []

router = include_core_routes(
    get_start_time=lambda: time.time(),
    get_state_manager=lambda: state_manager,
    get_config_manager=lambda: MagicMock(),
    get_last_command=lambda: None,
    get_last_state_change=lambda: datetime.now(),
    execute_command_fn=MagicMock(),
)
app.include_router(router)
client = TestClient(app)

@pytest.mark.asyncio
async def test_execute_command_calls_run_in_executor():
    """
    Verify that the execute_command endpoint delegates to a thread pool.
    """
    # Create a new app for this test to ensure clean state and avoid async library conflicts
    # TestClient in pytest-asyncio environment can be tricky.
    # Instead of full integration test, we will call the endpoint function directly.

    # Extract the route handler
    for route in router.routes:
        if route.path == "/api/v1/command" and "POST" in route.methods:
            endpoint = route.endpoint
            break
    else:
        pytest.fail("Endpoint not found")

    # Mock request object
    class MockRequest:
        command = "test_cmd"
        parameters = None

    req = MockRequest()

    # Mock asyncio.get_running_loop
    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        # Setup the future returned by run_in_executor
        f = asyncio.Future()
        f.set_result(True)
        mock_loop.run_in_executor.return_value = f

        # Call the endpoint function directly (it's an async function)
        response = await endpoint(req)

        # Verify response
        assert response.success is True

        # Verify run_in_executor was called
        mock_loop.run_in_executor.assert_called_once()

        call_args = mock_loop.run_in_executor.call_args
        assert call_args[0][0] is None  # Default executor
        # call_args[0][1] is the function
        assert call_args[0][2] == "test_cmd"
