from unittest.mock import patch
import pytest


def test_report_error(setup_executor):
    """Test error reporting functionality."""
    with patch("logging.critical") as mock_log:
        setup_executor.report_error("test_cmd", "Test error")
        mock_log.assert_called()
        call_args = mock_log.call_args[0][0]
        assert "test_cmd" in call_args
        assert "Test error" in call_args


def test_execute_command_failure_handling(setup_executor):
    """Test execute_command returns True even when execution method returns False."""
    with patch.object(setup_executor, "_execute_keybinding") as mock_key:
        mock_key.return_value = False
        result = setup_executor.execute_command("test_cmd")
        assert result is True  # still returns True for valid commands
        mock_key.assert_called_once_with("test_cmd", "space")


def test_execute_command_exception_handling(setup_executor):
    """Test that exceptions during execution are handled gracefully."""
    with patch.object(setup_executor, "_execute_keybinding", side_effect=Exception("Test error")):
        with patch.object(setup_executor, "post_execute_hook") as mock_post:
            result = setup_executor.execute_command("test_cmd")
            assert result is False
            mock_post.assert_called_once_with("test_cmd")


def test_execute_command_invalid_action_type_new_format(setup_executor):
    """Test execute_command with invalid action type in new format."""
    with patch.object(setup_executor, "_execute_keybinding", side_effect=TypeError("Invalid action type")):
        with patch.object(setup_executor, "post_execute_hook") as mock_post:
            result = setup_executor.execute_command("test_cmd")
            assert result is False
            mock_post.assert_called_once_with("test_cmd")


def test_execute_command_no_valid_action_old_format(setup_executor):
    """Test execute_command with no valid action in old format."""
    with patch.object(setup_executor, "_execute_keybinding", side_effect=TypeError("No valid action")):
        with patch.object(setup_executor, "post_execute_hook") as mock_post:
            result = setup_executor.execute_command("test_cmd")
            assert result is False
            mock_post.assert_called_once_with("test_cmd")


def test_report_error_with_utils_logger(setup_executor):
    """Test report_error with utils logger available."""
    with patch("logging.critical") as mock_log:
        with patch("chatty_commander.utils.logger.report_error") as mock_utils:
            setup_executor.report_error("test_cmd", "Test error")
            mock_log.assert_called_once_with("Error in test_cmd: Test error")
            mock_utils.assert_called_once_with("Test error", context="test_cmd")


def test_report_error_without_utils_logger(setup_executor):
    """Test report_error without utils logger (ImportError)."""
    with patch("logging.critical") as mock_log:
        with patch("chatty_commander.utils.logger.report_error", side_effect=ImportError):
            setup_executor.report_error("test_cmd", "Test error")
            mock_log.assert_called_once_with("Error in test_cmd: Test error")
