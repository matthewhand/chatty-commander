"""
Comprehensive tests for RecurringPrompt class.

Covers:
- Happy path variants (valid creation, different schedules/triggers)
- Error cases (missing required fields, invalid data)
- Template rendering (variable substitution, edge cases)
- Response handlers (different types, invalid configs)
- Edge cases (empty strings, long prompts, unicode, special chars)
- Metadata handling
- Invalid data types
"""

import pytest

from chatty_commander.advisors.recurring import RecurringPrompt


# ==============================================================================
# HAPPY PATH VARIANTS
# ==============================================================================

class TestRecurringPromptHappyPath:
    """Tests for successful RecurringPrompt creation scenarios."""

    def test_from_dict_with_all_fields(self):
        """Test creating a RecurringPrompt with all fields populated."""
        data = {
            "id": "advisor-daily-summary",
            "name": "Daily Summary Advisor",
            "description": "Summarises the last 24 hrs of chat activity.",
            "schedule": "0 9 * * *",
            "trigger": "cron",
            "context": "You are a helpful assistant.",
            "prompt": "Summarise the following {{messages}}.",
            "variables": {"messages": "<ALL_MESSAGES>"},
            "response_handler": {
                "type": "post",
                "action": "sendToDiscord",
                "channel": "#daily-summary",
            },
            "metadata": {"tags": ["daily", "summary"], "owner": "alice"},
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.id == "advisor-daily-summary"
        assert rp.name == "Daily Summary Advisor"
        assert rp.description == "Summarises the last 24 hrs of chat activity."
        assert rp.schedule == "0 9 * * *"
        assert rp.trigger == "cron"
        assert rp.context == "You are a helpful assistant."
        assert rp.prompt == "Summarise the following {{messages}}."
        assert rp.variables == {"messages": "<ALL_MESSAGES>"}
        assert rp.response_handler["type"] == "post"
        assert rp.metadata["tags"] == ["daily", "summary"]

    def test_from_dict_with_minimal_required_fields(self):
        """Test creating a RecurringPrompt with only required fields."""
        data = {
            "id": "minimal-prompt",
            "name": "Minimal Prompt",
            "description": "A minimal recurring prompt.",
            "schedule": "*/5 * * * *",
            "trigger": "cron",
            "context": "Base context",
            "prompt": "Do something.",
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.id == "minimal-prompt"
        assert rp.variables == {}
        assert rp.response_handler == {}
        assert rp.metadata == {}

    def test_from_dict_with_cron_schedule_every_minute(self):
        """Test with cron schedule running every minute."""
        data = {
            "id": "every-minute",
            "name": "Every Minute",
            "description": "Runs every minute.",
            "schedule": "* * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
        }
        rp = RecurringPrompt.from_dict(data)
        assert rp.schedule == "* * * * *"

    def test_from_dict_with_cron_schedule_specific_time(self):
        """Test with cron schedule for specific time daily."""
        data = {
            "id": "morning-brief",
            "name": "Morning Brief",
            "description": "Daily morning briefing.",
            "schedule": "0 6 * * 1-5",  # 6 AM on weekdays
            "trigger": "cron",
            "context": "Context",
            "prompt": "Good morning!",
        }
        rp = RecurringPrompt.from_dict(data)
        assert rp.schedule == "0 6 * * 1-5"

    def test_from_dict_with_interval_trigger(self):
        """Test with interval trigger type."""
        data = {
            "id": "interval-check",
            "name": "Interval Check",
            "description": "Runs at intervals.",
            "schedule": "every 30 minutes",
            "trigger": "interval",
            "context": "Context",
            "prompt": "Check status.",
        }
        rp = RecurringPrompt.from_dict(data)
        assert rp.trigger == "interval"
        assert rp.schedule == "every 30 minutes"

    def test_from_dict_with_webhook_trigger(self):
        """Test with webhook trigger type."""
        data = {
            "id": "webhook-handler",
            "name": "Webhook Handler",
            "description": "Triggered by webhook.",
            "schedule": "on-demand",
            "trigger": "webhook",
            "context": "Context",
            "prompt": "Process webhook payload.",
        }
        rp = RecurringPrompt.from_dict(data)
        assert rp.trigger == "webhook"

    def test_from_dict_with_manual_trigger(self):
        """Test with manual trigger type."""
        data = {
            "id": "manual-task",
            "name": "Manual Task",
            "description": "Manually triggered.",
            "schedule": "manual",
            "trigger": "manual",
            "context": "Context",
            "prompt": "Manual execution.",
        }
        rp = RecurringPrompt.from_dict(data)
        assert rp.trigger == "manual"


# ==============================================================================
# ERROR CASES - MISSING REQUIRED FIELDS
# ==============================================================================

class TestRecurringPromptMissingFields:
    """Tests for error cases when required fields are missing."""

    def test_missing_id_raises_value_error(self):
        """Test that missing 'id' field raises ValueError."""
        data = {
            "name": "Test",
            "description": "Test desc",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
        }
        with pytest.raises(ValueError, match="Missing required field: id"):
            RecurringPrompt.from_dict(data)

    def test_missing_name_raises_value_error(self):
        """Test that missing 'name' field raises ValueError."""
        data = {
            "id": "test-id",
            "description": "Test desc",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
        }
        with pytest.raises(ValueError, match="Missing required field: name"):
            RecurringPrompt.from_dict(data)

    def test_missing_description_raises_value_error(self):
        """Test that missing 'description' field raises ValueError."""
        data = {
            "id": "test-id",
            "name": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
        }
        with pytest.raises(ValueError, match="Missing required field: description"):
            RecurringPrompt.from_dict(data)

    def test_missing_schedule_raises_value_error(self):
        """Test that missing 'schedule' field raises ValueError."""
        data = {
            "id": "test-id",
            "name": "Test",
            "description": "Test desc",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
        }
        with pytest.raises(ValueError, match="Missing required field: schedule"):
            RecurringPrompt.from_dict(data)

    def test_missing_trigger_raises_value_error(self):
        """Test that missing 'trigger' field raises ValueError."""
        data = {
            "id": "test-id",
            "name": "Test",
            "description": "Test desc",
            "schedule": "0 * * * *",
            "context": "Context",
            "prompt": "Prompt",
        }
        with pytest.raises(ValueError, match="Missing required field: trigger"):
            RecurringPrompt.from_dict(data)

    def test_missing_context_raises_value_error(self):
        """Test that missing 'context' field raises ValueError."""
        data = {
            "id": "test-id",
            "name": "Test",
            "description": "Test desc",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "prompt": "Prompt",
        }
        with pytest.raises(ValueError, match="Missing required field: context"):
            RecurringPrompt.from_dict(data)

    def test_missing_prompt_raises_value_error(self):
        """Test that missing 'prompt' field raises ValueError."""
        data = {
            "id": "test-id",
            "name": "Test",
            "description": "Test desc",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
        }
        with pytest.raises(ValueError, match="Missing required field: prompt"):
            RecurringPrompt.from_dict(data)

    def test_empty_dict_raises_value_error(self):
        """Test that an empty dictionary raises ValueError."""
        with pytest.raises(ValueError, match="Missing required field"):
            RecurringPrompt.from_dict({})


# ==============================================================================
# TEMPLATE RENDERING
# ==============================================================================

class TestTemplateRendering:
    """Tests for prompt template rendering with variable substitution."""

    def test_render_prompt_basic_substitution(self):
        """Test basic variable substitution in prompt."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Hello {{name}}, welcome to {{place}}!",
            "variables": {"name": "Alice", "place": "Wonderland"},
        }
        rp = RecurringPrompt.from_dict(data)
        rendered = rp.render_prompt()

        assert rendered == "Hello Alice, welcome to Wonderland!"

    def test_render_prompt_with_runtime_vars(self):
        """Test that runtime variables override static variables."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Process {{data}}",
            "variables": {"data": "default_data"},
        }
        rp = RecurringPrompt.from_dict(data)
        rendered = rp.render_prompt({"data": "runtime_data"})

        assert rendered == "Process runtime_data"

    def test_render_prompt_merge_static_and_runtime_vars(self):
        """Test that runtime vars are merged with static vars."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "{{greeting}} {{name}}!",
            "variables": {"greeting": "Hello"},
        }
        rp = RecurringPrompt.from_dict(data)
        rendered = rp.render_prompt({"name": "World"})

        assert rendered == "Hello World!"

    def test_render_prompt_multiple_same_placeholder(self):
        """Test that multiple occurrences of same placeholder are replaced."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "{{item}} is here. {{item}} is there. {{item}} is everywhere.",
            "variables": {"item": "Data"},
        }
        rp = RecurringPrompt.from_dict(data)
        rendered = rp.render_prompt()

        assert rendered == "Data is here. Data is there. Data is everywhere."

    def test_render_prompt_no_placeholders(self):
        """Test rendering a prompt with no placeholders."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "This is a static prompt.",
        }
        rp = RecurringPrompt.from_dict(data)
        rendered = rp.render_prompt()

        assert rendered == "This is a static prompt."

    def test_render_prompt_missing_variable_keeps_placeholder(self):
        """Test that missing variables leave placeholder unchanged."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Hello {{name}}!",
            "variables": {},  # No variables provided
        }
        rp = RecurringPrompt.from_dict(data)
        rendered = rp.render_prompt()

        assert rendered == "Hello {{name}}!"

    def test_render_prompt_empty_variable_value(self):
        """Test rendering with empty string variable value."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Value: [{{value}}]",
            "variables": {"value": ""},
        }
        rp = RecurringPrompt.from_dict(data)
        rendered = rp.render_prompt()

        assert rendered == "Value: []"

    def test_render_prompt_none_runtime_vars(self):
        """Test rendering when runtime_vars is None."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Hello {{name}}!",
            "variables": {"name": "Alice"},
        }
        rp = RecurringPrompt.from_dict(data)
        rendered = rp.render_prompt(None)

        assert rendered == "Hello Alice!"

    def test_render_prompt_integer_value(self):
        """Test that integer values are converted to string during rendering."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Count: {{count}}",
            "variables": {"count": 42},
        }
        rp = RecurringPrompt.from_dict(data)
        rendered = rp.render_prompt()

        assert rendered == "Count: 42"

    def test_render_prompt_list_value(self):
        """Test that list values are converted to string during rendering."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Items: {{items}}",
            "variables": {"items": ["a", "b", "c"]},
        }
        rp = RecurringPrompt.from_dict(data)
        rendered = rp.render_prompt()

        assert "a" in rendered
        assert "b" in rendered
        assert "c" in rendered

    def test_render_prompt_dict_value(self):
        """Test that dict values are converted to string during rendering."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Config: {{config}}",
            "variables": {"config": {"key": "value"}},
        }
        rp = RecurringPrompt.from_dict(data)
        rendered = rp.render_prompt()

        assert "key" in rendered
        assert "value" in rendered


# ==============================================================================
# RESPONSE HANDLERS
# ==============================================================================

class TestResponseHandlers:
    """Tests for response handler configurations."""

    def test_response_handler_post_type(self):
        """Test response handler with post type."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
            "response_handler": {
                "type": "post",
                "action": "sendToSlack",
                "channel": "#general",
            },
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.response_handler["type"] == "post"
        assert rp.response_handler["action"] == "sendToSlack"
        assert rp.response_handler["channel"] == "#general"

    def test_response_handler_webhook_type(self):
        """Test response handler with webhook type."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
            "response_handler": {
                "type": "webhook",
                "url": "https://example.com/webhook",
                "method": "POST",
                "headers": {"Authorization": "Bearer token"},
            },
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.response_handler["type"] == "webhook"
        assert rp.response_handler["url"] == "https://example.com/webhook"
        assert rp.response_handler["method"] == "POST"

    def test_response_handler_empty_dict(self):
        """Test that empty response_handler dict is valid."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
            "response_handler": {},
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.response_handler == {}

    def test_response_handler_missing_type(self):
        """Test response handler with missing type field (allowed, validation elsewhere)."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
            "response_handler": {
                "action": "someAction",
            },
        }
        rp = RecurringPrompt.from_dict(data)

        assert "type" not in rp.response_handler
        assert rp.response_handler["action"] == "someAction"

    def test_response_handler_with_nested_config(self):
        """Test response handler with nested configuration."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
            "response_handler": {
                "type": "webhook",
                "config": {
                    "retry": {"count": 3, "delay": 1000},
                    "timeout": 5000,
                },
            },
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.response_handler["config"]["retry"]["count"] == 3
        assert rp.response_handler["config"]["timeout"] == 5000


