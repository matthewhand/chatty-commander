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
    return cmd_output.strip().replace('\n', ' | ')

def parse_model_keybindings(keybindings_str):
    """Parse a string of keybindings into a dictionary."""
    keybindings = {}
    if keybindings_str:
        pairs = keybindings_str.split(',')
        for pair in pairs:
            model, keys = pair.split('=')
            keybindings[model.strip()] = keys.strip()
    return keybindings

# Example usage of helper functions:
# directory = 'path/to/directory'
# ensure_directory_exists(directory)  # Make sure the directory exists
# formatted_output = format_command_output('Example output\nNew line included.')
# keybindings = parse_model_keybindings('model1=ctrl+shift+1,model2=alt+F4')
