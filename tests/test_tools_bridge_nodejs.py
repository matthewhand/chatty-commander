"""
Tests for the Node.js bridge generator tool.
"""

import json
from pathlib import Path

from chatty_commander.tools.bridge_nodejs import (
    generate_bridge_app,
    generate_docker_compose,
    generate_dockerfile,
    generate_env_template,
    generate_index_js,
    generate_package_json,
    generate_readme,
)


def test_generate_package_json():
    """Test package.json generation."""
    content = generate_package_json()
    data = json.loads(content)

    assert data["name"] == "chatty-commander-bridge"
    assert "dependencies" in data
    assert "express" in data["dependencies"]
    assert "discord.js" in data["dependencies"]
    assert "@slack/bolt" in data["dependencies"]
    assert "scripts" in data
    assert "start" in data["scripts"]


def test_generate_env_template():
    """Test .env template generation."""
    content = generate_env_template()
    assert "ADVISOR_API_URL" in content
    assert "DISCORD_TOKEN" in content
    assert "SLACK_BOT_TOKEN" in content
    assert "LOG_LEVEL" in content


def test_generate_index_js():
    """Test index.js generation."""
    content = generate_index_js()
    # Basic dependencies
    assert "require('express')" in content
    assert "require('discord.js')" in content
    assert "require('@slack/bolt')" in content
    assert "app.listen" in content
    assert "discordClient.login" in content

    # New features
    assert "app.post('/send'" in content  # Proactive messaging
    assert "app.get('/'" in content       # Dashboard
    assert "ChattyCommander Bridge Status" in content  # Dashboard title
    assert "process.env.BRIDGE_TOKEN" in content # Auth check


def test_generate_readme():
    """Test README generation."""
    content = generate_readme()
    assert "# ChattyCommander Bridge" in content
    assert "## Features" in content
    assert "## Setup" in content
    assert "npm install" in content


def test_generate_dockerfile():
    """Test Dockerfile generation."""
    content = generate_dockerfile()
    assert "FROM node:18-alpine" in content
    assert "WORKDIR /app" in content
    assert "CMD [\"npm\", \"start\"]" in content


def test_generate_docker_compose():
    """Test docker-compose.yml generation."""
    content = generate_docker_compose()
    assert "services:" in content
    assert "bridge:" in content
    assert "ADVISOR_API_URL" in content


def test_generate_bridge_app_creates_files(tmp_path):
    """Test full bridge application generation."""
    output_dir = tmp_path / "bridge_test"
    generate_bridge_app(str(output_dir))

    # Check directory structure
    assert output_dir.exists()
    assert (output_dir / "src").exists()
    assert (output_dir / "logs").exists()

    # Check files existence
    files_to_check = [
        "package.json",
        ".env.example",
        "src/index.js",
        "README.md",
        "Dockerfile",
        "docker-compose.yml",
        ".gitignore",
    ]

    for filename in files_to_check:
        assert (output_dir / filename).exists()

    # Verify package.json is valid JSON
    with open(output_dir / "package.json") as f:
        data = json.load(f)
        assert data["name"] == "chatty-commander-bridge"
