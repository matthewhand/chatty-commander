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

import sys
from unittest.mock import MagicMock
import pytest

# Safely mock fastapi and pydantic for this specific module's import
# to allow testing _extract_json_from_response even if dependencies are missing,
# without polluting sys.modules for subsequent tests.
_missing_fastapi = "fastapi" not in sys.modules
_missing_pydantic = "pydantic" not in sys.modules
_original_modules = sys.modules.copy()

try:
    if _missing_fastapi:
        sys.modules["fastapi"] = MagicMock()
    if _missing_pydantic:
        sys.modules["pydantic"] = MagicMock()

    from chatty_commander.web.routes.agents import _extract_json_from_response
finally:
    # Remove any module that was imported while fastapi/pydantic were mocked
    # to ensure they are cleanly re-imported by subsequent tests that need the real ones.
    for mod_name in list(sys.modules.keys()):
        if mod_name not in _original_modules:
            del sys.modules[mod_name]

    if _missing_fastapi and "fastapi" in sys.modules:
        del sys.modules["fastapi"]
    if _missing_pydantic and "pydantic" in sys.modules:
        del sys.modules["pydantic"]

def test_extract_json_standard_markdown():
    """Test extraction from a standard ```json ... ``` block."""
    response = 'Here is the JSON: ```json {"key": "value"} ```'
    assert _extract_json_from_response(response) == '{"key": "value"}'

def test_extract_json_generic_markdown():
    """Test extraction from a generic ``` ... ``` block."""
    response = 'Some data: ``` {"key": "value"} ```'
    assert _extract_json_from_response(response) == '{"key": "value"}'

def test_extract_json_plain_text():
    """Test extraction from a response without markdown blocks."""
    response = '{"key": "value"}'
    assert _extract_json_from_response(response) == '{"key": "value"}'

def test_extract_json_with_whitespace():
    """Test extraction with extra whitespace and newlines."""
    response = '\n  ```json\n  {"key": "value"}\n  ```  \n'
    assert _extract_json_from_response(response) == '{"key": "value"}'

def test_extract_json_text_around_block():
    """Test extraction when there is text before and after the code block."""
    response = 'Prefix text\n```json\n{"key": "value"}\n```\nSuffix text'
    assert _extract_json_from_response(response) == '{"key": "value"}'

def test_extract_json_multiple_blocks():
    """Test extraction when there are multiple code blocks (should pick the first)."""
    # Current implementation uses re.search which finds the first match
    response = 'First: ```json {"a": 1} ``` Second: ```json {"b": 2} ```'
    assert _extract_json_from_response(response) == '{"a": 1}'

def test_extract_json_empty_input():
    """Test extraction from an empty string."""
    assert _extract_json_from_response("") == ""

def test_extract_json_whitespace_only():
    """Test extraction from a whitespace-only string."""
    assert _extract_json_from_response("   \n  ") == ""

def test_extract_json_unclosed_block():
    """Test extraction when a block is not properly closed (should return stripped response)."""
    response = '```json {"key": "value"}'
    assert _extract_json_from_response(response) == response.strip()
