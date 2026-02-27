#!/usr/bin/env python3
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
Node.js Bridge Generator for Discord/Slack Integration

This tool generates a Node.js application that acts as a bridge between
Discord/Slack platforms and the Python advisor API.
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Constants
TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates" / "bridge_nodejs"


def render_template(template_name: str, context: dict) -> str:
    """Render a Jinja2 template."""
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(template_name)
    return template.render(context)


def generate_package_json() -> str:
    """Generate package.json for the Node.js bridge application."""
    context = {
        "name": "chatty-commander-bridge",
        "version": "1.0.0",
        "description": "Node.js bridge for Discord/Slack integration with ChattyCommander advisors",
    }
    return render_template("package.json.j2", context)


def generate_env_template() -> str:
    """Generate .env template for configuration."""
    context = {
        "advisor_api_url": "http://localhost:8100",
        "bridge_token": "your_shared_secret_here",
        "discord_token": "your_discord_bot_token",
        "discord_client_id": "your_discord_client_id",
        "discord_guild_id": "your_discord_guild_id",
        "slack_bot_token": "xoxb-your-slack-bot-token",
        "slack_signing_secret": "your_slack_signing_secret",
        "slack_app_token": "xapp-your-slack-app-token",
        "log_level": "info",
        "log_file": "bridge.log",
    }
    return render_template(".env.example.j2", context)


def generate_index_js() -> str:
    """Generate the main index.js file for the bridge application."""
    context = {
        "log_level_default": "info",
        "log_file_default": "bridge.log",
        "advisor_api_url_default": "http://localhost:8100",
        "port_default": 3001,
    }
    return render_template("index.js.j2", context)


def generate_readme() -> str:
    """Generate README.md for the Node.js bridge application."""
    context = {
        "name": "ChattyCommander Bridge",
        "description": "Node.js bridge application for connecting Discord and Slack to the ChattyCommander advisor API.",
    }
    return render_template("README.md.j2", context)


def generate_dockerfile() -> str:
    """Generate Dockerfile for containerized deployment."""
    context = {
        "node_version": "18",
        "port": 3001,
    }
    return render_template("Dockerfile.j2", context)


def generate_docker_compose() -> str:
    """Generate docker-compose.yml for local development."""
    context = {
        "port": 3001,
        "advisor_api_url_default": "http://host.docker.internal:8100",
    }
    return render_template("docker-compose.yml.j2", context)


def generate_bridge_app(output_dir: str = "bridge") -> None:
    """Generate the complete Node.js bridge application."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Create directory structure
    (output_path / "src").mkdir(exist_ok=True)
    (output_path / "logs").mkdir(exist_ok=True)

    # Generate files
    files = {
        "package.json": generate_package_json(),
        ".env.example": generate_env_template(),
        "src/index.js": generate_index_js(),
        "README.md": generate_readme(),
        "Dockerfile": generate_dockerfile(),
        "docker-compose.yml": generate_docker_compose(),
        ".gitignore": "node_modules/\n.env\nlogs/\n*.log\n",
    }

    for filename, content in files.items():
        file_path = output_path / filename
        with open(file_path, "w") as f:
            f.write(content)
        print(f"Generated: {file_path}")

    print(f"\nBridge application generated in: {output_path.absolute()}")
    print("Next steps:")
    print("1. cd bridge")
    print("2. npm install")
    print("3. cp .env.example .env")
    print("4. Configure your environment variables")
    print("5. npm start")


if __name__ == "__main__":
    import sys

    output_dir = sys.argv[1] if len(sys.argv) > 1 else "bridge"
    generate_bridge_app(output_dir)
