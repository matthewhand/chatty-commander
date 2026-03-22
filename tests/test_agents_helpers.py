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

# Mock fastapi and pydantic before importing the module under test
import pytest

# We should use unittest.mock.patch.dict instead of a global module assignment,
# as global sys.modules modification leaks to all other tests that pytest collects.

@pytest.fixture(autouse=True)
def mock_fastapi_and_pydantic():
    from unittest.mock import patch
    with patch.dict(sys.modules, {"fastapi": MagicMock(), "pydantic": MagicMock()}):
        yield

# Import late to avoid the module evaluating before the fixture patches sys.modules?
# Wait, actually _extract_json_from_response doesn't even need those modules
# but if the file imports it, it's evaluated at module level during collection.
# Wait, let's just mock them around the import of the function.
import importlib

def get_extract_json():
    from unittest.mock import patch
    with patch.dict(sys.modules, {"fastapi": MagicMock(), "pydantic": MagicMock()}):
        import chatty_commander.web.routes.agents as agents_mod
        return agents_mod._extract_json_from_response

def test_extract_json_standard_markdown():
    _extract_json_from_response = get_extract_json()
    """Test extraction from a standard ```json ... ``` block."""
    response = 'Here is the JSON: ```json {"key": "value"} ```'
    assert _extract_json_from_response(response) == '{"key": "value"}'

def test_extract_json_generic_markdown():
    _extract_json_from_response = get_extract_json()
    """Test extraction from a generic ``` ... ``` block."""
    response = 'Some data: ``` {"key": "value"} ```'
    assert _extract_json_from_response(response) == '{"key": "value"}'

def test_extract_json_plain_text():
    _extract_json_from_response = get_extract_json()
    """Test extraction from a response without markdown blocks."""
    response = '{"key": "value"}'
    assert _extract_json_from_response(response) == '{"key": "value"}'

def test_extract_json_with_whitespace():
    _extract_json_from_response = get_extract_json()
    """Test extraction with extra whitespace and newlines."""
    response = '\n  ```json\n  {"key": "value"}\n  ```  \n'
    assert _extract_json_from_response(response) == '{"key": "value"}'

def test_extract_json_text_around_block():
    _extract_json_from_response = get_extract_json()
    """Test extraction when there is text before and after the code block."""
    response = 'Prefix text\n```json\n{"key": "value"}\n```\nSuffix text'
    assert _extract_json_from_response(response) == '{"key": "value"}'

def test_extract_json_multiple_blocks():
    _extract_json_from_response = get_extract_json()
    """Test extraction when there are multiple code blocks (should pick the first)."""
    # Current implementation uses re.search which finds the first match
    response = 'First: ```json {"a": 1} ``` Second: ```json {"b": 2} ```'
    assert _extract_json_from_response(response) == '{"a": 1}'

def test_extract_json_empty_input():
    _extract_json_from_response = get_extract_json()
    """Test extraction from an empty string."""
    assert _extract_json_from_response("") == ""

def test_extract_json_whitespace_only():
    _extract_json_from_response = get_extract_json()
    """Test extraction from a whitespace-only string."""
    assert _extract_json_from_response("   \n  ") == ""

def test_extract_json_unclosed_block():
    _extract_json_from_response = get_extract_json()
    """Test extraction when a block is not properly closed (should return stripped response)."""
    response = '```json {"key": "value"}'
    assert _extract_json_from_response(response) == response.strip()
