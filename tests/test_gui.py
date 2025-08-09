import sys
from unittest.mock import patch

import pytest

# Add the root directory to the path to allow importing main and gui
sys.path.insert(0, ".")

def test_gui_module_imports():
    """Verify that the gui module can be imported without errors."""
    try:
        import gui
        assert gui.run_gui is not None, "run_gui function should exist"
    except ImportError as e:
        pytest.fail(f"Failed to import the gui module: {e}")

# CORRECTED: We now patch 'gui.run_gui' which is the actual target.
@patch('gui.run_gui')
def test_main_calls_run_gui_with_gui_flag(mock_run_gui):
    """
    Test that calling main with the --gui flag correctly calls the run_gui function.
    """
    # Import main here, after the patch is active
    import main

    test_args = ['main.py', '--gui']
    with patch.object(sys, 'argv', test_args):
        # The main function might call sys.exit(), so we catch it.
        with pytest.raises(SystemExit):
            main.main()

    # Assert that our mocked run_gui function was called exactly once.
    mock_run_gui.assert_called_once()
