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


def ensure_directory_exists(path):
    """Ensure that a directory exists, and if not, create it."""
    if not os.path.exists(path):
        os.makedirs(path)


def format_command_output(cmd_output):
    """Format the output of a command for better readability."""
    return cmd_output.strip().replace("\n", " | ")


def parse_model_keybindings(keybindings_str):
    """Parse a string of keybindings into a dictionary."""
    keybindings = {}
    if keybindings_str:
        pairs = keybindings_str.split(",")
        for pair in pairs:
            model, keys = pair.split("=")
            keybindings[model.strip()] = keys.strip()
    return keybindings


# Example usage of helper functions:
# directory = 'path/to/directory'
# ensure_directory_exists(directory)  # Make sure the directory exists
# formatted_output = format_command_output('Example output\nNew line included.')
# keybindings = parse_model_keybindings('model1=ctrl+shift+1,model2=alt+F4')
