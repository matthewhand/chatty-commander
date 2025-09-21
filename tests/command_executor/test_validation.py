
def test_validate_command_success(setup_executor):
    """Test validate_command with valid command."""
    result = setup_executor.validate_command("test_cmd")
    assert result is True


def test_validate_command_missing(setup_executor):
    """Test validate_command with missing command."""
    assert setup_executor.validate_command("missing_cmd") is False


def test_validate_command_empty_name(setup_executor):
    """Test validate_command with empty command name."""
    assert setup_executor.validate_command("") is False
    assert setup_executor.validate_command("   ") is False


def test_validate_command_none_name(setup_executor):
    """Test validate_command with None command name."""
    assert setup_executor.validate_command(None) is False


def test_validate_command_new_format_valid(setup_executor):
    """Test validate_command with valid new format commands."""
    setup_executor.config.model_actions = {
        "keypress_cmd": {"action": "keypress", "keys": "ctrl+c"},
        "url_cmd": {"action": "url", "url": "http://example.com"},
        "shell_cmd": {"action": "shell", "cmd": "echo test"},
    }
    assert setup_executor.validate_command("keypress_cmd") is True
    assert setup_executor.validate_command("url_cmd") is True
    assert setup_executor.validate_command("shell_cmd") is True


def test_validate_command_new_format_invalid_action_type(setup_executor):
    """Expect ValidationError for invalid action type."""
    from chatty_commander.exceptions import ValidationError
    setup_executor.config.model_actions = {"test_cmd": {"action": "invalid_action", "keys": "test"}}
    with pytest.raises(ValidationError):
        setup_executor.validate_command("test_cmd")(setup_executor):
    """Test validate_command with invalid action type in new format."""
    setup_executor.config.model_actions = {
        "test_cmd": {"action": "invalid_action", "keys": "test"}
    }
    assert setup_executor.validate_command("test_cmd") is False


def test_validate_command_new_format_missing_fields(setup_executor):
    """Expect ValidationError for missing required fields."""
    from chatty_commander.exceptions import ValidationError
    setup_executor.config.model_actions = {
        "keypress_cmd": {"action": "keypress"},
        "url_cmd": {"action": "url"},
        "shell_cmd": {"action": "shell"},
    }
    with pytest.raises(ValidationError):
        setup_executor.validate_command("keypress_cmd")(setup_executor):
    """Test validate_command with missing required fields in new format."""
    setup_executor.config.model_actions = {
        "keypress_cmd": {"action": "keypress"},  # Missing keys
        "url_cmd": {"action": "url"},  # Missing url
        "shell_cmd": {"action": "shell"},  # Missing cmd
    }
    assert setup_executor.validate_command("keypress_cmd") is False
    assert setup_executor.validate_command("url_cmd") is False
    assert setup_executor.validate_command("shell_cmd") is False


def test_validate_command_old_format_valid(setup_executor):
    """Test validate_command with valid old format commands."""
    setup_executor.config.model_actions = {
        "keypress_cmd": {"keypress": "ctrl+c"},
        "url_cmd": {"url": "http://example.com"},
        "shell_cmd": {"shell": "echo test"},
    }
    assert setup_executor.validate_command("keypress_cmd") is True
    assert setup_executor.validate_command("url_cmd") is True
    assert setup_executor.validate_command("shell_cmd") is True


def test_validate_command_old_format_invalid(setup_executor):
    """Expect ValidationError for invalid old format commands."""
    from chatty_commander.exceptions import ValidationError
    setup_executor.config.model_actions = {"test_cmd": {"invalid": "value"}}
    with pytest.raises(ValidationError):
        setup_executor.validate_command("test_cmd")(setup_executor):
    """Test validate_command with invalid old format commands."""
    setup_executor.config.model_actions = {"test_cmd": {"invalid": "value"}}
    assert setup_executor.validate_command("test_cmd") is False
