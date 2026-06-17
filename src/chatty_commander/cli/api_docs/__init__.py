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

"""API documentation generator for ChattyCommander.

Run as a module to generate OpenAPI JSON + Markdown docs:

    python -m chatty_commander.cli.api_docs -o docs

Modules:
- ``cli``: argument parsing and exit codes
- ``workflow``: orchestrates generation and writes artifacts
- ``builder``: pure builders for the OpenAPI schema and Markdown docs
- ``fs_ops``: atomic filesystem write helpers
"""

<<<<<<< HEAD:src/chatty_commander/cli/api_docs/__init__.py
from .cli import main

__all__ = ["main"]
=======
from chatty_commander.ai.agents.fleet import (
    AgentFleet,
    AgentFleetConfig,
    AgentInstance,
)
from chatty_commander.ai.agents.launcher import (
    LaunchConfig,
)

__all__ = [
    "AgentFleet",
    "AgentFleetConfig",
    "AgentInstance",
    "LaunchConfig",
]
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16:src/chatty_commander/ai/agents/__init__.py
