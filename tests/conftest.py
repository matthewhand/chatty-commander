"""Pytest configuration for Chatty Commander test suite.

This file contains portability hooks to make tests robust in restricted
sandboxes (e.g., where AF_UNIX socketpair or loopback sockets are blocked),
and ensures the project root is importable during testing.
"""

import contextlib
import os
import socket
import sys

import pytest


# Provide a robust fallback for environments that deny AF_UNIX socketpair.
def _tcp_socketpair():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Ensure fast reuse and bind to localhost ephemeral port
    with contextlib.ExitStack() as stack:
        stack.enter_context(contextlib.closing(srv))
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)

        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        stack.enter_context(contextlib.closing(c))
        c.connect(srv.getsockname())

        s, _ = srv.accept()
        # Prevent ExitStack from closing the pair we're returning
        stack.pop_all()
    return s, c


_orig_socketpair = socket.socketpair


def _safe_socketpair(*args, **kwargs):
    try:
        return _orig_socketpair(*args, **kwargs)
    except PermissionError:
        # Fallback to TCP-based pair on localhost
        return _tcp_socketpair()


# Apply the fallback globally for the test run so asyncio's selector event loop
# (used by Starlette's TestClient) can initialize even when AF_UNIX is blocked.
socket.socketpair = _safe_socketpair  # type: ignore[attr-defined]

# Ensure project root is at front so 'import main' resolves to repo's main.py shim, not any site-packages main.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _can_create_socketpair() -> bool:
    try:
        a, b = _safe_socketpair()
        a.close()
        b.close()
        return True
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    """Skip HTTP/ASGI tests when socketpair is not permitted in sandbox."""
    if _can_create_socketpair():
        return
    skip_marker = pytest.mark.skip(reason="sandbox denies socketpair needed by TestClient")
    skip_files = {
        "tests/test_web_mode_unit.py",
        "tests/test_web_integration.py",
        "tests/test_core_config_get_metrics.py",
        "tests/test_web_server_guards.py",
        "tests/test_web_context_api.py",
        "tests/test_agents_api_update_delete_404.py",
        "tests/test_advisors_memory_api.py",
        "tests/test_ws_heartbeat.py",
        "tests/test_websocket_resilience.py",
        "tests/test_avatar_selector.py",
        "tests/test_obs_metrics_prom_json.py",
        "tests/test_agents_api_create_from_description.py",
        "tests/test_ws_connection_snapshot.py",
        "tests/test_avatar_ws.py",
        "tests/test_avatar_audio_queue.py",
        "tests/test_core_endpoints_minimal.py",
        "tests/test_e2e_core_flow.py",
        "tests/test_web_advisors_api.py",
        "tests/test_advisors_memory_disabled.py",
        "tests/test_avatar_settings.py",
        "tests/test_avatar_api.py",
        "tests/test_avatar_selector_basic.py",
        "tests/test_version_git_sha_type.py",
        "tests/test_e2e_agents_flow.py",
        "tests/test_metrics_endpoint.py",
        "tests/test_agents_api_handoff_404.py",
        "tests/test_avatar_api_errors.py",
        "tests/test_core_endpoints_minimal_unknown_command.py",
        "tests/test_agents_api_errors.py",
        "tests/test_avatar_api_errors_minimal.py",
        "tests/test_core_config_put_and_metrics.py",
        "tests/test_openapi_endpoints.py",
        "tests/test_cors_no_auth.py",
        "tests/test_create_app_contract.py",
        "tests/test_bridge_unauthorized.py",
        "tests/test_agents_api_list_empty.py",
        "tests/test_avatar_api_list_success.py",
        "tests/test_agents_api_crud_happy_path.py",
        "tests/test_core_state_validation_422.py",
        "tests/test_avatar_ws_theme.py",
        "tests/test_web_mode.py",
        "tests/test_web_bridge_api.py",
        "tests/test_version_endpoint.py",
        "tests/test_metrics_increment_on_unknown_command.py",
        "tests/test_agents_api.py",
        "tests/test_performance_benchmarks.py",
        "tests/test_thinking_state_broadcast_async.py",
    }
    for item in items:
        for f in skip_files:
            if f in item.nodeid:
                item.add_marker(skip_marker)
                break
