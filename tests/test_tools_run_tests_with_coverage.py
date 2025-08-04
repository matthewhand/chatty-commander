import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, call

import importlib
import runpy


def _run_module_as_main(module: str, inject_argv: list[str]) -> int:
    """
    Helper to run a CLI-style module with a patched sys.argv and capture SystemExit.
    Returns the exit code (int).
    """
    old_argv = sys.argv[:]
    sys.argv = [module] + inject_argv
    try:
        try:
            runpy.run_module(module, run_name="__main__")
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 0
            return code
        # If no SystemExit raised, assume success
        return 0
    finally:
        sys.argv = old_argv


def test_cli_parsing_and_success_path(monkeypatch, tmp_path: Path):
    """
    Covers the happy path:
    - CLI parses default args
    - Invokes pytest main (mocked) with coverage flags
    - Returns exit code 0
    """
    mod_name = "src.chatty_commander.tools.run_tests_with_coverage"
    spec = importlib.util.find_spec(mod_name)
    assert spec is not None, f"Module {mod_name} not found"

    # Mock pytest.main to simulate success (exit code 0)
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    def fake_pytest_main(args: list[str]) -> int:
        calls.append(((tuple(args),), {}))
        return 0

    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    monkeypatch.setitem(sys.modules, "pytest", MagicMock(main=fake_pytest_main))

    code = _run_module_as_main(mod_name, [])
    assert code == 0, "Expected exit code 0 for success path"

    # Verify arguments include coverage flags and src
    assert calls, "pytest.main was not called"
    (args_tuple,), _ = calls[-1]
    args = list(args_tuple)
    # Basic expectations: --cov=src and --cov-report should be present
    assert any(arg.startswith("--cov=src") for arg in args), f"Missing --cov=src in {args}"
    assert any(arg.startswith("--cov-report=") for arg in args), f"Missing --cov-report in {args}"


def test_cli_failure_bubbles_nonzero_exit(monkeypatch, tmp_path: Path):
    """
    Covers failure path:
    - pytest.main returns non-zero
    - Tool should exit non-zero
    """
    mod_name = "src.chatty_commander.tools.run_tests_with_coverage"
    spec = importlib.util.find_spec(mod_name)
    assert spec is not None, f"Module {mod_name} not found"

    def fake_pytest_main_fail(args: list[str]) -> int:
        return 3

    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    monkeypatch.setitem(sys.modules, "pytest", MagicMock(main=fake_pytest_main_fail))

    code = _run_module_as_main(mod_name, [])
    assert code == 3, "Non-zero exit code from pytest should propagate"


def test_cli_allows_custom_paths(monkeypatch, tmp_path: Path):
    """
    If the tool supports passing test paths via argv, ensure they are forwarded to pytest.main.
    We simulate by inspecting the args passed into mocked pytest.main.
    """
    mod_name = "src.chatty_commander.tools.run_tests_with_coverage"
    spec = importlib.util.find_spec(mod_name)
    assert spec is not None, f"Module {mod_name} not found"

    recorded_calls: list[list[str]] = []

    def fake_pytest_main(args: list[str]) -> int:
        recorded_calls.append(list(args))
        return 0

    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    monkeypatch.setitem(sys.modules, "pytest", MagicMock(main=fake_pytest_main))

    # Pass a couple custom paths (these may or may not exist; we only assert passthrough)
    custom = ["tests/test_cli.py", "tests/test_openapi_endpoints.py"]
    code = _run_module_as_main(mod_name, custom)
    assert code == 0
    assert recorded_calls, "pytest.main not called"
    forwarded = recorded_calls[-1]
    # Ensure our custom paths appear in forwarded args (order may vary, so check inclusion)
    for p in custom:
        assert p in forwarded, f"Custom path {p} not forwarded in args: {forwarded}"