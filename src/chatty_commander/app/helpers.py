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
helpers.py

Utility functions for the ChattyCommander application. This module contains helper functions that are used
across different components of the application to perform common tasks.
"""
import os

def ensure_directory_exists(directory_path: str) -> None:
    """Ensures that the given directory exists, creating it if necessary."""
    os.makedirs(directory_path, exist_ok=True)

def format_command_output(output: str) -> str:
    """Formats a multi-line command output string into a single line separated by pipes."""
    return " | ".join(line for line in output.splitlines() if line)

def parse_model_keybindings(keybindings_str: str) -> dict[str, str]:
    """Parses a comma-separated keybindings string into a dictionary mapping models to keys."""
    if not keybindings_str:
        return {}

    result = {}
    for binding in keybindings_str.split(","):
        if "=" in binding:
            model, key = binding.split("=", 1)
            result[model.strip()] = key.strip()
    return result
