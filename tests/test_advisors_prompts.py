"""Comprehensive tests for advisors prompt templates, persona resolution, and recurring prompts."""

import pytest

from chatty_commander.advisors.prompting import (
    Persona,
    build_prompt,
    build_provider_prompt,
    resolve_persona,
)
from chatty_commander.advisors.recurring import RecurringPrompt
from chatty_commander.advisors.templates import (
    get_prompt_template,
    render_with_template,
)


class TestPersona:
    """Tests for Persona dataclass."""

    def test_persona_creation(self) -> None:
        """Test basic Persona creation."""
        persona = Persona(name="test", system="You are a test assistant.")
        assert persona.name == "test"
        assert persona.system == "You are a test assistant."

    def test_persona_is_frozen_like(self) -> None:
        """Test Persona behaves as expected (dataclass)."""
        persona = Persona(name="p", system="s")
        # Dataclasses are mutable by default, but we can verify structure
        assert hasattr(persona, "name")
        assert hasattr(persona, "system")


class TestResolvePersona:
    """Tests for resolve_persona function."""

    def test_default_persona(self) -> None:
        """Test resolving the default persona."""
        persona = resolve_persona("default")
        assert persona.name == "default"
        assert persona.system == "Provide helpful, concise answers."

    def test_none_name_returns_default(self) -> None:
        """Test that None name returns default persona."""
        persona = resolve_persona(None)
        assert persona.name == "default"

    def test_known_persona_from_defaults(self) -> None:
        """Test resolving a known persona from DEFAULT_PERSONAS."""
        persona = resolve_persona("philosophy_advisor")
        assert persona.name == "philosophy_advisor"
        assert "Stoic" in persona.system

    def test_unknown_persona_falls_back(self) -> None:
        """Test that unknown persona falls back to default system."""
        persona = resolve_persona("unknown_persona")
        assert persona.name == "unknown_persona"
        assert persona.system == "Provide helpful, concise answers."

    def test_persona_from_config(self) -> None:
        """Test resolving persona from provided config."""
        custom = {"custom_bot": "You are a friendly helper."}
        persona = resolve_persona("custom_bot", personas_cfg=custom)
        assert persona.name == "custom_bot"
        assert persona.system == "You are a friendly helper."

    def test_empty_string_name_returns_default(self) -> None:
        """Test that empty string name returns default persona."""
        persona = resolve_persona("")
        assert persona.name == "default"


class TestBuildPrompt:
    """Tests for build_prompt function."""

    def test_build_prompt_format(self) -> None:
        """Test that build_prompt creates correct envelope."""
        persona = Persona(name="advisor", system="Be helpful.")
        result = build_prompt(persona, "What is the weather?")
        assert "[system:advisor]" in result
        assert "Be helpful." in result
        assert "[user] What is the weather?" in result

    def test_build_prompt_empty_text(self) -> None:
        """Test build_prompt with empty user text."""
        persona = Persona(name="p", system="s")
        result = build_prompt(persona, "")
        assert "[user] " in result

    def test_build_prompt_multiline_text(self) -> None:
        """Test build_prompt with multiline user text."""
        persona = Persona(name="p", system="s")
        result = build_prompt(persona, "Line 1\nLine 2\nLine 3")
        assert "Line 1\nLine 2\nLine 3" in result


class TestBuildProviderPrompt:
    """Tests for build_provider_prompt function."""

    def test_completion_mode(self) -> None:
        """Test completion mode envelope."""
        persona = Persona(name="p", system="s")
        result = build_provider_prompt("completion", persona, "test")
        assert result.startswith("[mode:completion]")

    def test_responses_mode(self) -> None:
        """Test responses mode envelope."""
        persona = Persona(name="p", system="s")
        result = build_provider_prompt("responses", persona, "test")
        assert result.startswith("[mode:responses]")

    def test_mode_case_insensitive(self) -> None:
        """Test that api_mode is case insensitive."""
        persona = Persona(name="p", system="s")
        upper = build_provider_prompt("RESPONSES", persona, "test")
        lower = build_provider_prompt("responses", persona, "test")
        assert upper.startswith("[mode:responses]")
        assert lower.startswith("[mode:responses]")

    def test_contains_base_prompt(self) -> None:
        """Test that provider prompt contains base prompt."""
        persona = Persona(name="test_name", system="test_system")
        result = build_provider_prompt("completion", persona, "user_input")
        assert "[system:test_name]" in result
        assert "test_system" in result
        assert "[user] user_input" in result


