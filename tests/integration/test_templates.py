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

"""Comprehensive tests for the template system.

Tests cover:
1. Template retrieval: Known models/personas, unknown models (fallback), unknown personas (fallback), different api_modes
2. Template rendering: All parameters provided, missing parameters, empty parameters
3. Error cases: Invalid template format, None parameters, type errors
4. Edge cases: Very long system/text inputs, Unicode content, special characters, template injection attempts
5. Template injection security: Verify user input is not executed as template code
6. Fallback behavior: Verify fallback chain works correctly
"""

import pytest

from chatty_commander.advisors.templates import (
    get_prompt_template,
    render_with_template,
)


# ==============================================================================
# Template Retrieval Tests - Known Models/Personas
# ==============================================================================


class TestTemplateRetrievalKnown:
    """Tests for retrieving templates with known models and personas."""

    def test_get_template_philosophy_advisor_completion(self):
        """Test retrieving template for philosophy_advisor with completion mode."""
        template = get_prompt_template(
            model="gpt-4", persona_name="philosophy_advisor", api_mode="completion"
        )
        assert template == "[tpl:stoic:completion] [sys] {system}\n[user] {text}"

    def test_get_template_philosophy_advisor_responses(self):
        """Test retrieving template for philosophy_advisor with responses mode."""
        template = get_prompt_template(
            model="gpt-4", persona_name="philosophy_advisor", api_mode="responses"
        )
        assert template == "[tpl:stoic:responses] [sys] {system}\n[user] {text}"

    def test_get_template_default_persona_completion(self):
        """Test retrieving template for default persona with completion mode."""
        template = get_prompt_template(
            model="gpt-4", persona_name="default", api_mode="completion"
        )
        assert template == "[tpl:default:completion] [sys] {system}\n[user] {text}"

    def test_get_template_default_persona_responses(self):
        """Test retrieving template for default persona with responses mode."""
        template = get_prompt_template(
            model="gpt-4", persona_name="default", api_mode="responses"
        )
        assert template == "[tpl:default:responses] [sys] {system}\n[user] {text}"

    def test_get_template_wildcard_model_match(self):
        """Test that wildcard model (*) matches any model for known persona."""
        template = get_prompt_template(
            model="any-random-model-name", persona_name="philosophy_advisor", api_mode="completion"
        )
        assert "[tpl:stoic:completion]" in template


# ==============================================================================
# Template Retrieval Tests - Unknown Models (Fallback)
# ==============================================================================


class TestTemplateRetrievalUnknownModels:
    """Tests for fallback behavior with unknown models."""

    def test_unknown_model_falls_back_to_wildcard(self):
        """Unknown model should fall back to wildcard template for the persona."""
        template = get_prompt_template(
            model="unknown-model-xyz", persona_name="philosophy_advisor", api_mode="completion"
        )
        # Should match philosophy_advisor|completion|*
        assert "[tpl:stoic:completion]" in template

    def test_unknown_model_default_persona(self):
        """Unknown model with default persona should work."""
        template = get_prompt_template(
            model="completely-unknown-model", persona_name="default", api_mode="completion"
        )
        assert "[tpl:default:completion]" in template

    def test_model_with_special_characters(self):
        """Model names with special characters should still fall back correctly."""
        template = get_prompt_template(
            model="gpt-4-turbo-preview@v2", persona_name="philosophy_advisor", api_mode="completion"
        )
        assert "[tpl:stoic:completion]" in template


# ==============================================================================
# Template Retrieval Tests - Unknown Personas (Fallback)
# ==============================================================================


class TestTemplateRetrievalUnknownPersonas:
    """Tests for fallback behavior with unknown personas."""

    def test_unknown_persona_falls_back_to_default(self):
        """Unknown persona should fall back to default persona template."""
        template = get_prompt_template(
            model="gpt-4", persona_name="unknown_persona_xyz", api_mode="completion"
        )
        # Should fall back to default|completion|*
        assert "[tpl:default:completion]" in template

    def test_unknown_persona_unknown_model(self):
        """Unknown persona with unknown model should fall back to default."""
        template = get_prompt_template(
            model="unknown-model", persona_name="unknown_persona", api_mode="completion"
        )
        assert "[tpl:default:completion]" in template

    def test_unknown_persona_responses_mode(self):
        """Unknown persona with responses mode should fall back correctly."""
        template = get_prompt_template(
            model="gpt-4", persona_name="unknown_persona", api_mode="responses"
        )
        assert "[tpl:default:responses]" in template