# ==============================================================================
# METADATA HANDLING
# ==============================================================================

class TestMetadataHandling:
    """Tests for metadata field handling."""

    def test_metadata_with_tags(self):
        """Test metadata with tags array."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
            "metadata": {"tags": ["important", "automated", "production"]},
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.metadata["tags"] == ["important", "automated", "production"]

    def test_metadata_with_owner(self):
        """Test metadata with owner field."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
            "metadata": {"owner": "alice@example.com"},
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.metadata["owner"] == "alice@example.com"

    def test_metadata_with_custom_fields(self):
        """Test metadata with custom fields."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
            "metadata": {
                "version": "1.0.0",
                "created_at": "2024-01-15",
                "environment": "staging",
                "priority": 5,
            },
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.metadata["version"] == "1.0.0"
        assert rp.metadata["created_at"] == "2024-01-15"
        assert rp.metadata["environment"] == "staging"
        assert rp.metadata["priority"] == 5

    def test_metadata_empty_dict(self):
        """Test that empty metadata dict is valid."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
            "metadata": {},
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.metadata == {}

    def test_metadata_not_provided_defaults_to_empty_dict(self):
        """Test that missing metadata defaults to empty dict."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.metadata == {}


# ==============================================================================
# EDGE CASES
# ==============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_string_for_required_fields(self):
        """Test that empty strings are accepted for required fields."""
        data = {
            "id": "",
            "name": "",
            "description": "",
            "schedule": "",
            "trigger": "",
            "context": "",
            "prompt": "",
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.id == ""
        assert rp.name == ""
        assert rp.description == ""

    def test_very_long_prompt_over_10kb(self):
        """Test with a very long prompt (over 10KB)."""
        long_prompt = "x" * 15000  # 15KB string
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": long_prompt,
        }
        rp = RecurringPrompt.from_dict(data)

        assert len(rp.prompt) == 15000
        assert rp.prompt == long_prompt

    def test_unicode_in_prompt(self):
        """Test with Unicode characters in prompt."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test with Unicode: 你好世界 🌍 مرحبا",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context with émojis 🎉 and açcénts",
            "prompt": "Привет {{name}}! 日本語テスト 💯",
            "variables": {"name": "世界"},
        }
        rp = RecurringPrompt.from_dict(data)

        assert "Привет" in rp.prompt
        rendered = rp.render_prompt()
        assert "世界" in rendered
        assert "💯" in rendered

    def test_special_characters_in_schedule(self):
        """Test with special characters in schedule."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "*/15 0-6 * * 1,3,5",  # Complex cron
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.schedule == "*/15 0-6 * * 1,3,5"

    def test_special_characters_in_prompt(self):
        """Test with special characters in prompt."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?`~",
        }
        rp = RecurringPrompt.from_dict(data)

        assert "!@#$%^&*()" in rp.prompt

    def test_newlines_and_whitespace_in_prompt(self):
        """Test with newlines and whitespace in prompt."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Line 1\nLine 2\r\nLine 3\t\tIndented",
        }
        rp = RecurringPrompt.from_dict(data)

        assert "\n" in rp.prompt
        assert "\t" in rp.prompt

    def test_placeholder_like_text_not_replaced(self):
        """Test that text resembling placeholders but not matching variables isn't affected."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Use {{name}} but not {invalid} or {{{extra}}}",
            "variables": {"name": "Alice"},
        }
        rp = RecurringPrompt.from_dict(data)
        rendered = rp.render_prompt()

        assert rendered == "Use Alice but not {invalid} or {{{extra}}}"

    def test_whitespace_in_placeholder_name(self):
        """Test that placeholders with whitespace are handled correctly."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Hello {{ name }} and {{  name  }}!",
            "variables": {"name": "Alice"},
        }
        rp = RecurringPrompt.from_dict(data)
        rendered = rp.render_prompt()

        # Placeholders with spaces should not be replaced (exact match required)
        assert "{{ name }}" in rendered

    def test_json_in_prompt(self):
        """Test with JSON-like content in prompt."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": '{"key": "value", "nested": {"data": {{data}}}}',
            "variables": {"data": "123"},
        }
        rp = RecurringPrompt.from_dict(data)
        rendered = rp.render_prompt()

        assert '"data": 123' in rendered


