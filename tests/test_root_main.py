import pytest
from unittest.mock import patch
import sys

def test_root_main():
    """Verify that src/main.py delegates to chatty_commander.main.main()"""
    with patch("chatty_commander.main.main", return_value=0) as mock_main:
        # Import dynamically to ensure the patch is applied when it executes
        import src.main as root_main
        
        result = root_main.main()
        
        assert result == 0
        mock_main.assert_called_once()