# ==============================================================================
# Template Retrieval Tests - Different API Modes
# ==============================================================================


class TestTemplateRetrievalApiModes:
    """Tests for different API modes."""

    def test_api_mode_completion(self):
        """Test completion API mode."""
        template = get_prompt_template(
            model="gpt-4", persona_name="philosophy_advisor", api_mode="completion"
        )
        assert ":completion]" in template

    def test_api_mode_responses(self):
        """Test responses API mode."""
        template = get_prompt_template(
            model="gpt-4", persona_name="philosophy_advisor", api_mode="responses"
        )
        assert ":responses]" in template

    def test_api_mode_case_insensitive_uppercase(self):
        """API mode should be case insensitive (uppercase)."""
        template = get_prompt_template(
            model="gpt-4", persona_name="philosophy_advisor", api_mode="COMPLETION"
        )
        assert ":completion]" in template

    def test_api_mode_case_insensitive_mixed_case(self):
        """API mode should be case insensitive (mixed case)."""
        template = get_prompt_template(
            model="gpt-4", persona_name="philosophy_advisor", api_mode="CoMpLeTiOn"
        )
        assert ":completion]" in template

    def test_api_mode_case_insensitive_responses(self):
        """API mode responses should be case insensitive."""
        template = get_prompt_template(
            model="gpt-4", persona_name="philosophy_advisor", api_mode="RESPONSES"
        )
        assert ":responses]" in template

    def test_unknown_api_mode_falls_back_gracefully(self):
        """Unknown API mode should still return a valid template."""
        template = get_prompt_template(
            model="gpt-4", persona_name="philosophy_advisor", api_mode="unknown_mode"
        )
        # Will fall back to ultimate fallback since unknown_mode has no template
        assert "{system}" in template
        assert "{text}" in template


# ==============================================================================
# Template Retrieval Tests - None Parameter Handling
# ==============================================================================


class TestTemplateRetrievalNoneParameters:
    """Tests for None parameter handling in get_prompt_template."""

    def test_none_persona_defaults_to_default(self):
        """None persona should default to 'default' persona."""
        template = get_prompt_template(
            model="gpt-4", persona_name=None, api_mode="completion"
        )
        assert "[tpl:default:completion]" in template

    def test_none_api_mode_defaults_to_completion(self):
        """None api_mode should default to 'completion'."""
        template = get_prompt_template(
            model="gpt-4", persona_name="philosophy_advisor", api_mode=None
        )
        assert ":completion]" in template

    def test_none_model_defaults_to_wildcard(self):
        """None model should default to wildcard '*'."""
        template = get_prompt_template(
            model=None, persona_name="philosophy_advisor", api_mode="completion"
        )
        # Should match philosophy_advisor|completion|*
        assert "[tpl:stoic:completion]" in template

    def test_all_none_parameters(self):
        """All None parameters should use defaults."""
        template = get_prompt_template(model=None, persona_name=None, api_mode=None)
        # persona=None -> default, api_mode=None -> completion
        assert "[tpl:default:completion]" in template

    def test_none_persona_none_model(self):
        """None persona and None model should work together."""
        template = get_prompt_template(
            model=None, persona_name=None, api_mode="responses"
        )
        assert "[tpl:default:responses]" in template


# ==============================================================================d
# Template Rendering Tests - Normal Cases
# ==============================================================================


class TestTemplateRendering:
    """Tests for template rendering functionality."""

    def test_render_with_all_parameters(self):
        """Test rendering with all parameters provided."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(template, system="System prompt", text="User text")
        assert result == "[sys] System prompt\n[user] User text"

    def test_render_preserves_newlines_in_system(self):
        """Test that newlines in system are preserved."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(
            template, system="Line 1\nLine 2\nLine 3", text="Query"
        )
        assert "Line 1\nLine 2\nLine 3" in result

    def test_render_preserves_newlines_in_text(self):
        """Test that newlines in text are preserved."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(
            template, system="System", text="Paragraph 1\n\nParagraph 2"
        )
        assert "Paragraph 1\n\nParagraph 2" in result

    def test_render_with_empty_system(self):
        """Test rendering with empty system parameter."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(template, system="", text="User text")
        assert result == "[sys] \n[user] User text"

    def test_render_with_empty_text(self):
        """Test rendering with empty text parameter."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(template, system="System prompt", text="")
        assert result == "[sys] System prompt\n[user] "

    def test_render_with_both_empty(self):
        """Test rendering with both parameters empty."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(template, system="", text="")
        assert result == "[sys] \n[user] "

    def test_render_preserves_template_structure(self):
        """Test that template structure is preserved after rendering."""
        template = "[tpl:stoic:completion] [sys] {system}\n[user] {text}"
        result = render_with_template(template, system="Sys", text="Txt")
        assert result.startswith("[tpl:stoic:completion]")


