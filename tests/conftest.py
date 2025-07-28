import pytest
import sys
from unittest.mock import MagicMock

@pytest.fixture(autouse=True)
def mock_gui_modules():
    # Mock pyautogui and mouseinfo to prevent DISPLAY errors
    sys.modules['pyautogui'] = MagicMock()
    sys.modules['mouseinfo'] = MagicMock()