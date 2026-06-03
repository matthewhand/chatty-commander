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
Tests for bridge_nodejs tool.
"""

import json
from pathlib import Path
import pytest

from src.chatty_commander.tools.bridge_nodejs import (
    generate_package_json,
    generate_env_template,
    generate_index_js,
    generate_readme,
    generate_dockerfile,
    generate_docker_compose,
    generate_bridge_app,
)


class TestBridgeNodejsGenerators:
    """Tests for individual file generation functions."""

    def test_generate_package_json(self):
        """Test package.json generation."""
        content = generate_package_json()
        data = json.loads(content)
        assert data["name"] == "chatty-commander-bridge"
        assert "dependencies" in data
        assert "express" in data["dependencies"]
        assert "discord.js" in data["dependencies"]
        assert "@slack/bolt" in data["dependencies"]

    def test_generate_env_template(self):
        """Test .env template generation."""
        content = generate_env_template()
        assert "ADVISOR_API_URL" in content
        assert "DISCORD_TOKEN" in content
        assert "SLACK_BOT_TOKEN" in content

    def test_generate_index_js(self):
        """Test index.js generation."""
        content = generate_index_js()
        assert "require('express')" in content
        assert "discord.js" in content
        assert "@slack/bolt" in content
        assert "class AdvisorAPIClient" in content

    def test_generate_readme(self):
        """Test README.md generation."""
        content = generate_readme()
        assert "# ChattyCommander Bridge" in content
        assert "Setup" in content
        assert "Configuration" in content

    def test_generate_dockerfile(self):
        """Test Dockerfile generation."""
        content = generate_dockerfile()
        assert "FROM node:18-alpine" in content
        assert "WORKDIR /app" in content
        assert 'CMD ["npm", "start"]' in content

    def test_generate_docker_compose(self):
        """Test docker-compose.yml generation."""
        content = generate_docker_compose()
        assert "version: '3.8'" in content
        assert "services:" in content
        assert "bridge:" in content


class TestGenerateBridgeApp:
    """Tests for the complete application generation."""

    def test_generate_bridge_app(self, tmp_path):
        """Test that generate_bridge_app creates the expected files and directories."""
        output_dir = tmp_path / "test_bridge"
        generate_bridge_app(str(output_dir))

        # Check directory structure
        assert output_dir.exists()
        assert (output_dir / "src").is_dir()
        assert (output_dir / "logs").is_dir()

        # Check files
        expected_files = [
            "package.json",
            ".env.example",
            "src/index.js",
            "README.md",
            "Dockerfile",
            "docker-compose.yml",
            ".gitignore",
        ]

        for filename in expected_files:
            file_path = output_dir / filename
            assert file_path.exists()
            assert file_path.stat().st_size > 0

        # Spot check content of one file
        with open(output_dir / "package.json", "r") as f:
            data = json.load(f)
            assert data["name"] == "chatty-commander-bridge"