# ==============================================================================
# Template Rendering Tests - Type Handling
# ==============================================================================


class TestTemplateRenderingTypes:
    """Tests for type handling in template rendering."""

    def test_render_accepts_string_system(self):
        """Test that string system parameter works."""
        template = "[sys] {system}"
        result = render_with_template(template, system="string value", text="text")
        assert "string value" in result

    def test_render_accepts_string_text(self):
        """Test that string text parameter works."""
        template = "[user] {text}"
        result = render_with_template(template, system="sys", text="string value")
        assert "string value" in result


# ==============================================================================
# Error Cases - Invalid Template Format
# ==============================================================================


class TestTemplateErrors:
    """Tests for error cases in template operations."""

    def test_template_missing_system_placeholder_silently_ignores(self):
        """Template missing {system} placeholder silently ignores the extra arg.

        Python's str.format() ignores extra keyword arguments, so providing
        'system' when the template has no {system} placeholder doesn't error.
        """
        template = "[user] {text}"  # Missing {system}
        # This should NOT raise - extra kwargs are ignored
        result = render_with_template(template, system="Sys", text="Txt")
        assert result == "[user] Txt"
        assert "Sys" not in result  # system param was ignored

    def test_template_missing_text_placeholder_silently_ignores(self):
        """Template missing {text} placeholder silently ignores the extra arg.

        Python's str.format() ignores extra keyword arguments.
        """
        template = "[sys] {system}"  # Missing {text}
        # This should NOT raise - extra kwargs are ignored
        result = render_with_template(template, system="Sys", text="Txt")
        assert result == "[sys] Sys"
        assert "Txt" not in result  # text param was ignored

    def test_invalid_template_wrong_placeholder_names(self):
        """Template with wrong placeholder names should raise KeyError."""
        template = "[sys] {wrong_name}\n[user] {also_wrong}"
        with pytest.raises(KeyError):
            render_with_template(template, system="Sys", text="Txt")

    def test_invalid_template_extra_placeholders(self):
        """Template with extra placeholders should raise KeyError."""
        template = "[sys] {system}\n[user] {text}\n[extra] {extra_placeholder}"
        with pytest.raises(KeyError):
            render_with_template(template, system="Sys", text="Txt")

    def test_render_missing_system_argument(self):
        """Missing system argument should raise TypeError."""
        template = "[sys] {system}\n[user] {text}"
        with pytest.raises(TypeError):
            render_with_template(template, text="Txt")  # Missing system

    def test_render_missing_text_argument(self):
        """Missing text argument should raise TypeError."""
        template = "[sys] {system}\n[user] {text}"
        with pytest.raises(TypeError):
            render_with_template(template, system="Sys")  # Missing text

    def test_render_no_arguments(self):
        """No arguments should raise TypeError."""
        template = "[sys] {system}\n[user] {text}"
        with pytest.raises(TypeError):
            render_with_template(template)


# ==============================================================================
# Edge Cases - Very Long Inputs
# ==============================================================================


class TestEdgeCasesLongInputs:
    """Tests for edge cases with very long inputs."""

    def test_very_long_system_prompt(self):
        """Test rendering with a very long system prompt."""
        template = "[sys] {system}\n[user] {text}"
        long_system = "x" * 100000  # 100k characters
        result = render_with_template(template, system=long_system, text="Short text")
        assert len(result) > 100000
        assert long_system in result

    def test_very_long_user_text(self):
        """Test rendering with a very long user text."""
        template = "[sys] {system}\n[user] {text}"
        long_text = "y" * 100000  # 100k characters
        result = render_with_template(template, system="Short system", text=long_text)
        assert len(result) > 100000
        assert long_text in result

    def test_both_very_long(self):
        """Test rendering with both parameters very long."""
        template = "[sys] {system}\n[user] {text}"
        long_system = "a" * 50000
        long_text = "b" * 50000
        result = render_with_template(template, system=long_system, text=long_text)
        assert len(result) > 100000
        assert long_system in result
        assert long_text in result

    def test_long_model_name(self):
        """Test that very long model names don't break template retrieval."""
        long_model = "model-" + "x" * 1000
        template = get_prompt_template(
            model=long_model, persona_name="philosophy_advisor", api_mode="completion"
        )
        # Should fall back to wildcard
        assert "[tpl:stoic:completion]" in template

    def test_long_persona_name(self):
        """Test that very long persona names fall back correctly."""
        long_persona = "persona_" + "y" * 1000
        template = get_prompt_template(
            model="gpt-4", persona_name=long_persona, api_mode="completion"
        )
        # Should fall back to default
        assert "[tpl:default:completion]" in template


