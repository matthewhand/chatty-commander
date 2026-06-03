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

"""Tests for agents routes module."""

import pytest

from src.chatty_commander.web.routes.agents import (
    AgentBlueprint,
    AgentBlueprintModel,
    AgentBlueprintResponse,
    _extract_json_from_response,
)


class TestAgentBlueprint:
    """Tests for AgentBlueprint dataclass."""

    def test_basic_creation(self):
        """Test basic blueprint creation."""
        blueprint = AgentBlueprint(
            id="test-123",
            name="Test Agent",
            description="A test agent",
            persona_prompt="You are a test agent.",
        )
        assert blueprint.id == "test-123"
        assert blueprint.name == "Test Agent"
        assert blueprint.description == "A test agent"
        assert blueprint.persona_prompt == "You are a test agent."
        assert blueprint.capabilities == []
        assert blueprint.team_role is None
        assert blueprint.handoff_triggers == []

    def test_full_creation(self):
        """Test blueprint with all fields."""
        blueprint = AgentBlueprint(
            id="agent-456",
            name="Full Agent",
            description="Complete agent",
            persona_prompt="You are complete.",
            capabilities=["speak", "listen"],
            team_role="assistant",
            handoff_triggers=["help", "transfer"],
        )
        assert blueprint.capabilities == ["speak", "listen"]
        assert blueprint.team_role == "assistant"
        assert blueprint.handoff_triggers == ["help", "transfer"]


class TestAgentBlueprintModel:
    """Tests for AgentBlueprintModel pydantic model."""

    def test_valid_creation(self):
        """Test valid model creation."""
        model = AgentBlueprintModel(
            name="Test Agent",
            description="A test agent",
            persona_prompt="You are a test agent.",
        )
        assert model.name == "Test Agent"

    def test_name_max_length(self):
        """Test name maximum length validation."""
        with pytest.raises(ValueError):
            AgentBlueprintModel(
                name="x" * 201,
                description="Test",
                persona_prompt="Test prompt.",
            )

    def test_description_max_length(self):
        """Test description maximum length validation."""
        with pytest.raises(ValueError):
            AgentBlueprintModel(
                name="Test",
                description="x" * 2001,
                persona_prompt="Test prompt.",
            )

    def test_persona_max_length(self):
        """Test persona prompt maximum length validation."""
        with pytest.raises(ValueError):
            AgentBlueprintModel(
                name="Test",
                description="Test desc",
                persona_prompt="x" * 10001,
            )

    def test_capabilities_max_length(self):
        """Test capabilities maximum length validation."""
        with pytest.raises(ValueError):
            AgentBlueprintModel(
                name="Test",
                description="Test",
                persona_prompt="Test",
                capabilities=["cap"] * 51,
            )

    def test_team_role_max_length(self):
        """Test team_role maximum length validation."""
        with pytest.raises(ValueError):
            AgentBlueprintModel(
                name="Test",
                description="Test",
                persona_prompt="Test",
                team_role="x" * 201,
            )


class TestAgentBlueprintResponse:
    """Tests for AgentBlueprintResponse model."""

    def test_response_with_id(self):
        """Test response model with ID."""
        response = AgentBlueprintResponse(
            id="agent-789",
            name="Response Agent",
            description="A response agent",
            persona_prompt="You respond.",
        )
        assert response.id == "agent-789"


class TestExtractJsonFromResponse:
    """Tests for _extract_json_from_response function."""

    def test_plain_json(self):
        """Test extracting plain JSON."""
        json_str = '{"key": "value"}'
        result = _extract_json_from_response(json_str)
        assert result == '{"key": "value"}'

    def test_json_in_code_block(self):
        """Test extracting JSON from markdown code block."""
        response = '```json\n{"key": "value"}\n```'
        result = _extract_json_from_response(response)
        assert result == '{"key": "value"}'

    def test_json_in_generic_code_block(self):
        """Test extracting JSON from generic code block."""
        response = '```\n{"key": "value"}\n```'
        result = _extract_json_from_response(response)
        assert result == '{"key": "value"}'

    def test_strips_whitespace(self):
        """Test that whitespace is stripped."""
        response = '   {"key": "value"}   '
        result = _extract_json_from_response(response)
        assert result == '{"key": "value"}'

    def test_empty_response(self):
        """Test empty response handling."""
        result = _extract_json_from_response("")
        assert result == ""

    def test_no_code_block(self):
        """Test response without code block."""
        response = "Just text without JSON"
        result = _extract_json_from_response(response)
        assert result == "Just text without JSON"
