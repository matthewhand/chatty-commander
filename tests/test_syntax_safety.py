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
AST-based syntax safety regression tests.

This module walks all Python files in src/ and validates that:
1. No orphan try blocks exist (try without handlers or finalbody)
2. Other syntax safety patterns as needed
"""

import ast
import os
from pathlib import Path

import pytest


def get_python_files_in_src():
    """Get all Python files in the src/ directory."""
    src_dir = Path(__file__).parent.parent / "src"
    if not src_dir.exists():
        return []

    python_files = []
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)

    return python_files


def check_orphan_try_blocks(file_path: Path):
    """Check a Python file for orphan try blocks.

    Returns a list of line numbers where orphan try blocks are found.
    An orphan try block is one that has neither handlers nor finalbody.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError) as e:
        pytest.fail(f"Failed to parse {file_path}: {e}")

    orphan_tries = []

    class TryVisitor(ast.NodeVisitor):
        def visit_Try(self, node):
            # Check if try block has neither exception handlers nor finally block
            if not node.handlers and not node.finalbody:
                orphan_tries.append(node.lineno)

            # Continue visiting child nodes
            self.generic_visit(node)

    visitor = TryVisitor()
    visitor.visit(tree)

    return orphan_tries


def test_no_orphan_try_blocks():
    """Test that no Python files in src/ contain orphan try blocks."""
    python_files = get_python_files_in_src()

    if not python_files:
        pytest.skip("No Python files found in src/ directory")

    all_orphans = {}

    for file_path in python_files:
        orphan_lines = check_orphan_try_blocks(file_path)
        if orphan_lines:
            # Make path relative to project root for cleaner error messages
            rel_path = file_path.relative_to(Path(__file__).parent.parent)
            all_orphans[str(rel_path)] = orphan_lines

    if all_orphans:
        error_msg = "Found orphan try blocks (try without except or finally):\n"
        for file_path, lines in all_orphans.items():
            error_msg += f"  {file_path}: lines {', '.join(map(str, lines))}\n"
        error_msg += (
            "\nOrphan try blocks are invalid Python syntax and should be fixed."
        )
        pytest.fail(error_msg)


def test_python_files_parse_successfully():
    """Test that all Python files in src/ can be parsed by ast.parse()."""
    python_files = get_python_files_in_src()

    if not python_files:
        pytest.skip("No Python files found in src/ directory")

    parse_errors = {}

    for file_path in python_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            ast.parse(content, filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError) as e:
            rel_path = file_path.relative_to(Path(__file__).parent.parent)
            parse_errors[str(rel_path)] = str(e)

    if parse_errors:
        error_msg = "Found Python files with syntax errors:\n"
        for file_path, error in parse_errors.items():
            error_msg += f"  {file_path}: {error}\n"
        pytest.fail(error_msg)


if __name__ == "__main__":
    # Allow running this test directly for debugging
    test_no_orphan_try_blocks()
    test_python_files_parse_successfully()
    print("All syntax safety tests passed!")
