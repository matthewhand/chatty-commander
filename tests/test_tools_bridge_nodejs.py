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
    content = generate_env_template()
    assert "ADVISOR_API_URL=" in content
    assert "BRIDGE_TOKEN=" in content
    assert "DISCORD_TOKEN=" in content
    assert "SLACK_BOT_TOKEN=" in content

def test_generate_index_js():
    content = generate_index_js()
    assert "require('express')" in content
    assert "require('discord.js')" in content
    assert "require('@slack/bolt')" in content
    assert "class AdvisorAPIClient" in content

def test_generate_readme():
    content = generate_readme()
    assert "# ChattyCommander Bridge" in content
    assert "## Setup" in content
    assert "## Configuration" in content

def test_generate_dockerfile():
    content = generate_dockerfile()
    assert "FROM node:18-alpine" in content
    assert "WORKDIR /app" in content
    assert "CMD [\"npm\", \"start\"]" in content

def test_generate_docker_compose():
    content = generate_docker_compose()
    assert "version: '3.8'" in content
    assert "services:" in content
    assert "bridge:" in content
    assert "ADVISOR_API_URL=" in content

def test_generate_bridge_app(tmp_path):
    output_dir = tmp_path / "bridge_test"
    generate_bridge_app(str(output_dir))

    assert output_dir.is_dir()
    assert (output_dir / "src").is_dir()
    assert (output_dir / "logs").is_dir()
    assert (output_dir / "package.json").is_file()
    assert (output_dir / ".env.example").is_file()
    assert (output_dir / "src/index.js").is_file()
    assert (output_dir / "README.md").is_file()
    assert (output_dir / "Dockerfile").is_file()
    assert (output_dir / "docker-compose.yml").is_file()
    assert (output_dir / ".gitignore").is_file()
