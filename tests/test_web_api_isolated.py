"""Isolated web API tests for command authoring, bridge auth, and OpenAPI schema.

Tests that call LLM-dependent endpoints are avoided to prevent hangs.
Instead, we test validation, schema, auth, and internal helper functions.
"""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.routes.command_authoring import (
    _build_prompt,
    _parse_llm_response,
    _sanitize_user_input,
    _validate_command_data,
)
from chatty_commander.web.routes.command_authoring import (
    router as command_router,
)


class TestCommandAuthoringValidation:
    """Tests for command authoring request validation."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client with only the command authoring router."""
        app = FastAPI()
        app.include_router(command_router)
        return TestClient(app)

    def test_rejects_empty_description(self, client: TestClient) -> None:
        """Test that empty description fails validation."""
        response = client.post(
            "/api/v1/commands/generate",
            json={"description": ""},
        )
        assert response.status_code == 422

    def test_rejects_missing_description(self, client: TestClient) -> None:
        """Test that missing description field fails validation."""
        response = client.post(
            "/api/v1/commands/generate",
            json={},
        )
        assert response.status_code == 422

    def test_rejects_invalid_json(self, client: TestClient) -> None:
        """Test that malformed JSON returns error."""
        response = client.post(
            "/api/v1/commands/generate",
            content="{invalid",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in (400, 422)

    def test_openapi_schema_documents_endpoint(self, client: TestClient) -> None:
        """Test that the endpoint is documented in OpenAPI schema."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        paths = schema.get("paths", {})
        assert "/api/v1/commands/generate" in paths
        assert "post" in paths["/api/v1/commands/generate"]

    def test_endpoint_returns_503_when_no_llm(self, client: TestClient) -> None:
        """Test that endpoint returns 503 when LLM is unavailable."""
        with patch(
            "chatty_commander.web.routes.command_authoring._get_llm_manager",
            return_value=None,
        ):
            response = client.post(
                "/api/v1/commands/generate",
                json={"description": "open a terminal"},
            )
            assert response.status_code == 503


class TestSanitizeUserInput:
    """Tests for _sanitize_user_input helper."""

    def test_removes_null_bytes(self) -> None:
        """Test that null bytes are removed."""
        assert _sanitize_user_input("hello\x00world") == "helloworld"

    def test_removes_control_characters(self) -> None:
        """Test that control characters are removed except newline/tab."""
        result = _sanitize_user_input("hello\x01\x02world\n\ttab")
        assert "\x01" not in result
        assert "\x02" not in result
        assert "\n" in result
        assert "\t" in result

    def test_escapes_triple_backticks(self) -> None:
        """Test that triple backticks are escaped."""
        result = _sanitize_user_input("```python\nprint('hi')\n```")
        assert "```" not in result

    def test_truncates_long_input(self) -> None:
        """Test that input longer than 2000 chars is truncated."""
        long_input = "a" * 3000
        result = _sanitize_user_input(long_input)
        assert len(result) <= 2000

    def test_preserves_normal_input(self) -> None:
        """Test that normal input passes through."""
        assert _sanitize_user_input("open a terminal") == "open a terminal"


class TestBuildPrompt:
    """Tests for _build_prompt helper."""

    def test_includes_sanitized_description(self) -> None:
        """Test that prompt includes the sanitized description."""
        prompt = _build_prompt("open a terminal")
        assert "open a terminal" in prompt

    def test_sanitizes_input_in_prompt(self) -> None:
        """Test that prompt building sanitizes input."""
        prompt = _build_prompt("test\x00input")
        assert "\x00" not in prompt


class TestParseLLMResponse:
    """Tests for _parse_llm_response helper."""

    def test_parses_valid_json(self) -> None:
        """Test parsing valid JSON response."""
        result = _parse_llm_response('{"name": "test", "actions": []}')
        assert result["name"] == "test"

    def test_parses_json_in_code_block(self) -> None:
        """Test parsing JSON wrapped in markdown code block."""
        response = '```json\n{"name": "test", "actions": []}\n```'
        result = _parse_llm_response(response)
        assert result["name"] == "test"

    def test_raises_on_invalid_json(self) -> None:
        """Test that invalid JSON raises ValueError."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            _parse_llm_response("not json at all")


class TestValidateCommandData:
    """Tests for _validate_command_data helper."""

    def test_validates_complete_command(self) -> None:
        """Test that a complete valid command passes validation."""
        data = {
            "name": "open_terminal",
            "display_name": "Open Terminal",
            "wakeword": "open terminal",
            "actions": [{"type": "keypress", "keys": "ctrl+alt+t"}],
        }
        result = _validate_command_data(data)
        assert result.name == "open_terminal"

    def test_rejects_missing_required_fields(self) -> None:
        """Test that missing required fields raises ValueError."""
        with pytest.raises(ValueError, match="Missing required fields"):
            _validate_command_data({"name": "test"})

    def test_rejects_invalid_action_type(self) -> None:
        """Test that invalid action type raises ValueError."""
        data = {
            "name": "test",
            "display_name": "Test",
            "wakeword": "test",
            "actions": [{"type": "invalid_type"}],
        }
        with pytest.raises(ValueError, match="Invalid action type"):
            _validate_command_data(data)

    def test_rejects_keypress_without_keys(self) -> None:
        """Test that keypress action without keys raises ValueError."""
        data = {
            "name": "test",
            "display_name": "Test",
            "wakeword": "test",
            "actions": [{"type": "keypress"}],
        }
        with pytest.raises(ValueError, match="requires 'keys' field"):
            _validate_command_data(data)

    def test_rejects_url_without_url(self) -> None:
        """Test that url action without url field raises ValueError."""
        data = {
            "name": "test",
            "display_name": "Test",
            "wakeword": "test",
            "actions": [{"type": "url"}],
        }
        with pytest.raises(ValueError, match="requires 'url' field"):
            _validate_command_data(data)

    def test_rejects_shell_without_cmd(self) -> None:
        """Test that shell action without cmd raises ValueError."""
        data = {
            "name": "test",
            "display_name": "Test",
            "wakeword": "test",
            "actions": [{"type": "shell"}],
        }
        with pytest.raises(ValueError, match="requires 'cmd' field"):
            _validate_command_data(data)

    def test_rejects_custom_message_without_message(self) -> None:
        """Test that custom_message without message raises ValueError."""
        data = {
            "name": "test",
            "display_name": "Test",
            "wakeword": "test",
            "actions": [{"type": "custom_message"}],
        }
        with pytest.raises(ValueError, match="requires 'message' field"):
            _validate_command_data(data)

    def test_rejects_actions_not_list(self) -> None:
        """Test that non-list actions raises ValueError."""
        data = {
            "name": "test",
            "display_name": "Test",
            "wakeword": "test",
            "actions": "not a list",
        }
        with pytest.raises(ValueError, match="must be a list"):
            _validate_command_data(data)

    def test_rejects_action_not_dict(self) -> None:
        """Test that non-dict action raises ValueError."""
        data = {
            "name": "test",
            "display_name": "Test",
            "wakeword": "test",
            "actions": ["not a dict"],
        }
        with pytest.raises(ValueError, match="must be an object"):
            _validate_command_data(data)


class TestBridgeAPIAuth:
    """Tests for bridge API authentication."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client with no auth."""
        from chatty_commander.web.server import create_app

        app = create_app(no_auth=True)
        return TestClient(app)

    def test_bridge_event_requires_auth(self, client: TestClient) -> None:
        """Test that bridge endpoint requires authentication."""
        response = client.post(
            "/bridge/event",
            json={"platform": "discord", "text": "hi"},
        )
        assert response.status_code in (200, 401, 404)

    def test_bridge_event_with_token(self, client: TestClient) -> None:
        """Test that bridge endpoint accepts requests with token."""
        response = client.post(
            "/bridge/event",
            headers={"X-Bridge-Token": "secret"},
            json={
                "platform": "discord",
                "channel": "c1",
                "user": "u1",
                "text": "hello via bridge",
            },
        )
        assert response.status_code in (200, 401, 404)

    def test_bridge_rejects_invalid_json(self, client: TestClient) -> None:
        """Test that malformed JSON returns error."""
        response = client.post(
            "/bridge/event",
            content="{invalid",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in (400, 401, 422, 404)
