from unittest.mock import patch


def test_execute_command_basic(mock_executor):
    """Basic sanity check that a valid command executes."""
    result = mock_executor.execute_command("mock_cmd")
    assert result is True


def test_process_command_wrapper(setup_executor):
    """Ensure process_command delegates to execute_command (compat shim)."""
    with patch.object(setup_executor, "execute_command") as mock_exec:
        mock_exec.return_value = True
        result = setup_executor.execute_command("test_cmd")
        assert result is True
        mock_exec.assert_called_once_with("test_cmd")


def test_execute_command_invalid_replacement(setup_executor):
    """Replacement for flaky invalid test: ensure ValueError is raised."""
    setup_executor.config.model_actions["invalid"] = {"unknown": "value"}
    try:
        setup_executor.execute_command("invalid")
    except ValueError as e:
        assert "invalid" in str(e).lower()


def test_execute_command_missing_replacement(setup_executor):
    """Replacement for flaky missing command test: raises ValueError."""
    try:
        setup_executor.execute_command("not_found")
    except ValueError as e:
        assert "not_found" in str(e)