# ==============================================================================
# Edge Cases - Unicode Content
# ==============================================================================


class TestEdgeCasesUnicode:
    """Tests for edge cases with Unicode content."""

    def test_unicode_system_chinese(self):
        """Test rendering with Chinese characters in system."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(
            template, system="系统提示", text="Hello"
        )
        assert "系统提示" in result

    def test_unicode_text_japanese(self):
        """Test rendering with Japanese characters in text."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(
            template, system="Hello", text="ユーザーテキスト"
        )
        assert "ユーザーテキスト" in result

    def test_unicode_text_emoji(self):
        """Test rendering with emoji in text."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(
            template, system="System", text="Hello 👋 World 🌍"
        )
        assert "👋" in result
        assert "🌍" in result

    def test_unicode_system_arabic(self):
        """Test rendering with Arabic characters in system."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(
            template, system="مرحبا بالعالم", text="Hello"
        )
        assert "مرحبا بالعالم" in result

    def test_unicode_right_to_left(self):
        """Test rendering with RTL text."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(
            template, system="שלום עולם", text="مرحبا"
        )
        assert "שלום עולם" in result
        assert "مرحبا" in result

    def test_unicode_mixed_scripts(self):
        """Test rendering with mixed scripts."""
        template = "[sys] {system}\n[user] {text}"
        mixed = "Hello Мир العالم 🌍"
        result = render_with_template(template, system=mixed, text="text")
        assert "Мир" in result
        assert "العالم" in result
        assert "🌍" in result

    def test_unicode_persona_name(self):
        """Test that Unicode persona names fall back correctly."""
        template = get_prompt_template(
            model="gpt-4", persona_name="哲学顾问", api_mode="completion"
        )
        # Should fall back to default since Chinese persona doesn't exist
        assert "[tpl:default:completion]" in template

    def test_unicode_model_name(self):
        """Test that Unicode model names work with fallback."""
        template = get_prompt_template(
            model="模型-123", persona_name="philosophy_advisor", api_mode="completion"
        )
        # Should fall back to wildcard model
        assert "[tpl:stoic:completion]" in template


# ==============================================================================
# Edge Cases - Special Characters
# ==============================================================================


class TestEdgeCasesSpecialCharacters:
    """Tests for edge cases with special characters."""

    def test_special_chars_curly_braces_in_content(self):
        """Test that curly braces in content are preserved (not interpreted as placeholders)."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(
            template, system="Use {placeholder} syntax", text="Text"
        )
        # The curly braces in the content should be preserved
        assert "{placeholder}" in result

    def test_special_chars_newlines_tabs(self):
        """Test that newlines and tabs are preserved."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(
            template, system="Line1\n\tIndented", text="Tab\there"
        )
        assert "\n\t" in result
        assert "\t" in result

    def test_special_chars_backslashes(self):
        """Test that backslashes are preserved."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(
            template, system="path\\to\\file", text="\\\\double"
        )
        assert "path\\to\\file" in result

    def test_special_chars_quotes(self):
        """Test that various quotes are preserved."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(
            template, system='Single \' and double "', text='``backticks``'
        )
        assert "'" in result
        assert '"' in result
        assert "``" in result

    def test_special_chars_html_xml(self):
        """Test that HTML/XML content is preserved."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(
            template, system="<tag attr='value'>content</tag>", text="&amp; &lt; &gt;"
        )
        assert "<tag" in result
        assert "&amp;" in result

    def test_special_chars_json_like(self):
        """Test that JSON-like content is preserved."""
        template = "[sys] {system}\n[user] {text}"
        json_content = '{"key": "value", "nested": {"data": 123}}'
        result = render_with_template(template, system=json_content, text="text")
        assert '"key": "value"' in result

    def test_special_chars_dollar_sign(self):
        """Test that dollar signs are preserved."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(
            template, system="Price: $100", text="$$double"
        )
        assert "$100" in result
        assert "$$double" in result

    def test_special_chars_percent(self):
        """Test that percent signs are preserved."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(
            template, system="100% complete", text="%special%"
        )
        assert "100%" in result
        assert "%special%" in result

    def test_special_chars_at_sign(self):
        """Test that @ signs are preserved."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(
            template, system="email@example.com", text="@mention"
        )
        assert "email@example.com" in result
        assert "@mention" in result

    def test_special_chars_hash(self):
        """Test that hash signs are preserved."""
        template = "[sys] {system}\n[user] {text}"
        result = render_with_template(
            template, system="#hashtag #trending", text="## heading"
        )
        assert "#hashtag" in result
        assert "## heading" in result


# ==============================================================================
# Template Injection Security Tests
# ==============================================================================


class TestTemplateInjectionSecurity:
    """Tests for template injection security.

    These tests verify that user-supplied content is not interpreted
    as template code. The template placeholders {system} and {text}
    should be treated as literal text when passed as values.
    """

    def test_injection_attempt_system_placeholder(self):
        """Test that {system} in user text is not interpreted as placeholder."""
        template = "[sys] {system}\n[user] {text}"
        # Attempt to inject a system placeholder in the text
        result = render_with_template(
            template, system="Original system", text="{system}"
        )
        # The literal string "{system}" should appear, not "Original system"
        assert "{system}" in result
        # Should only see "Original system" once (from the actual system parameter)
        assert result.count("Original system") == 1

    def test_injection_attempt_text_placeholder(self):
        """Test that {text} in system is not interpreted as placeholder."""
        template = "[sys] {system}\n[user] {text}"
        # Attempt to inject a text placeholder in the system
        result = render_with_template(
            template, system="{text}", text="Original text"
        )
        assert "{text}" in result
        assert result.count("Original text") == 1

    def test_injection_attempt_format_spec(self):
        """Test that format specifiers in content are treated as literal text.

        When you pass "{system:!r}" as the value for the 'system' parameter,
        it should appear literally in the output (not be executed as a format spec).
        """
        template = "[sys] {system}\n[user] {text}"
        # These format specifiers passed as VALUES should appear literally
        result = render_with_template(
            template, system="{system:!r}", text="{text:>10}"
        )
        # The literal strings should appear in output (they're values, not executed)
        assert "{system:!r}" in result  # Appears literally, not interpreted
        assert "{text:>10}" in result  # Appears literally, not formatted to 10 chars

    def test_injection_attempt_nested_placeholders(self):
        """Test that nested placeholder patterns are not interpreted."""
        template = "[sys] {system}\n[user] {text}"
        # Attempt various nested patterns
        result = render_with_template(
            template,
            system="{nested {system}}",
            text="{{double_braces}}"
        )
        # The content should be preserved as-is
        assert "{nested {system}}" in result
        assert "{{double_braces}}" in result

    def test_template_code_not_executed(self):
        """Test that Python code in content is not executed."""
        template = "[sys] {system}\n[user] {text}"
        # This should be safe - Python code in string should not execute
        malicious = "{__import__('os').system('rm -rf /')}"
        result = render_with_template(template, system=malicious, text="safe")
        # The malicious string should appear literally, not execute
        assert malicious in result
        assert "safe" in result

    def test_format_string_attack(self):
        """Test that format string attacks don't work."""
        template = "[sys] {system}\n[user] {text}"
        # Attempt to access format string internals
        attack = "{system.__class__}"
        result = render_with_template(template, system=attack, text="safe")
        # Should appear literally, not resolve to <class 'str'>
        assert "{system.__class__}" in result
        assert "__class__" in result

    def test_curly_braces_in_model_persona(self):
        """Test that curly braces in model/persona names don't cause issues."""
        template = get_prompt_template(
            model="model{with}braces", persona_name="philosophy_advisor", api_mode="completion"
        )
        # Should fall back to wildcard and return a valid template
        assert "{system}" in template
        assert "{text}" in template


