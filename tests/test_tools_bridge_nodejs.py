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
Comprehensive tests for tools/bridge_nodejs.py module.

Tests the Node.js bridge generator functions for Discord/Slack integration.
"""

import json
from unittest.mock import mock_open, patch

from chatty_commander.tools.bridge_nodejs import (
    generate_bridge_app,
    generate_docker_compose,
    generate_dockerfile,
    generate_env_template,
    generate_index_js,
    generate_package_json,
    generate_readme,
)


class TestPackageJsonGeneration:
    """Test package.json generation."""

    def test_generate_package_json_structure(self):
        """Test that package.json has the correct structure."""
        package_json = generate_package_json()

        # Parse JSON to validate structure
        data = json.loads(package_json)

        # Test required fields
        assert data["name"] == "chatty-commander-bridge"
        assert data["version"] == "1.0.0"
        assert "description" in data
        assert "main" in data
        assert "scripts" in data
        assert "dependencies" in data
        assert "devDependencies" in data
        assert "engines" in data

    def test_scripts_section(self):
        """Test the scripts section of package.json."""
        package_json = generate_package_json()
        data = json.loads(package_json)

        scripts = data["scripts"]
        assert scripts["start"] == "node src/index.js"
        assert scripts["dev"] == "nodemon src/index.js"
        assert scripts["test"] == "jest"

    def test_dependencies_section(self):
        """Test the dependencies section."""
        package_json = generate_package_json()
        data = json.loads(package_json)

        deps = data["dependencies"]
        expected_deps = [
            "express", "discord.js", "@slack/bolt",
            "axios", "dotenv", "winston"
        ]

        for dep in expected_deps:
            assert dep in deps

    def test_dev_dependencies(self):
        """Test the devDependencies section."""
        package_json = generate_package_json()
        data = json.loads(package_json)

        dev_deps = data["devDependencies"]
        assert "nodemon" in dev_deps
        assert "jest" in dev_deps

    def test_engines_section(self):
        """Test the engines section."""
        package_json = generate_package_json()
        data = json.loads(package_json)

        assert data["engines"]["node"] == ">=18.0.0"

    def test_json_format(self):
        """Test that the output is valid JSON."""
        package_json = generate_package_json()

        # Should not raise JSONDecodeError
        data = json.loads(package_json)

        # Should be pretty-printed with indent=2
        lines = package_json.split('\n')
        assert len(lines) > 1  # Multi-line JSON

    def test_return_type(self):
        """Test that the function returns a string."""
        result = generate_package_json()
        assert isinstance(result, str)


class TestEnvTemplateGeneration:
    """Test .env template generation."""

    def test_generate_env_template_structure(self):
        """Test that .env template has the correct structure."""
        env_template = generate_env_template()

        assert isinstance(env_template, str)
        assert len(env_template) > 100  # Should be substantial content

    def test_env_sections(self):
        """Test that all required environment sections are present."""
        env_template = generate_env_template()

        # Test for section headers
        assert "# Node.js Bridge Configuration" in env_template
        assert "# Python Advisor API" in env_template
        assert "# Discord Bot Configuration" in env_template
        assert "# Slack App Configuration" in env_template
        assert "# Logging" in env_template

    def test_environment_variables(self):
        """Test that all required environment variables are documented."""
        env_template = generate_env_template()

        expected_vars = [
            "ADVISOR_API_URL",
            "BRIDGE_TOKEN",
            "DISCORD_TOKEN",
            "DISCORD_CLIENT_ID",
            "DISCORD_GUILD_ID",
            "SLACK_BOT_TOKEN",
            "SLACK_SIGNING_SECRET",
            "SLACK_APP_TOKEN",
            "LOG_LEVEL",
            "LOG_FILE"
        ]

        for var in expected_vars:
            assert var in env_template

    def test_default_values(self):
        """Test that default values are provided where appropriate."""
        env_template = generate_env_template()

        assert "ADVISOR_API_URL=http://localhost:8100" in env_template
        assert "LOG_LEVEL=info" in env_template
        assert "LOG_FILE=bridge.log" in env_template


class TestIndexJsGeneration:
    """Test index.js generation."""

    def test_generate_index_js_structure(self):
        """Test that index.js has the correct structure."""
        index_js = generate_index_js()

        assert isinstance(index_js, str)
        assert len(index_js) > 500  # Should be substantial JavaScript code

    def test_required_imports(self):
        """Test that all required imports are present."""
        index_js = generate_index_js()

        required_imports = [
            "express",
            "discord.js",
            "@slack/bolt",
            "axios",
            "winston",
            "dotenv"
        ]

        for import_name in required_imports:
            assert import_name in index_js

    def test_discord_client_setup(self):
        """Test that Discord client setup is included."""
        index_js = generate_index_js()

        assert "new Client({" in index_js
        assert "GatewayIntentBits.Guilds" in index_js
        assert "GatewayIntentBits.GuildMessages" in index_js
        assert "GatewayIntentBits.MessageContent" in index_js

    def test_slack_app_setup(self):
        """Test that Slack app setup is included."""
        index_js = generate_index_js()

        assert "new App({" in index_js
        assert "SLACK_BOT_TOKEN" in index_js
        assert "SLACK_SIGNING_SECRET" in index_js
        assert "socketMode: true" in index_js

    def test_advisor_api_client(self):
        """Test that AdvisorAPIClient class is defined."""
        index_js = generate_index_js()

        assert "class AdvisorAPIClient" in index_js
        assert "sendMessage" in index_js
        assert "sendBridgeEvent" in index_js

    def test_event_handlers(self):
        """Test that event handlers are defined."""
        index_js = generate_index_js()

        assert "discordClient.on('ready'" in index_js
        assert "discordClient.on('messageCreate'" in index_js
        assert "slackApp.message" in index_js

    def test_health_endpoint(self):
        """Test that health check endpoint is defined."""
        index_js = generate_index_js()

        assert "app.get('/health'" in index_js
        assert "res.json({ status: 'ok'" in index_js

    def test_error_handling(self):
        """Test that error handling is included."""
        index_js = generate_index_js()

        assert "try {" in index_js
        assert "catch (error)" in index_js
        assert "logger.error" in index_js

    def test_start_function(self):
        """Test that the start function is defined."""
        index_js = generate_index_js()

        assert "async function start()" in index_js
        assert "app.listen(port" in index_js
        assert "discordClient.login" in index_js
        assert "slackApp.start()" in index_js


class TestReadmeGeneration:
    """Test README.md generation."""

    def test_generate_readme_structure(self):
        """Test that README has the correct structure."""
        readme = generate_readme()

        assert isinstance(readme, str)
        assert "# ChattyCommander Bridge" in readme
        assert "## Features" in readme
        assert "## Setup" in readme
        assert "## Configuration" in readme

    def test_setup_instructions(self):
        """Test that setup instructions are included."""
        readme = generate_readme()

        assert "npm install" in readme
        assert "cp .env.example .env" in readme
        assert "npm start" in readme

    def test_discord_setup_section(self):
        """Test that Discord setup instructions are included."""
        readme = generate_readme()

        assert "## Discord Bot Setup" in readme
        assert "discord.com/developers/applications" in readme
        assert "Message Content Intent" in readme

    def test_slack_setup_section(self):
        """Test that Slack setup instructions are included."""
        readme = generate_readme()

        assert "## Slack App Setup" in readme
        assert "api.slack.com/apps" in readme
        assert "chat:write" in readme
        assert "event subscriptions" in readme

    def test_environment_variables_section(self):
        """Test that environment variables are documented."""
        readme = generate_readme()

        env_vars = [
            "ADVISOR_API_URL",
            "BRIDGE_TOKEN",
            "DISCORD_TOKEN",
            "SLACK_BOT_TOKEN",
            "SLACK_SIGNING_SECRET",
            "SLACK_APP_TOKEN"
        ]

        for var in env_vars:
            assert var in readme

    def test_development_section(self):
        """Test that development instructions are included."""
        readme = generate_readme()

        assert "## Development" in readme
        assert "npm run dev" in readme
        assert "npm test" in readme

    def test_deployment_section(self):
        """Test that deployment instructions are included."""
        readme = generate_readme()

        assert "## Deployment" in readme
        assert "Heroku" in readme
        assert "Railway" in readme


class TestDockerfileGeneration:
    """Test Dockerfile generation."""

    def test_generate_dockerfile_structure(self):
        """Test that Dockerfile has the correct structure."""
        dockerfile = generate_dockerfile()

        assert isinstance(dockerfile, str)
        assert "FROM node:18-alpine" in dockerfile
        assert "WORKDIR /app" in dockerfile
        assert "EXPOSE 3001" in dockerfile

    def test_node_version(self):
        """Test that correct Node.js version is specified."""
        dockerfile = generate_dockerfile()

        assert "node:18-alpine" in dockerfile

    def test_security_features(self):
        """Test that security features are included."""
        dockerfile = generate_dockerfile()

        assert "addgroup -g 1001 -S nodejs" in dockerfile
        assert "adduser -S bridge -u 1001" in dockerfile
        assert "USER bridge" in dockerfile

    def test_health_check(self):
        """Test that health check is configured."""
        dockerfile = generate_dockerfile()

        assert "HEALTHCHECK" in dockerfile
        assert "CMD node -e" in dockerfile
        assert "localhost:3001/health" in dockerfile

    def test_copy_instructions(self):
        """Test that copy instructions are correct."""
        dockerfile = generate_dockerfile()

        assert "COPY package*.json ./" in dockerfile
        assert "COPY . ." in dockerfile

    def test_start_command(self):
        """Test that the correct start command is specified."""
        dockerfile = generate_dockerfile()

        assert 'CMD ["npm", "start"]' in dockerfile


class TestDockerComposeGeneration:
    """Test docker-compose.yml generation."""

    def test_generate_docker_compose_structure(self):
        """Test that docker-compose.yml has the correct structure."""
        docker_compose = generate_docker_compose()

        assert isinstance(docker_compose, str)
        assert "version: '3.8'" in docker_compose
        assert "services:" in docker_compose

    def test_service_configuration(self):
        """Test that service configuration is correct."""
        docker_compose = generate_docker_compose()

        assert "bridge:" in docker_compose
        assert "build: ." in docker_compose
        assert "ports:" in docker_compose
        assert '"3001:3001"' in docker_compose

    def test_environment_variables(self):
        """Test that environment variables are configured."""
        docker_compose = generate_docker_compose()

        env_vars = [
            "ADVISOR_API_URL=http://host.docker.internal:8100",
            "BRIDGE_TOKEN=${BRIDGE_TOKEN}",
            "DISCORD_TOKEN=${DISCORD_TOKEN}",
            "SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}",
            "SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET}",
            "SLACK_APP_TOKEN=${SLACK_APP_TOKEN}"
        ]

        for var in env_vars:
            assert var in docker_compose

    def test_volumes_configuration(self):
        """Test that volumes are configured correctly."""
        docker_compose = generate_docker_compose()

        assert "volumes:" in docker_compose
        assert "./logs:/app/logs" in docker_compose

    def test_restart_policy(self):
        """Test that restart policy is configured."""
        docker_compose = generate_docker_compose()

        assert "restart: unless-stopped" in docker_compose


class TestBridgeAppGeneration:
    """Test the main bridge application generation function."""

    def test_generate_bridge_app_creates_directory(self, tmp_path):
        """Test that generate_bridge_app creates the output directory."""
        output_dir = tmp_path / "test_bridge"

        with patch('builtins.open', mock_open()) as mock_file:
            with patch('builtins.print'):
                generate_bridge_app(str(output_dir))

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_generate_bridge_app_creates_subdirectories(self, tmp_path):
        """Test that generate_bridge_app creates required subdirectories."""
        output_dir = tmp_path / "test_bridge"

        with patch('builtins.open', mock_open()) as mock_file:
            with patch('builtins.print'):
                generate_bridge_app(str(output_dir))

        # Check for src and logs directories
        assert (output_dir / "src").exists()
        assert (output_dir / "logs").exists()

    def test_generate_bridge_app_creates_files(self, tmp_path):
        """Test that generate_bridge_app creates all required files."""
        output_dir = tmp_path / "test_bridge"

        with patch('builtins.open', mock_open()) as mock_file:
            with patch('builtins.print'):
                generate_bridge_app(str(output_dir))

        expected_files = [
            "package.json",
            ".env.example",
            "src/index.js",
            "README.md",
            "Dockerfile",
            "docker-compose.yml",
            ".gitignore"
        ]

        for filename in expected_files:
            file_path = output_dir / filename
            assert file_path.exists(), f"Missing file: {filename}"

    def test_generate_bridge_app_calls_all_generators(self, tmp_path):
        """Test that generate_bridge_app calls all generation functions."""
        output_dir = tmp_path / "test_bridge"

        with patch('chatty_commander.tools.bridge_nodejs.generate_package_json') as mock_package:
            with patch('chatty_commander.tools.bridge_nodejs.generate_env_template') as mock_env:
                with patch('chatty_commander.tools.bridge_nodejs.generate_index_js') as mock_js:
                    with patch('chatty_commander.tools.bridge_nodejs.generate_readme') as mock_readme:
                        with patch('chatty_commander.tools.bridge_nodejs.generate_dockerfile') as mock_docker:
                            with patch('chatty_commander.tools.bridge_nodejs.generate_docker_compose') as mock_compose:
                                with patch('builtins.open', mock_open()):
                                    with patch('builtins.print'):
                                        mock_package.return_value = '{"test": "package"}'
                                        mock_env.return_value = "ENV_TEMPLATE"
                                        mock_js.return_value = "INDEX_JS"
                                        mock_readme.return_value = "README"
                                        mock_docker.return_value = "DOCKERFILE"
                                        mock_compose.return_value = "COMPOSE"

                                        generate_bridge_app(str(output_dir))

        # Verify all functions were called
        mock_package.assert_called_once()
        mock_env.assert_called_once()
        mock_js.assert_called_once()
        mock_readme.assert_called_once()
        mock_docker.assert_called_once()
        mock_compose.assert_called_once()

    def test_generate_bridge_app_handles_existing_directory(self, tmp_path):
        """Test that generate_bridge_app handles existing directories gracefully."""
        output_dir = tmp_path / "existing_bridge"
        output_dir.mkdir()

        # Create a file in the directory
        (output_dir / "existing_file.txt").write_text("existing content")

        with patch('builtins.open', mock_open()) as mock_file:
            with patch('builtins.print'):
                # Should not raise an error
                generate_bridge_app(str(output_dir))

        # Directory should still exist
        assert output_dir.exists()

    def test_generate_bridge_app_default_output_dir(self):
        """Test that generate_bridge_app uses default directory when none specified."""
        with patch('chatty_commander.tools.bridge_nodejs.generate_bridge_app') as mock_generate:
            with patch('builtins.open', mock_open()):
                with patch('builtins.print'):
                    with patch('sys.argv', ['bridge_nodejs.py']):
                        # Import and call the main block
                        import chatty_commander.tools.bridge_nodejs as bridge_module
                        bridge_module.generate_bridge_app("bridge")

            # Should be called with default "bridge" directory
            mock_generate.assert_called_with("bridge")


class TestIntegration:
    """Integration tests for the bridge module."""

    def test_all_generated_files_are_valid(self, tmp_path):
        """Test that all generated files are valid and parseable."""
        output_dir = tmp_path / "test_bridge"

        with patch('builtins.open', mock_open()):
            with patch('builtins.print'):
                generate_bridge_app(str(output_dir))

        # Test package.json is valid JSON
        package_json_path = output_dir / "package.json"
        with open(package_json_path) as f:
            json.loads(f.read())

        # Test that all text files are non-empty
        text_files = [
            ".env.example",
            "src/index.js",
            "README.md",
            "Dockerfile",
            "docker-compose.yml",
            ".gitignore"
        ]

        for filename in text_files:
            file_path = output_dir / filename
            with open(file_path) as f:
                content = f.read()
                assert len(content) > 0, f"Empty file: {filename}"

    def test_generated_application_structure(self, tmp_path):
        """Test that the generated application has the correct structure."""
        output_dir = tmp_path / "test_bridge"

        with patch('builtins.open', mock_open()):
            with patch('builtins.print'):
                generate_bridge_app(str(output_dir))

        # Verify the structure matches what the Node.js app expects
        assert (output_dir / "package.json").exists()
        assert (output_dir / ".env.example").exists()
        assert (output_dir / "src" / "index.js").exists()

        # Verify the main entry point exists
        index_js_path = output_dir / "src" / "index.js"
        with open(index_js_path) as f:
            index_content = f.read()
            assert "const express = require('express');" in index_content
            assert "const { Client, GatewayIntentBits } = require('discord.js');" in index_content

    def test_function_purity(self):
        """Test that all functions are pure (no side effects)."""
        # Call functions multiple times
        package1 = generate_package_json()
        package2 = generate_package_json()

        env1 = generate_env_template()
        env2 = generate_env_template()

        readme1 = generate_readme()
        readme2 = generate_readme()

        dockerfile1 = generate_dockerfile()
        dockerfile2 = generate_dockerfile()

        docker_compose1 = generate_docker_compose()
        docker_compose2 = generate_docker_compose()

        # Results should be identical
        assert package1 == package2
        assert env1 == env2
        assert readme1 == readme2
        assert dockerfile1 == dockerfile2
        assert docker_compose1 == docker_compose2
