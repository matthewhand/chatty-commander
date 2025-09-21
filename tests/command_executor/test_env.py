import os
from unittest.mock import patch


def test_execute_command_sets_display_env_var(setup_executor):
    """Test that execute_command sets DISPLAY environment variable if not set."""
    with patch.dict(os.environ, {}, clear=True):  # simulate no env vars
        with patch.object(setup_executor, "_execute_keybinding") as mock_key:
            mock_key.return_value = True
            setup_executor.execute_command("test_cmd")
            assert os.environ.get("DISPLAY") == ":0"