# ==============================================================================
# INVALID DATA TYPES
# ==============================================================================

class TestInvalidDataTypes:
    """Tests for handling of invalid data types."""

    def test_integer_id_converted_to_string(self):
        """Test that non-string id is converted to string."""
        data = {
            "id": 12345,
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.id == "12345"
        assert isinstance(rp.id, str)

    def test_integer_name_converted_to_string(self):
        """Test that non-string name is converted to string."""
        data = {
            "id": "test",
            "name": 999,
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.name == "999"
        assert isinstance(rp.name, str)

    def test_list_as_variables_converted_to_dict(self):
        """Test that list variables are converted (though may raise error)."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
            "variables": ["item1", "item2"],
        }
        # This should work since dict() can convert list of tuples
        # but dict(["item1", "item2"]) will fail
        with pytest.raises((ValueError, TypeError)):
            RecurringPrompt.from_dict(data)

    def test_none_as_trigger_converted_to_string(self):
        """Test that None trigger is converted to string 'None'."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": None,
            "context": "Context",
            "prompt": "Prompt",
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.trigger == "None"

    def test_boolean_fields_converted_to_string(self):
        """Test that boolean values are converted to strings."""
        data = {
            "id": True,
            "name": False,
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.id == "True"
        assert rp.name == "False"


# ==============================================================================
# DATA CLASS PROPERTIES
# ==============================================================================

class TestDataclassProperties:
    """Tests for dataclass-specific behaviors."""

    def test_equality_comparison(self):
        """Test that two RecurringPrompts with same data are equal."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
        }
        rp1 = RecurringPrompt.from_dict(data)
        rp2 = RecurringPrompt.from_dict(data)

        assert rp1 == rp2

    def test_inequality_different_ids(self):
        """Test that RecurringPrompts with different ids are not equal."""
        data1 = {
            "id": "test1",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
        }
        data2 = {**data1, "id": "test2"}
        rp1 = RecurringPrompt.from_dict(data1)
        rp2 = RecurringPrompt.from_dict(data2)

        assert rp1 != rp2

    def test_repr_contains_id(self):
        """Test that repr contains the id."""
        data = {
            "id": "my-test-id",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
        }
        rp = RecurringPrompt.from_dict(data)

        assert "my-test-id" in repr(rp)

    def test_dataclass_fields_immutable(self):
        """Test that dataclass fields can be accessed and modified."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
        }
        rp = RecurringPrompt.from_dict(data)

        # Dataclasses are mutable by default
        rp.name = "Updated Name"
        assert rp.name == "Updated Name"


# ==============================================================================
# ADDITIONAL EDGE CASES FOR COMPREHENSIVE COVERAGE
# ==============================================================================

class TestAdditionalEdgeCases:
    """Additional tests for boundary conditions and edge cases."""

    def test_variables_with_none_value(self):
        """Test that None values in variables are handled."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Value: {{value}}",
            "variables": {"value": None},
        }
        rp = RecurringPrompt.from_dict(data)
        rendered = rp.render_prompt()

        assert rendered == "Value: None"

    def test_render_prompt_preserves_unmatched_placeholders(self):
        """Test that placeholders without matching variables are preserved."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "{{known}} and {{unknown}}",
            "variables": {"known": "value1"},
        }
        rp = RecurringPrompt.from_dict(data)
        rendered = rp.render_prompt()

        assert rendered == "value1 and {{unknown}}"

    def test_from_dict_extra_fields_ignored(self):
        """Test that extra fields in dict are ignored."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
            "extra_field": "should be ignored",
            "another_extra": 12345,
        }
        rp = RecurringPrompt.from_dict(data)

        assert not hasattr(rp, "extra_field")
        assert rp.id == "test"

    def test_cron_schedule_with_year_field(self):
        """Test cron schedule with extended format (6 fields including year)."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 0 1 1 * 2024",  # 6-field cron
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
        }
        rp = RecurringPrompt.from_dict(data)

        assert rp.schedule == "0 0 1 1 * 2024"

    def test_schedule_with_timezone(self):
        """Test schedule string that includes timezone info."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 9 * * * America/New_York",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Prompt",
        }
        rp = RecurringPrompt.from_dict(data)

        assert "America/New_York" in rp.schedule

    def test_render_prompt_with_falsy_runtime_vars(self):
        """Test rendering with falsy but not None runtime variables."""
        data = {
            "id": "test",
            "name": "Test",
            "description": "Test",
            "schedule": "0 * * * *",
            "trigger": "cron",
            "context": "Context",
            "prompt": "Value: {{value}}",
            "variables": {},
        }
        rp = RecurringPrompt.from_dict(data)

        # Empty dict should not cause issues
        rendered = rp.render_prompt({})
        assert rendered == "Value: {{value}}"
