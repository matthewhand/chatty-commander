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
Tests for builder module.

Tests OpenAPI schema and markdown documentation generation.
"""

import pytest

from src.chatty_commander.tools.builder import (
    build_openapi_schema,
    generate_markdown_docs,
)


class TestBuildOpenapiSchema:
    """Tests for build_openapi_schema function."""

    def test_returns_dict(self):
        """Test that function returns a dictionary."""
        result = build_openapi_schema()
        assert isinstance(result, dict)

    def test_has_openapi_version(self):
        """Test that schema has OpenAPI version."""
        result = build_openapi_schema()
        assert result["openapi"] == "3.0.3"

    def test_has_info_section(self):
        """Test that schema has info section."""
        result = build_openapi_schema()
        assert "info" in result
        assert result["info"]["title"] == "ChattyCommander API"
        assert result["info"]["version"] == "0.2.0"

    def test_has_servers(self):
        """Test that schema has servers section."""
        result = build_openapi_schema()
        assert "servers" in result
        assert len(result["servers"]) > 0
        assert result["servers"][0]["url"] == "http://localhost:8100"

    def test_has_paths(self):
        """Test that schema has paths section."""
        result = build_openapi_schema()
        assert "paths" in result
        assert len(result["paths"]) > 0

    def test_has_status_endpoint(self):
        """Test that schema includes status endpoint."""
        result = build_openapi_schema()
        assert "/api/v1/status" in result["paths"]

    def test_has_config_endpoint(self):
        """Test that schema includes config endpoint."""
        result = build_openapi_schema()
        assert "/api/v1/config" in result["paths"]

    def test_has_state_endpoint(self):
        """Test that schema includes state endpoint."""
        result = build_openapi_schema()
        assert "/api/v1/state" in result["paths"]

    def test_has_command_endpoint(self):
        """Test that schema includes command endpoint."""
        result = build_openapi_schema()
        assert "/api/v1/command" in result["paths"]

    def test_has_components(self):
        """Test that schema has components section."""
        result = build_openapi_schema()
        assert "components" in result
        assert "schemas" in result["components"]

    def test_has_license_info(self):
        """Test that schema includes license information."""
        result = build_openapi_schema()
        assert "license" in result["info"]
        assert result["info"]["license"]["name"] == "MIT"

    def test_has_contact_info(self):
        """Test that schema includes contact information."""
        result = build_openapi_schema()
        assert "contact" in result["info"]


class TestGenerateMarkdownDocs:
    """Tests for generate_markdown_docs function."""

    def test_returns_string(self):
        """Test that function returns a string."""
        result = generate_markdown_docs()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_has_title(self):
        """Test that markdown has title."""
        result = generate_markdown_docs()
        assert "# ChattyCommander API" in result

    def test_has_version(self):
        """Test that markdown includes version."""
        result = generate_markdown_docs()
        assert "0.2.0" in result

    def test_has_server_section(self):
        """Test that markdown has server section."""
        result = generate_markdown_docs()
        assert "Server" in result or "localhost:8100" in result

    def test_has_endpoints_section(self):
        """Test that markdown documents endpoints."""
        result = generate_markdown_docs()
        assert "Endpoints" in result or "endpoint" in result.lower()

    def test_has_status_documentation(self):
        """Test that markdown documents status endpoint."""
        result = generate_markdown_docs()
        assert "status" in result.lower()

    def test_has_config_documentation(self):
        """Test that markdown documents config endpoint."""
        result = generate_markdown_docs()
        assert "config" in result.lower()

    def test_has_state_documentation(self):
        """Test that markdown documents state endpoint."""
        result = generate_markdown_docs()
        assert "state" in result.lower()

    def test_has_command_documentation(self):
        """Test that markdown documents command endpoint."""
        result = generate_markdown_docs()
        assert "command" in result.lower()

    def test_has_code_examples(self):
        """Test that markdown includes code examples."""
        result = generate_markdown_docs()
        assert "```" in result or "curl" in result.lower()

    def test_has_http_methods(self):
        """Test that markdown documents HTTP methods."""
        result = generate_markdown_docs()
        # Should mention GET, POST, PUT
        assert any(method in result for method in ["GET", "POST", "PUT"])


class TestSchemaContent:
    """Tests for schema content details."""

    def test_status_endpoint_has_get_method(self):
        """Test that status endpoint supports GET."""
        schema = build_openapi_schema()
        status_path = schema["paths"]["/api/v1/status"]
        assert "get" in status_path

    def test_config_endpoint_has_get_and_put(self):
        """Test that config endpoint supports GET and PUT."""
        schema = build_openapi_schema()
        config_path = schema["paths"]["/api/v1/config"]
        assert "get" in config_path
        assert "put" in config_path

    def test_state_endpoint_has_get_and_post(self):
        """Test that state endpoint supports GET and POST."""
        schema = build_openapi_schema()
        state_path = schema["paths"]["/api/v1/state"]
        assert "get" in state_path
        assert "post" in state_path

    def test_endpoints_have_tags(self):
        """Test that endpoints are properly tagged."""
        schema = build_openapi_schema()
        for path, methods in schema["paths"].items():
            for method, details in methods.items():
                if isinstance(details, dict):
                    assert "tags" in details or "summary" in details

    def test_responses_defined(self):
        """Test that endpoints have responses defined."""
        schema = build_openapi_schema()
        status_path = schema["paths"]["/api/v1/status"]
        assert "responses" in status_path["get"]
        assert "200" in status_path["get"]["responses"]


class TestEdgeCases:
    """Edge case tests."""

    def test_openapi_schema_is_deterministic(self):
        """Test that schema generation is deterministic."""
        result1 = build_openapi_schema()
        result2 = build_openapi_schema()
        assert result1 == result2

    def test_markdown_is_deterministic(self):
        """Test that markdown generation is deterministic."""
        result1 = generate_markdown_docs()
        result2 = generate_markdown_docs()
        assert result1 == result2

    def test_schema_has_no_none_values(self):
        """Test that schema doesn't contain None values at top level."""
        result = build_openapi_schema()
        assert result["openapi"] is not None
        assert result["info"] is not None
        assert result["paths"] is not None

    def test_markdown_is_multiline(self):
        """Test that markdown has multiple lines."""
        result = generate_markdown_docs()
        lines = result.split("\n")
        assert len(lines) > 20  # Should be substantial documentation