class TestGetPromptTemplate:
    """Tests for get_prompt_template function."""

    def test_exact_match(self) -> None:
        """Test exact key match."""
        # The templates dict should have some entries
        template = get_prompt_template(
            model="*",
            persona_name="philosophy_advisor",
            api_mode="completion"
        )
        assert "[tpl:stoic:completion]" in template

    def test_wildcard_fallback(self) -> None:
        """Test wildcard fallback for unknown model."""
        template = get_prompt_template(
            model="unknown-model-xyz",
            persona_name="philosophy_advisor",
            api_mode="completion"
        )
        # Should fall back to wildcard match
        assert "[tpl:" in template

    def test_default_fallback(self) -> None:
        """Test default fallback for unknown persona."""
        template = get_prompt_template(
            model="x",
            persona_name="unknown_persona",
            api_mode="completion"
        )
        assert "[tpl:default:completion]" in template

    def test_none_values_handled(self) -> None:
        """Test that None values are handled gracefully."""
        template = get_prompt_template(
            model=None,
            persona_name=None,
            api_mode=None
        )
        # Should not raise, returns something
        assert isinstance(template, str)


class TestRenderWithTemplate:
    """Tests for render_with_template function."""

    def test_basic_render(self) -> None:
        """Test basic template rendering."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(template, system="S", text="T")
        assert result == "[sys] S\n[user] T"

    def test_render_with_special_chars(self) -> None:
        """Test rendering with special characters."""
        template = "{system}: {text}"
        result = render_with_template(
            template,
            system="Hello 'world'",
            text='Test "quotes"'
        )
        assert "Hello 'world'" in result
        assert 'Test "quotes"' in result

    def test_render_with_newlines(self) -> None:
        """Test rendering with newlines in content."""
        template = "{system}\n{text}"
        result = render_with_template(
            template,
            system="Line 1\nLine 2",
            text="User\nText"
        )
        assert result == "Line 1\nLine 2\nUser\nText"


class TestRecurringPrompt:
    """Tests for RecurringPrompt dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating RecurringPrompt from minimal dict."""
        data = {
            "id": "test-id",
            "name": "Test Prompt",
            "description": "A test prompt",
            "schedule": "0 9 * * *",
            "trigger": "cron",
            "context": "You are helpful.",
            "prompt": "Hello {{name}}",
        }
        rp = RecurringPrompt.from_dict(data)
        assert rp.id == "test-id"
        assert rp.name == "Test Prompt"
        assert rp.schedule == "0 9 * * *"
        assert rp.trigger == "cron"

    def test_from_dict_missing_required_field(self) -> None:
        """Test that missing required field raises ValueError."""
        data = {
            "id": "test",
            "name": "Test",
            # missing description, schedule, trigger, context, prompt
        }
        with pytest.raises(ValueError, match="Missing required field"):
            RecurringPrompt.from_dict(data)

    def test_from_dict_with_all_fields(self) -> None:
        """Test creating RecurringPrompt with all optional fields."""
        data = {
            "id": "full-test",
            "name": "Full Test",
            "description": "Complete test",
            "schedule": "0 0 * * *",
            "trigger": "manual",
            "context": "Context here",
            "prompt": "Prompt {{var}}",
            "variables": {"var": "default"},
            "response_handler": {"type": "post"},
            "metadata": {"owner": "test"},
        }
        rp = RecurringPrompt.from_dict(data)
        assert rp.variables == {"var": "default"}
        assert rp.response_handler == {"type": "post"}
        assert rp.metadata == {"owner": "test"}

    def test_render_prompt_basic(self) -> None:
        """Test basic prompt rendering."""
        rp = RecurringPrompt(
            id="test",
            name="Test",
            description="Test",
            schedule="* * * * *",
            trigger="manual",
            context="Context",
            prompt="Hello {{name}}, you are {{role}}",
            variables={"name": "Alice", "role": "admin"},
        )
        result = rp.render_prompt()
        assert result == "Hello Alice, you are admin"

    def test_render_prompt_runtime_override(self) -> None:
        """Test runtime variables override defaults."""
        rp = RecurringPrompt(
            id="test",
            name="Test",
            description="Test",
            schedule="* * * * *",
            trigger="manual",
            context="Context",
            prompt="Hello {{name}}",
            variables={"name": "Default"},
        )
        result = rp.render_prompt({"name": "Runtime"})
        assert "Runtime" in result

    def test_render_prompt_no_variables(self) -> None:
        """Test prompt with no variables."""
        rp = RecurringPrompt(
            id="test",
            name="Test",
            description="Test",
            schedule="* * * * *",
            trigger="manual",
            context="Context",
            prompt="Hello World",
        )
        result = rp.render_prompt()
        assert result == "Hello World"

    def test_render_prompt_missing_var_unchanged(self) -> None:
        """Test that missing variables remain as placeholders."""
        rp = RecurringPrompt(
            id="test",
            name="Test",
            description="Test",
            schedule="* * * * *",
            trigger="manual",
            context="Context",
            prompt="Hello {{unknown}}",
            variables={},
        )
        result = rp.render_prompt()
        assert "{{unknown}}" in result
