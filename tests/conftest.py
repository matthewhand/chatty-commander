import sys
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def mock_dependencies(monkeypatch):
    """Mock GUI and hardware-related modules to prevent errors in CI/headless environments."""
    # Mock GUI packages that cause issues in headless environments
    monkeypatch.setitem(sys.modules, 'pyautogui', MagicMock())
    monkeypatch.setitem(sys.modules, 'mouseinfo', MagicMock())

    # Mock the Model class directly where it's imported and used
    monkeypatch.setattr('model_manager.Model', MagicMock())


import os  # noqa: E402 - imports after fixtures for test isolation/setup
import stat  # noqa: E402 - imports after fixtures for test isolation/setup


@pytest.fixture(autouse=True)
def fix_pytest_cache_permissions():
    """
    Ensure the .pytest_cache directory has correct permissions to avoid cache permission warnings.
    """
    cache_dir = ".pytest_cache"
    if os.path.exists(cache_dir):
        os.chmod(cache_dir, stat.S_IRWXU)
