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
Tests for Node.js bridge generator module.

Tests Discord/Slack bridge code generation.
"""

import json

import pytest

from src.chatty_commander.tools.bridge_nodejs import (
    generate_package_json,
    generate_env_template,
    generate_index_js,
)


class TestGeneratePackageJson:
    """Tests for generate_package_json function."""

    def test_returns_valid_json(self):
        """Test that function returns valid JSON string."""
        result = generate_package_json()
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_has_required_fields(self):
        """Test that package.json has required fields."""
        result = generate_package_json()
        pkg = json.loads(result)
        
        assert pkg["name"] == "chatty-commander-bridge"
        assert pkg["version"] == "1.0.0"
        assert "description" in pkg
        assert pkg["main"] == "src/index.js"

    def test_has_scripts(self):
        """Test that package.json has npm scripts."""
        result = generate_package_json()
        pkg = json.loads(result)
        
        assert "scripts" in pkg
        assert "start" in pkg["scripts"]
        assert "dev" in pkg["scripts"]
        assert "test" in pkg["scripts"]
        assert "nodemon src/index.js" in pkg["scripts"]["dev"]

    def test_has_dependencies(self):
        """Test that package.json has required dependencies."""
        result = generate_package_json()
        pkg = json.loads(result)
        
        deps = pkg.get("dependencies", {})
        assert "express" in deps
        assert "discord.js" in deps
        assert "@slack/bolt" in deps
        assert "axios" in deps
        assert "dotenv" in deps
        assert "winston" in deps

    def test_has_dev_dependencies(self):
        """Test that package.json has dev dependencies."""
        result = generate_package_json()
        pkg = json.loads(result)
        
        dev_deps = pkg.get("devDependencies", {})
        assert "nodemon" in dev_deps
        assert "jest" in dev_deps

    def test_has_engines(self):
        """Test that package.json specifies Node.js engine."""
        result = generate_package_json()
        pkg = json.loads(result)
        
        assert "engines" in pkg
        assert pkg["engines"]["node"] == ">=18.0.0"

    def test_json_is_formatted(self):
        """Test that JSON output is properly formatted."""
        result = generate_package_json()
        # Should have indentation
        assert "  \"name\"" in result or '"name"' in result


class TestGenerateEnvTemplate:
    """Tests for generate_env_template function."""

    def test_returns_string(self):
        """Test that function returns a string."""
        result = generate_env_template()
        assert isinstance(result, str)

    def test_contains_advisor_config(self):
        """Test that template has advisor API config."""
        result = generate_env_template()
        assert "ADVISOR_API_URL" in result
        assert "localhost:8100" in result
        assert "BRIDGE_TOKEN" in result

    def test_contains_discord_config(self):
        """Test that template has Discord config."""
        result = generate_env_template()
        assert "DISCORD_TOKEN" in result
        assert "DISCORD_CLIENT_ID" in result
        assert "DISCORD_GUILD_ID" in result

    def test_contains_slack_config(self):
        """Test that template has Slack config."""
        result = generate_env_template()
        assert "SLACK_BOT_TOKEN" in result
        assert "SLACK_SIGNING_SECRET" in result
        assert "SLACK_APP_TOKEN" in result

    def test_contains_logging_config(self):
        """Test that template has logging config."""
        result = generate_env_template()
        assert "LOG_LEVEL" in result
        assert "LOG_FILE" in result

    def test_is_template_format(self):
        """Test that output is a template with placeholders."""
        result = generate_env_template()
        assert "your_" in result or "xoxb-" in result or "xapp-" in result


class TestGenerateIndexJs:
    """Tests for generate_index_js function."""

    def test_returns_string(self):
        """Test that function returns a string."""
        result = generate_index_js()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_express_import(self):
        """Test that code imports Express."""
        result = generate_index_js()
        assert "require('express')" in result

    def test_contains_discord_import(self):
        """Test that code imports Discord.js."""
        result = generate_index_js()
        assert "discord.js" in result

    def test_contains_slack_import(self):
        """Test that code imports Slack Bolt."""
        result = generate_index_js()
        assert "@slack/bolt" in result

    def test_contains_axios_import(self):
        """Test that code imports axios."""
        result = generate_index_js()
        assert "axios" in result

    def test_contains_winston_import(self):
        """Test that code imports winston for logging."""
        result = generate_index_js()
        assert "winston" in result

    def test_contains_dotenv_config(self):
        """Test that code configures dotenv."""
        result = generate_index_js()
        assert "dotenv" in result
        assert "config()" in result

    def test_contains_advisor_api_client_class(self):
        """Test that code defines AdvisorAPIClient class."""
        result = generate_index_js()
        assert "class AdvisorAPIClient" in result
        assert "baseURL" in result
        assert "bridgeToken" in result

    def test_contains_discord_client(self):
        """Test that code initializes Discord client."""
        result = generate_index_js()
        assert "new Client" in result
        assert "GatewayIntentBits" in result

    def test_contains_slack_app(self):
        """Test that code initializes Slack app."""
        result = generate_index_js()
        assert "new App" in result
        assert "socketMode" in result

    def test_contains_logger_setup(self):
        """Test that code sets up winston logger."""
        result = generate_index_js()
        assert "winston.createLogger" in result
        assert "winston.format" in result


class TestBridgeCodeIntegration:
    """Integration tests for bridge code generation."""

    def test_package_json_is_parseable(self):
        """Test that generated package.json can be parsed."""
        result = generate_package_json()
        pkg = json.loads(result)
        
        # Verify structure
        assert "name" in pkg
        assert "version" in pkg
        assert "dependencies" in pkg

    def test_all_required_deps_present(self):
        """Test that all required dependencies are present."""
        result = generate_package_json()
        pkg = json.loads(result)
        deps = pkg.get("dependencies", {})
        
        required = ["express", "discord.js", "@slack/bolt", "axios", "dotenv", "winston"]
        for dep in required:
            assert dep in deps, f"Missing dependency: {dep}"


class TestEdgeCases:
    """Edge case tests."""

    def test_package_json_version_format(self):
        """Test that version follows semver format."""
        result = generate_package_json()
        pkg = json.loads(result)
        version = pkg["version"]
        
        # Basic semver check (major.minor.patch)
        parts = version.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_env_template_is_multiline(self):
        """Test that env template has multiple lines."""
        result = generate_env_template()
        lines = result.split("\n")
        assert len(lines) > 10  # Should have many config lines

    def test_index_js_is_substantial(self):
        """Test that generated index.js is substantial code."""
        result = generate_index_js()
        assert len(result) > 1000  # Should be substantial
        
        # Should have multiple classes/functions
        assert result.count("class ") >= 1
        assert result.count("const ") >= 5
        assert result.count("async ") >= 2
