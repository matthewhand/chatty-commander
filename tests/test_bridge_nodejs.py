import json
from pathlib import Path
from chatty_commander.tools.bridge_nodejs import (
    generate_package_json,
    generate_env_template,
    generate_index_js,
    generate_readme,
    generate_dockerfile,
    generate_docker_compose,
    generate_bridge_app,
)

def test_generate_package_json():
    """Test generating package.json for the Node.js bridge application."""
    content = generate_package_json()
    data = json.loads(content)

    assert data["name"] == "chatty-commander-bridge"
    assert "scripts" in data
    assert "dependencies" in data
    assert "devDependencies" in data

    deps = data["dependencies"]
    assert "express" in deps
    assert "discord.js" in deps
    assert "@slack/bolt" in deps
    assert "axios" in deps
    assert "dotenv" in deps
    assert "winston" in deps

def test_generate_env_template():
    """Test generating .env template for configuration."""
    content = generate_env_template()

    assert "ADVISOR_API_URL" in content
    assert "BRIDGE_TOKEN" in content
    assert "DISCORD_TOKEN" in content
    assert "SLACK_BOT_TOKEN" in content
    assert "LOG_LEVEL" in content

def test_generate_index_js():
    """Test generating the main index.js file."""
    content = generate_index_js()

    assert "require('express')" in content
    assert "require('discord.js')" in content
    assert "require('@slack/bolt')" in content
    assert "AdvisorAPIClient" in content
    assert "new Client" in content
    assert "new App" in content

def test_generate_readme():
    """Test generating README.md."""
    content = generate_readme()

    assert "# ChattyCommander Bridge" in content
    assert "Setup" in content
    assert "Configuration" in content

def test_generate_dockerfile():
    """Test generating Dockerfile."""
    content = generate_dockerfile()

    assert "FROM node:18-alpine" in content
    assert "EXPOSE 3001" in content
    assert "HEALTHCHECK" in content

def test_generate_docker_compose():
    """Test generating docker-compose.yml."""
    content = generate_docker_compose()

    assert "version: '3.8'" in content
    assert "services:" in content
    assert "bridge:" in content
    assert "ADVISOR_API_URL" in content

def test_generate_bridge_app(tmp_path: Path):
    """Test generating the complete Node.js bridge application."""
    output_dir = tmp_path / "bridge_test"
    generate_bridge_app(str(output_dir))

    assert output_dir.exists()
    assert (output_dir / "src").exists()
    assert (output_dir / "logs").exists()

    files = [
        "package.json",
        ".env.example",
        "src/index.js",
        "README.md",
        "Dockerfile",
        "docker-compose.yml",
        ".gitignore",
    ]

    for filename in files:
        assert (output_dir / filename).exists()

    # Verify content of package.json matches generate_package_json output
    with open(output_dir / "package.json", "r") as f:
        package_content = f.read()

    expected_package_content = generate_package_json()
    assert json.loads(package_content) == json.loads(expected_package_content)
