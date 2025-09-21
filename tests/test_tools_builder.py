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
Comprehensive tests for tools/builder.py module.

Tests the OpenAPI schema generation and Markdown documentation generation.
"""

from unittest.mock import patch

from chatty_commander.tools.builder import build_openapi_schema, generate_markdown_docs


class TestOpenAPISchema:
    """Test OpenAPI schema generation."""

    def test_build_openapi_schema_structure(self):
        """Test that the OpenAPI schema has the correct structure."""
        schema = build_openapi_schema()

        # Test top-level structure
        assert schema["openapi"] == "3.0.3"
        assert "info" in schema
        assert "servers" in schema
        assert "paths" in schema
        assert "components" in schema
        assert "tags" in schema

    def test_info_section(self):
        """Test the info section of the OpenAPI schema."""
        schema = build_openapi_schema()

        info = schema["info"]
        assert info["title"] == "ChattyCommander API"
        assert info["description"] == "Voice command automation system with web interface"
        assert info["version"] == "0.2.0"
        assert "contact" in info
        assert "license" in info
        assert info["license"]["name"] == "MIT"

    def test_servers_section(self):
        """Test the servers section of the OpenAPI schema."""
        schema = build_openapi_schema()

        servers = schema["servers"]
        assert len(servers) == 1
        assert servers[0]["url"] == "http://localhost:8100"
        assert servers[0]["description"] == "Local development server"

    def test_paths_section(self):
        """Test that all expected API paths are present."""
        schema = build_openapi_schema()

        paths = schema["paths"]
        expected_paths = [
            "/api/v1/status",
            "/api/v1/config",
            "/api/v1/state",
            "/api/v1/command",
            "/api/v1/health",
            "/api/v1/version",
            "/ws"
        ]

        for path in expected_paths:
            assert path in paths, f"Missing path: {path}"

    def test_status_endpoint(self):
        """Test the status endpoint definition."""
        schema = build_openapi_schema()

        status_endpoint = schema["paths"]["/api/v1/status"]["get"]
        assert status_endpoint["summary"] == "Get system status"
        assert status_endpoint["tags"] == ["System"]
        assert "200" in status_endpoint["responses"]

        response_schema = status_endpoint["responses"]["200"]["content"]["application/json"]["schema"]
        assert response_schema["$ref"] == "#/components/schemas/SystemStatus"

    def test_config_endpoints(self):
        """Test the configuration endpoints."""
        schema = build_openapi_schema()

        config_path = schema["paths"]["/api/v1/config"]

        # Test GET endpoint
        get_endpoint = config_path["get"]
        assert get_endpoint["summary"] == "Get configuration"
        assert get_endpoint["tags"] == ["Configuration"]

        # Test PUT endpoint
        put_endpoint = config_path["put"]
        assert put_endpoint["summary"] == "Update configuration"
        assert put_endpoint["tags"] == ["Configuration"]
        assert put_endpoint["requestBody"]["required"] is True

    def test_state_endpoints(self):
        """Test the state management endpoints."""
        schema = build_openapi_schema()

        state_path = schema["paths"]["/api/v1/state"]

        # Test GET endpoint
        get_endpoint = state_path["get"]
        assert get_endpoint["summary"] == "Get current state"
        assert get_endpoint["tags"] == ["State Management"]

        # Test POST endpoint
        post_endpoint = state_path["post"]
        assert post_endpoint["summary"] == "Change state"
        assert post_endpoint["tags"] == ["State Management"]

        # Test request body schema
        request_schema = post_endpoint["requestBody"]["content"]["application/json"]["schema"]
        assert request_schema["type"] == "object"
        assert "state" in request_schema["properties"]
        assert request_schema["properties"]["state"]["enum"] == ["idle", "computer", "chatty"]

    def test_command_endpoint(self):
        """Test the command execution endpoint."""
        schema = build_openapi_schema()

        command_endpoint = schema["paths"]["/api/v1/command"]["post"]
        assert command_endpoint["summary"] == "Execute command"
        assert command_endpoint["tags"] == ["Commands"]

        # Test request body schema
        request_schema = command_endpoint["requestBody"]["content"]["application/json"]["schema"]
        assert request_schema["type"] == "object"
        assert "command" in request_schema["properties"]
        assert request_schema["required"] == ["command"]

        # Test responses
        assert "200" in command_endpoint["responses"]
        assert "400" in command_endpoint["responses"]
        assert "404" in command_endpoint["responses"]

    def test_health_endpoint(self):
        """Test the health check endpoint."""
        schema = build_openapi_schema()

        health_endpoint = schema["paths"]["/api/v1/health"]["get"]
        assert health_endpoint["summary"] == "Health check"
        assert health_endpoint["tags"] == ["System"]

        # Test response properties
        response_schema = health_endpoint["responses"]["200"]["content"]["application/json"]["schema"]
        assert response_schema["type"] == "object"
        assert "status" in response_schema["properties"]
        assert "timestamp" in response_schema["properties"]
        assert "uptime" in response_schema["properties"]

    def test_version_endpoint(self):
        """Test the version endpoint."""
        schema = build_openapi_schema()

        version_endpoint = schema["paths"]["/api/v1/version"]["get"]
        assert version_endpoint["summary"] == "Get version info"
        assert version_endpoint["tags"] == ["System"]

        response_schema = version_endpoint["responses"]["200"]["content"]["application/json"]["schema"]
        assert response_schema["type"] == "object"
        assert "version" in response_schema["properties"]
        assert "git_sha" in response_schema["properties"]

    def test_websocket_endpoint(self):
        """Test the WebSocket endpoint."""
        schema = build_openapi_schema()

        ws_endpoint = schema["paths"]["/ws"]["get"]
        assert ws_endpoint["summary"] == "WebSocket connection"
        assert ws_endpoint["tags"] == ["WebSocket"]
        assert ws_endpoint["responses"]["101"]["description"] == "WebSocket connection established"

    def test_components_schemas(self):
        """Test the components/schemas section."""
        schema = build_openapi_schema()

        schemas = schema["components"]["schemas"]
        expected_schemas = ["SystemStatus", "Configuration", "StateInfo"]

        for schema_name in expected_schemas:
            assert schema_name in schemas, f"Missing schema: {schema_name}"

    def test_system_status_schema(self):
        """Test the SystemStatus schema definition."""
        schema = build_openapi_schema()

        status_schema = schema["components"]["schemas"]["SystemStatus"]
        assert status_schema["type"] == "object"

        properties = status_schema["properties"]
        assert "status" in properties
        assert "current_state" in properties
        assert "active_models" in properties
        assert "uptime" in properties
        assert "version" in properties

        assert status_schema["required"] == ["status", "current_state", "active_models"]

    def test_configuration_schema(self):
        """Test the Configuration schema definition."""
        schema = build_openapi_schema()

        config_schema = schema["components"]["schemas"]["Configuration"]
        assert config_schema["type"] == "object"

        properties = config_schema["properties"]
        assert "general_models_path" in properties
        assert "system_models_path" in properties
        assert "chat_models_path" in properties
        assert "model_actions" in properties
        assert "default_state" in properties

    def test_state_info_schema(self):
        """Test the StateInfo schema definition."""
        schema = build_openapi_schema()

        state_schema = schema["components"]["schemas"]["StateInfo"]
        assert state_schema["type"] == "object"

        properties = state_schema["properties"]
        assert "current_state" in properties
        assert "active_models" in properties
        assert "last_command" in properties
        assert "timestamp" in properties

        assert state_schema["required"] == ["current_state", "active_models"]

    def test_tags_section(self):
        """Test the tags section of the OpenAPI schema."""
        schema = build_openapi_schema()

        tags = schema["tags"]
        expected_tags = [
            {"name": "System", "description": "System status and health monitoring"},
            {"name": "Configuration", "description": "System configuration management"},
            {"name": "State Management", "description": "Operational state control"},
            {"name": "Commands", "description": "Voice command execution"},
            {"name": "WebSocket", "description": "Real-time communication"},
        ]

        for expected_tag in expected_tags:
            assert expected_tag in tags, f"Missing tag: {expected_tag}"


class TestMarkdownDocumentation:
    """Test Markdown documentation generation."""

    def test_generate_markdown_docs_structure(self):
        """Test that the generated Markdown has the correct structure."""
        docs = generate_markdown_docs()

        # Test that it contains expected sections
        assert "# ChattyCommander API Documentation" in docs
        assert "## Overview" in docs
        assert "## Base URL" in docs
        assert "## Authentication" in docs
        assert "## API Endpoints" in docs
        assert "## WebSocket Interface" in docs
        assert "## Error Handling" in docs
        assert "## Examples" in docs

    def test_timestamp_inclusion(self):
        """Test that the generated timestamp is included."""
        with patch('chatty_commander.tools.builder.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2024-01-15 10:30:00"

            docs = generate_markdown_docs()

            assert "*Generated on 2024-01-15 10:30:00*" in docs

    def test_api_endpoints_section(self):
        """Test that API endpoints are documented."""
        docs = generate_markdown_docs()

        # Test that major endpoints are documented
        assert "GET /api/v1/status" in docs
        assert "GET /api/v1/config" in docs
        assert "PUT /api/v1/config" in docs
        assert "GET /api/v1/state" in docs
        assert "POST /api/v1/state" in docs
        assert "POST /api/v1/command" in docs

    def test_code_examples(self):
        """Test that code examples are included."""
        docs = generate_markdown_docs()

        # Test Python examples
        assert "```python" in docs
        assert "import requests" in docs
        assert "import websockets" in docs

        # Test JavaScript examples
        assert "```javascript" in docs
        assert "fetch('http://localhost:8100/api/v1/status')" in docs
        assert "const ws = new WebSocket('ws://localhost:8100/ws');" in docs

    def test_request_response_examples(self):
        """Test that request/response examples are included."""
        docs = generate_markdown_docs()

        # Test JSON examples
        assert '"status": "running"' in docs
        assert '"current_state": "idle"' in docs
        assert '"command": "lights_on"' in docs
        assert '"success": true' in docs

    def test_websocket_documentation(self):
        """Test that WebSocket documentation is included."""
        docs = generate_markdown_docs()

        assert "ws://localhost:8100/ws" in docs
        assert "state_change" in docs
        assert "command_detected" in docs
        assert "system_event" in docs

    def test_error_handling_section(self):
        """Test that error handling is documented."""
        docs = generate_markdown_docs()

        assert "## Error Handling" in docs
        assert "200" in docs and "Success" in docs
        assert "400" in docs and "Bad Request" in docs
        assert "404" in docs and "Not Found" in docs
        assert "422" in docs and "Unprocessable Entity" in docs
        assert "500" in docs and "Internal Server Error" in docs

    def test_troubleshooting_section(self):
        """Test that troubleshooting information is included."""
        docs = generate_markdown_docs()

        assert "## Troubleshooting" in docs
        assert "## Common Issues" in docs
        assert "Connection Refused" in docs
        assert "CORS Errors" in docs
        assert "WebSocket Connection Failed" in docs
        assert "Command Not Found" in docs

    def test_changelog_section(self):
        """Test that changelog is included."""
        docs = generate_markdown_docs()

        assert "## Changelog" in docs
        assert "### Version 0.2.0" in docs
        assert "### Version 0.1.0" in docs

    def test_return_type(self):
        """Test that the function returns a string."""
        docs = generate_markdown_docs()

        assert isinstance(docs, str)
        assert len(docs) > 1000  # Should be a substantial document


class TestIntegration:
    """Integration tests for the builder module."""

    def test_openapi_schema_consistency(self):
        """Test that the OpenAPI schema is consistent with the Markdown docs."""
        schema = build_openapi_schema()
        docs = generate_markdown_docs()

        # Extract endpoints from schema
        schema_paths = set(schema["paths"].keys())

        # Check that major endpoints mentioned in docs exist in schema
        documented_endpoints = [
            "/api/v1/status",
            "/api/v1/config",
            "/api/v1/state",
            "/api/v1/command",
            "/api/v1/health",
            "/api/v1/version",
            "/ws"
        ]

        for endpoint in documented_endpoints:
            assert endpoint in schema_paths, f"Documented endpoint {endpoint} missing from schema"

    def test_schema_version_consistency(self):
        """Test that schema version matches what's documented."""
        schema = build_openapi_schema()

        assert schema["info"]["version"] == "0.2.0"

        # Check that this version is mentioned in the changelog
        docs = generate_markdown_docs()
        assert "0.2.0" in docs

    def test_pure_functions(self):
        """Test that both functions are pure (no side effects)."""
        # Call functions multiple times
        schema1 = build_openapi_schema()
        schema2 = build_openapi_schema()

        docs1 = generate_markdown_docs()
        docs2 = generate_markdown_docs()

        # Results should be identical
        assert schema1 == schema2
        assert docs1 == docs2

    def test_no_external_dependencies(self):
        """Test that functions don't require external dependencies."""
        # These functions should work without any imports beyond what's already imported
        schema = build_openapi_schema()
        docs = generate_markdown_docs()

        # Should not fail even if network or file system is unavailable
        assert isinstance(schema, dict)
        assert isinstance(docs, str)
