# Pytest configuration to constrain test discovery and avoid permission/cache issues

import os
from pathlib import Path

import pytest

# Ensure pytest never wanders into virtual environments or external directories.
# This complements [tool.pytest.ini_options].testpaths in pyproject.toml.
EXCLUDE_DIR_NAMES: list[str] = [
    ".venv",
    "venv",
    "env",
    ".env",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".gitlab",
    ".github",
    "site-packages",
    "archive",  # keep tests out of archived content by default
    "webui/frontend/node_modules",
]


def _is_path_excluded(path: Path) -> bool:
    parts = set(path.parts)
    # Quick name-based exclusion
    if any(name in parts for name in EXCLUDE_DIR_NAMES):
        return True
    # Avoid entering any virtualenv or site-packages by absolute path hints
    text = str(path)
    forbidden_substrings = [
        "/site-packages/",
        "/.venv/",
        "/venv/",
        "/env/",
    ]
    return any(s in text for s in forbidden_substrings)


def pytest_ignore_collect(path: Path, config: pytest.Config) -> bool:  # noqa: D401
    """
    Decide whether to ignore a given path during test collection.

    This prevents pytest from traversing into virtualenvs or other non-project
    directories that can cause PermissionError or unnecessary collection time.
    """
    try:
        # Normalize to absolute path for robust checks
        p = path if path.is_absolute() else (config.rootpath / path).resolve()
    except Exception:
        # If resolution fails for any reason, be conservative and do not ignore.
        return False

    # Respect configured testpaths; if provided, do not ignore paths inside them
    try:
        testpaths = [Path(tp) for tp in config.getini("testpaths")]  # type: ignore[list-item]
    except Exception:
        testpaths = []

    for tp in testpaths:
        try:
            base = tp if tp.is_absolute() else (config.rootpath / tp).resolve()
            if str(p).startswith(str(base)):
                # Inside an allowed test path: do not ignore
                return False
        except Exception:
            # If resolution fails, skip this testpath entry
            continue

    return _is_path_excluded(p)


def pytest_configure(config: pytest.Config) -> None:
    """
    Ensure cache directory lives under the repository root to avoid permission issues.
    """
    # If the user overrides cache_dir in CLI or config, respect it.
    current_cache_dir = config.getini("cache_dir")
    # Only adjust if it's the default and not absolute outside root
    if not current_cache_dir:
        # Default to .pytest_cache in project root if unset
        os.environ.setdefault("PYTEST_ADDOPTS", "")
        # No direct programmatic setter for cache_dir; it's already set in pyproject.toml
        # This hook exists mainly to document the intent and future-proof adjustments.
        pass
