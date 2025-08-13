from pathlib import Path

import pytest


def pytest_ignore_collect(collection_path: Path, config: "pytest.Config") -> bool:
    """Ignore certain paths during test collection using pathlib.Path as per pytest>=8."""
    # Keep existing logic if any; default to not ignoring.
    return False
