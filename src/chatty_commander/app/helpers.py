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

import logging
import os

logger = logging.getLogger(__name__)


def ensure_directory_exists(path: str) -> bool:
    """Ensure that a directory exists, creating it if necessary.

    Returns True if the directory exists (or was created), False if creation
    failed due to a permission or concurrent-creation issue. Those failures are
    logged rather than raised so non-critical callers are not interrupted (e.g.
    when another process created the directory first). Other errors, such as an
    invalid empty path, still propagate.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except (PermissionError, FileExistsError) as e:
        logger.warning("Failed to ensure directory %r exists: %s", path, e)
        return False


def format_command_output(cmd_output: str) -> str:
    """Format the output of a command for better readability."""
    return cmd_output.strip().replace("\n", " | ")


def parse_model_keybindings(keybindings_str: str) -> dict[str, str]:
    """Parse a string of keybindings into a dictionary."""
    keybindings: dict[str, str] = {}
    if keybindings_str:
        pairs = keybindings_str.split(",")
        for pair in pairs:
            if not pair.strip():
                continue
            try:
                model, keys = pair.split("=", 1)
            except ValueError:
                logger.warning("Skipping malformed keybinding entry: %r", pair)
                continue
            keybindings[model.strip()] = keys.strip()
    return keybindings


# Example usage of helper functions:
# directory = 'path/to/directory'
# ensure_directory_exists(directory)  # Make sure the directory exists
# formatted_output = format_command_output('Example output\nNew line included.')
# keybindings = parse_model_keybindings('model1=ctrl+shift+1,model2=alt+F4')
