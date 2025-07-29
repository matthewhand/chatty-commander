import pytest
import sys
from unittest.mock import MagicMock

@pytest.fixture(autouse=True)
def mock_dependencies(monkeypatch):
    """Mock GUI and hardware-related modules to prevent errors in CI/headless environments."""
    # Mock GUI packages that cause issues in headless environments
    monkeypatch.setitem(sys.modules, 'pyautogui', MagicMock())
    monkeypatch.setitem(sys.modules, 'mouseinfo', MagicMock())
    
    # Mock the Model class directly where it's imported and used
    monkeypatch.setattr('model_manager.Model', MagicMock())