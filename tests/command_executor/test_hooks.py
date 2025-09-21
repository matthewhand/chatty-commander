from unittest.mock import patch


def test_execute_command_hooks_called(setup_executor):
    """Test that pre and post execute hooks are called."""
    with patch.object(setup_executor, "pre_execute_hook") as mock_pre:
        with patch.object(setup_executor, "post_execute_hook") as mock_post:
            with patch.object(setup_executor, "_execute_keybinding", return_value=True):
                setup_executor.execute_command("test_cmd")
                mock_pre.assert_called_once_with("test_cmd")
                mock_post.assert_called_once_with("test_cmd")