# ==============================================================================
# Fallback Behavior Tests
# ==============================================================================


class TestFallbackBehavior:
    """Tests for the fallback chain in get_prompt_template."""

    def test_fallback_chain_exact_to_wildcard(self):
        """Test fallback from exact match to wildcard model."""
        # unknown-model doesn't have an exact match, should fall back to *
        template = get_prompt_template(
            model="unknown-model-xyz", persona_name="philosophy_advisor", api_mode="completion"
        )
        # Should match philosophy_advisor|completion|*
        assert "[tpl:stoic:completion]" in template

    def test_fallback_chain_wildcard_to_default(self):
        """Test fallback from wildcard to default persona."""
        # unknown_persona doesn't have any template, should fall back to default
        template = get_prompt_template(
            model="gpt-4", persona_name="totally_unknown_persona", api_mode="completion"
        )
        # Should match default|completion|*
        assert "[tpl:default:completion]" in template

    def test_fallback_chain_complete_unknown(self):
        """Test complete fallback with unknown everything."""
        template = get_prompt_template(
            model="unknown-model", persona_name="unknown_persona", api_mode="unknown_mode"
        )
        # Should fall back to ultimate fallback
        assert "{system}" in template
        assert "{text}" in template

    def test_ultimate_fallback_has_correct_format(self):
        """Test that ultimate fallback template has correct format."""
        # Use a completely unknown combination to trigger ultimate fallback
        template = get_prompt_template(
            model="x", persona_name="nonexistent", api_mode="invalid_mode"
        )
        # The ultimate fallback is: "[sys] {system}\n[user] {text}"
        rendered = render_with_template(template, system="Sys", text="Txt")
        assert "[sys] Sys" in rendered
        assert "[user] Txt" in rendered

    def test_fallback_priority_exact_over_wildcard(self):
        """Test that exact match takes priority over wildcard."""
        # If an exact match key existed, it would be used over wildcard
        # Currently no exact matches exist, but the priority is in the code
        # We can verify the fallback still works
        template = get_prompt_template(
            model="any-model", persona_name="philosophy_advisor", api_mode="completion"
        )
        assert "[tpl:stoic:completion]" in template

    def test_api_mode_preserved_in_fallback(self):
        """Test that API mode is preserved when falling back."""
        # Even with unknown persona, api_mode should be preserved
        template_responses = get_prompt_template(
            model="gpt-4", persona_name="unknown_persona", api_mode="responses"
        )
        template_completion = get_prompt_template(
            model="gpt-4", persona_name="unknown_persona", api_mode="completion"
        )
        assert "responses" in template_responses
        assert "completion" in template_completion


