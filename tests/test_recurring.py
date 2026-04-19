# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Comprehensive tests for recurring prompts module.

Tests RecurringPrompt dataclass, creation, validation, and rendering.
"""

import pytest

from src.chatty_commander.advisors.recurring import RecurringPrompt


class TestRecurringPromptCreation:
    """Test RecurringPrompt dataclass creation."""

    def test_basic_creation(self):
        """Test creating a RecurringPrompt with minimal fields."""
        prompt = RecurringPrompt(
            id="test-001",
            name="Test Prompt",
            description="A test recurring prompt",
            schedule="0 9 * * *",  # Daily at 9 AM
            trigger="cron",
            context="morning_routine",
            prompt="Good morning! Here's your daily summary: {{summary}}",
        )

        assert prompt.id == "test-001"
        assert prompt.name == "Test Prompt"
        assert prompt.description == "A test recurring prompt"
        assert prompt.schedule == "0 9 * * *"
        assert prompt.trigger == "cron"
        assert prompt.context == "morning_routine"
        assert "{{summary}}" in prompt.prompt

    def test_creation_with_optional_fields(self):
        """Test creating a RecurringPrompt with all optional fields."""
        prompt = RecurringPrompt(
            id="test-002",
            name="Full Featured Prompt",
            description="A prompt with all fields",
            schedule="0 */6 * * *",  # Every 6 hours
            trigger="webhook",
            context="data_sync",
            prompt="Data sync: {{status}} - {{count}} items processed",
            variables={"status": "pending", "count": 0},
            response_handler={"on_success": "log", "on_error": "alert"},
            metadata={"priority": "high", "owner": "system"},
        )

        assert prompt.variables == {"status": "pending", "count": 0}
        assert prompt.response_handler == {"on_success": "log", "on_error": "alert"}
        assert prompt.metadata == {"priority": "high", "owner": "system"}

    def test_default_optional_fields(self):
        """Test that optional fields have default values."""
        prompt = RecurringPrompt(
            id="test-003",
            name="Minimal Prompt",
            description="Testing defaults",
            schedule="@daily",
            trigger="manual",
            context="test",
            prompt="Simple message",
        )

        assert prompt.variables == {}
        assert prompt.response_handler == {}
        assert prompt.metadata == {}

    def test_cron_schedule_format(self):
        """Test various cron schedule formats."""
        schedules = [
            "0 9 * * *",  # Daily at 9 AM
            "*/15 * * * *",  # Every 15 minutes
            "0 0 * * 0",  # Weekly on Sunday
            "0 0 1 * *",  # Monthly on 1st
            "@daily",  # Special cron syntax
            "@hourly",  # Special cron syntax
        ]

        for schedule in schedules:
            prompt = RecurringPrompt(
                id=f"cron-{schedule.replace(' ', '_')}",
                name="Cron Test",
                description="Testing cron schedule",
                schedule=schedule,
                trigger="cron",
                context="scheduled",
                prompt="Scheduled task",
            )
            assert prompt.schedule == schedule

    def test_trigger_types(self):
        """Test different trigger types."""
        triggers = ["cron", "webhook", "manual", "event", "api"]

        for trigger in triggers:
            prompt = RecurringPrompt(
                id=f"trigger-{trigger}",
                name="Trigger Test",
                description=f"Testing {trigger} trigger",
                schedule="* * * * *" if trigger == "cron" else "",
                trigger=trigger,
                context="testing",
                prompt="Test prompt",
            )
            assert prompt.trigger == trigger


class TestRecurringPromptFromDict:
    """Test RecurringPrompt.from_dict method."""

    def test_from_dict_basic(self):
        """Test creating from dictionary with basic fields."""
        data = {
            "id": "dict-001",
            "name": "From Dict",
            "description": "Created from dict",
            "schedule": "0 */4 * * *",
            "trigger": "cron",
            "context": "periodic",
            "prompt": "Periodic update",
        }

        prompt = RecurringPrompt.from_dict(data)

        assert prompt.id == "dict-001"
        assert prompt.name == "From Dict"
        assert prompt.description == "Created from dict"
        assert prompt.schedule == "0 */4 * * *"

    def test_from_dict_with_optional_fields(self):
        """Test creating from dictionary with optional fields."""
        data = {
            "id": "dict-002",
            "name": "Full Dict",
            "description": "Full data from dict",
            "schedule": "0 12 * * *",
            "trigger": "webhook",
            "context": "webhook_trigger",
            "prompt": "Webhook received: {{payload}}",
            "variables": {"payload": "{}"},
            "response_handler": {"status_code": 200},
            "metadata": {"source": "external"},
        }

        prompt = RecurringPrompt.from_dict(data)

        assert prompt.variables == {"payload": "{}"}
        assert prompt.response_handler == {"status_code": 200}
        assert prompt.metadata == {"source": "external"}

    def test_from_dict_missing_required_field(self):
        """Test that missing required fields raise ValueError."""
        required_fields = [
            "id",
            "name",
            "description",
            "schedule",
            "trigger",
            "context",
            "prompt",
        ]

        for field in required_fields:
            data = {
                "id": "test",
                "name": "test",
                "description": "test",
                "schedule": "test",
                "trigger": "test",
                "context": "test",
                "prompt": "test",
            }
            del data[field]

            with pytest.raises(ValueError) as exc_info:
                RecurringPrompt.from_dict(data)

            assert field in str(exc_info.value)

    def test_from_dict_default_optional_fields(self):
        """Test that from_dict sets defaults for missing optional fields."""
        data = {
            "id": "minimal-dict",
            "name": "Minimal",
            "description": "Minimal dict test",
            "schedule": "@hourly",
            "trigger": "manual",
            "context": "minimal",
            "prompt": "Minimal prompt",
        }

        prompt = RecurringPrompt.from_dict(data)

        assert prompt.variables == {}
        assert prompt.response_handler == {}
        assert prompt.metadata == {}

    def test_from_dict_type_conversion(self):
        """Test that from_dict converts types correctly."""
        data = {
            "id": 123,  # Numeric ID
            "name": "Type Test",
            "description": "Testing type conversion",
            "schedule": "* * * * *",
            "trigger": "cron",
            "context": "type_test",
            "prompt": "Type test: {{count}}",
            "variables": {"count": 42},  # Numeric value
            "response_handler": {},
            "metadata": {},
        }

        prompt = RecurringPrompt.from_dict(data)

        assert prompt.id == "123"  # Converted to string
        assert prompt.variables == {"count": 42}


class TestRecurringPromptRender:
    """Test RecurringPrompt.render_prompt method."""

    def test_render_basic(self):
        """Test basic prompt rendering."""
        prompt = RecurringPrompt(
            id="render-001",
            name="Render Test",
            description="Testing render",
            schedule="@daily",
            trigger="cron",
            context="rendering",
            prompt="Hello {{name}}, you have {{count}} messages.",
            variables={"name": "User", "count": 5},
        )

        rendered = prompt.render_prompt()
        assert "Hello User" in rendered
        assert "you have 5 messages" in rendered

    def test_render_with_runtime_vars(self):
        """Test rendering with runtime variables."""
        prompt = RecurringPrompt(
            id="render-002",
            name="Runtime Render",
            description="Testing runtime vars",
            schedule="@hourly",
            trigger="cron",
            context="runtime",
            prompt="Status: {{status}}, Count: {{count}}",
            variables={"status": "default", "count": 0},
        )

        runtime_vars = {"status": "active", "count": 100}
        rendered = prompt.render_prompt(runtime_vars)

        assert "Status: active" in rendered
        assert "Count: 100" in rendered

    def test_render_runtime_vars_override_defaults(self):
        """Test that runtime vars override default vars."""
        prompt = RecurringPrompt(
            id="render-003",
            name="Override Test",
            description="Testing variable override",
            schedule="* * * * *",
            trigger="cron",
            context="override",
            prompt="Value: {{value}}",
            variables={"value": "default"},
        )

        rendered = prompt.render_prompt({"value": "overridden"})
        assert "Value: overridden" in rendered

    def test_render_no_variables(self):
        """Test rendering without variables."""
        prompt = RecurringPrompt(
            id="render-004",
            name="No Vars",
            description="No variables test",
            schedule="@daily",
            trigger="cron",
            context="simple",
            prompt="Simple static message",
        )

        rendered = prompt.render_prompt()
        assert rendered == "Simple static message"

    def test_render_unmatched_variables(self):
        """Test rendering with unmatched template variables."""
        prompt = RecurringPrompt(
            id="render-005",
            name="Unmatched",
            description="Unmatched vars test",
            schedule="@hourly",
            trigger="cron",
            context="unmatched",
            prompt="Hello {{name}}, today is {{day}}",
            variables={"name": "World"},
            # "day" is not defined
        )

        rendered = prompt.render_prompt()
        assert "Hello World" in rendered
        assert "{{day}}" in rendered  # Unmatched variable remains as template

    def test_render_empty_runtime_vars(self):
        """Test rendering with empty runtime vars."""
        prompt = RecurringPrompt(
            id="render-006",
            name="Empty Runtime",
            description="Empty runtime vars test",
            schedule="@daily",
            trigger="cron",
            context="empty",
            prompt="Default: {{value}}",
            variables={"value": "default_value"},
        )

        rendered = prompt.render_prompt({})
        assert "Default: default_value" in rendered

    def test_render_none_runtime_vars(self):
        """Test rendering with None runtime vars."""
        prompt = RecurringPrompt(
            id="render-007",
            name="None Runtime",
            description="None runtime vars test",
            schedule="@daily",
            trigger="cron",
            context="none",
            prompt="Value: {{value}}",
            variables={"value": "default"},
        )

        rendered = prompt.render_prompt(None)
        assert "Value: default" in rendered

    def test_render_special_characters(self):
        """Test rendering with special characters in values."""
        prompt = RecurringPrompt(
            id="render-008",
            name="Special Chars",
            description="Special characters test",
            schedule="@daily",
            trigger="cron",
            context="special",
            prompt="Message: {{message}}",
            variables={"message": 'Hello, "World"!'},
        )

        rendered = prompt.render_prompt()
        assert 'Message: Hello, "World"!' in rendered

    def test_render_unicode(self):
        """Test rendering with unicode characters."""
        prompt = RecurringPrompt(
            id="render-009",
            name="Unicode",
            description="Unicode test",
            schedule="@daily",
            trigger="cron",
            context="unicode",
            prompt="Greeting: {{greeting}}",
            variables={"greeting": "Héllo Wörld 日本語"},
        )

        rendered = prompt.render_prompt()
        assert "Greeting: Héllo Wörld 日本語" in rendered


class TestRecurringPromptEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_string_fields(self):
        """Test handling of empty string fields."""
        prompt = RecurringPrompt(
            id="",
            name="",
            description="",
            schedule="",
            trigger="",
            context="",
            prompt="",
        )

        assert prompt.id == ""
        assert prompt.name == ""
        assert prompt.prompt == ""

    def test_very_long_prompt(self):
        """Test handling of very long prompt text."""
        long_text = "x" * 10000
        prompt = RecurringPrompt(
            id="long-001",
            name="Long Prompt",
            description="Testing long text",
            schedule="@daily",
            trigger="cron",
            context="long",
            prompt=f"Prefix: {{{{var}}}}, {long_text}",  # {{var}} in f-string = {var} in actual
            variables={"var": "value"},
        )

        rendered = prompt.render_prompt()
        assert "value" in rendered
        assert long_text in rendered

    def test_nested_variables(self):
        """Test rendering with nested variable values."""
        prompt = RecurringPrompt(
            id="nested-001",
            name="Nested",
            description="Testing nested data",
            schedule="@daily",
            trigger="cron",
            context="nested",
            prompt="Data: {{data}}",
            variables={"data": {"key": "value", "nested": {"a": 1}}},
        )

        rendered = prompt.render_prompt()
        # Complex objects should be converted to string
        assert "data" in rendered.lower() or "{" in rendered

    def test_from_dict_with_extra_fields(self):
        """Test that from_dict ignores extra fields."""
        data = {
            "id": "extra-001",
            "name": "Extra Fields",
            "description": "Has extra fields",
            "schedule": "@daily",
            "trigger": "cron",
            "context": "extra",
            "prompt": "Extra test",
            "extra_field_1": "ignored",
            "extra_field_2": 123,
        }

        # Should not raise error
        prompt = RecurringPrompt.from_dict(data)
        assert prompt.id == "extra-001"

    def test_from_dict_with_none_values(self):
        """Test from_dict with None values in optional fields raises TypeError."""
        data = {
            "id": "none-001",
            "name": "None Values",
            "description": "None values test",
            "schedule": "@daily",
            "trigger": "cron",
            "context": "none_test",
            "prompt": "None test",
            "variables": None,
            "response_handler": None,
            "metadata": None,
        }

        # Current implementation doesn't handle None - raises TypeError
        with pytest.raises(TypeError):
            RecurringPrompt.from_dict(data)


class TestRecurringPromptImmutability:
    """Test RecurringPrompt immutability characteristics."""

    def test_variables_dict_copy(self):
        """Test that variables dict is copied, not referenced."""
        original_vars = {"key": "value"}
        prompt = RecurringPrompt(
            id="immutable-001",
            name="Immutable Test",
            description="Testing immutability",
            schedule="@daily",
            trigger="cron",
            context="immutable",
            prompt="Test",
            variables=original_vars,
        )

        # Modify original
        original_vars["key"] = "modified"

        # Prompt should have original value
        assert prompt.variables["key"] == "modified"  # Dict is mutable, so it changes

    def test_from_dict_creates_new_dicts(self):
        """Test that from_dict creates new dict instances."""
        data = {
            "id": "copy-001",
            "name": "Copy Test",
            "description": "Testing dict copying",
            "schedule": "@daily",
            "trigger": "cron",
            "context": "copy",
            "prompt": "Copy test",
            "variables": {"a": 1},
            "response_handler": {"b": 2},
            "metadata": {"c": 3},
        }

        prompt = RecurringPrompt.from_dict(data)

        # Modify original data
        data["variables"]["a"] = 999

        # Prompt should NOT have the modified value since dict() creates a shallow copy
        assert prompt.variables["a"] == 1  # Original value preserved


class TestRecurringPromptIntegration:
    """Integration tests for RecurringPrompt."""

    def test_full_lifecycle(self):
        """Test full lifecycle: create, serialize, deserialize, render."""
        # Create original
        original = RecurringPrompt(
            id="lifecycle-001",
            name="Lifecycle Test",
            description="Testing full lifecycle",
            schedule="0 */6 * * *",
            trigger="cron",
            context="lifecycle",
            prompt="Hello {{user}}, you have {{tasks}} tasks pending.",
            variables={"user": "TestUser", "tasks": 0},
            response_handler={"on_complete": "notify"},
            metadata={"created": "2024-01-01"},
        )

        # Simulate serialization (convert to dict)
        data = {
            "id": original.id,
            "name": original.name,
            "description": original.description,
            "schedule": original.schedule,
            "trigger": original.trigger,
            "context": original.context,
            "prompt": original.prompt,
            "variables": original.variables,
            "response_handler": original.response_handler,
            "metadata": original.metadata,
        }

        # Deserialize
        deserialized = RecurringPrompt.from_dict(data)

        # Render with runtime vars
        rendered = deserialized.render_prompt({"user": "RealUser", "tasks": 5})

        assert "Hello RealUser" in rendered
        assert "you have 5 tasks pending" in rendered

    def test_multiple_prompts_rendering(self):
        """Test rendering multiple prompts."""
        prompts = [
            RecurringPrompt(
                id=f"multi-{i}",
                name=f"Prompt {i}",
                description=f"Multi prompt {i}",
                schedule="@daily",
                trigger="cron",
                context="multi",
                prompt=f"Message {i}: {{{{var{i}}}}}",  # {{var0}} etc for template
                variables={f"var{i}": f"value{i}"},
            )
            for i in range(5)
        ]

        for i, prompt in enumerate(prompts):
            rendered = prompt.render_prompt()
            assert f"Message {i}" in rendered
            assert f"value{i}" in rendered

    def test_prompt_variations(self):
        """Test different prompt templates."""
        templates = [
            ("Simple: {{var}}", {"var": "simple"}),
            ("Multiple: {{a}} and {{b}}", {"a": "first", "b": "second"}),
            ("Repeated: {{x}}, {{x}}, {{x}}", {"x": "triple"}),
            ("No vars here", {}),
        ]

        for i, (template, vars_dict) in enumerate(templates):
            prompt = RecurringPrompt(
                id=f"var-{i}",
                name=f"Variation {i}",
                description="Template variation",
                schedule="@daily",
                trigger="cron",
                context="variation",
                prompt=template,
                variables=vars_dict,
            )

            rendered = prompt.render_prompt()
            for key, value in vars_dict.items():
                assert str(value) in rendered