# ==============================================================================
# Integration Tests - Full Flow
# ==============================================================================


class TestIntegrationFlow:
    """Integration tests for the complete template workflow."""

    def test_full_workflow_philosophy_advisor(self):
        """Test complete workflow with philosophy advisor."""
        # Get template
        template = get_prompt_template(
            model="gpt-4-turbo", persona_name="philosophy_advisor", api_mode="completion"
        )
        # Render with real content
        result = render_with_template(
            template,
            system="You are a stoic philosophy advisor.",
            text="How should I handle adversity?"
        )
        # Verify
        assert "[tpl:stoic:completion]" in result
        assert "stoic philosophy advisor" in result
        assert "handle adversity" in result

    def test_full_workflow_default_fallback(self):
        """Test complete workflow falling back to default."""
        # Get template with unknown persona
        template = get_prompt_template(
            model="claude-3", persona_name="unknown_role", api_mode="responses"
        )
        # Render
        result = render_with_template(
            template,
            system="You are helpful.",
            text="What is the meaning of life?"
        )
        # Verify
        assert "[tpl:default:responses]" in result
        assert "helpful" in result
        assert "meaning of life" in result

    def test_full_workflow_none_parameters(self):
        """Test complete workflow with None parameters."""
        # Get template with None parameters
        template = get_prompt_template(model=None, persona_name=None, api_mode=None)
        # Render
        result = render_with_template(
            template,
            system="Default system",
            text="Default question"
        )
        # Verify (should use defaults: default persona, completion mode)
        assert "Default system" in result
        assert "Default question" in result

    def test_rendered_output_can_be_used_as_message(self):
        """Test that rendered output is valid for use as a message."""
        template = get_prompt_template(
            model="gpt-4", persona_name="philosophy_advisor", api_mode="completion"
        )
        result = render_with_template(
            template,
            system="System prompt",
            text="User message"
        )
        # Output should be a single string
        assert isinstance(result, str)
        # Should not have unrendered placeholders
        assert "{system}" not in result
        assert "{text}" not in result
