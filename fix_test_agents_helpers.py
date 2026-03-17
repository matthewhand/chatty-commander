import re
with open("tests/test_agents_helpers.py", "r") as f:
    content = f.read()

content = content.replace("# sys.modules[\"fastapi\"] = mock_fastapi", "")
content = content.replace("# sys.modules[\"pydantic\"] = mock_pydantic", "")

# Let's fix the mocking properly
new_content = """# MIT License
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

# The module under test (chatty_commander.web.routes.agents) only imports things that don't need
# global mock injection if we are just testing the helper functions that have no dependencies.
# We will just import the helper directly. If the import fails due to missing FastAPI,
# we temporarily mock it just for the import.

try:
    from chatty_commander.web.routes.agents import _extract_json_from_response
except ImportError:
    mock_fastapi = MagicMock()
    mock_pydantic = MagicMock()

    # Save original
    orig_fastapi = sys.modules.get("fastapi")
    orig_pydantic = sys.modules.get("pydantic")

    try:
        sys.modules["fastapi"] = mock_fastapi
        sys.modules["pydantic"] = mock_pydantic
        from chatty_commander.web.routes.agents import _extract_json_from_response
    finally:
        # Restore
        if orig_fastapi:
            sys.modules["fastapi"] = orig_fastapi
        else:
            del sys.modules["fastapi"]

        if orig_pydantic:
            sys.modules["pydantic"] = orig_pydantic
        else:
            del sys.modules["pydantic"]

import pytest

def test_extract_json_standard_markdown():
    \"\"\"Test extraction from a standard ```json ... ``` block.\"\"\"
    response = 'Here is the JSON: ```json {"key": "value"} ```'
    assert _extract_json_from_response(response) == '{"key": "value"}'

def test_extract_json_generic_markdown():
    \"\"\"Test extraction from a generic ``` ... ``` block.\"\"\"
    response = 'Some data: ``` {"key": "value"} ```'
    assert _extract_json_from_response(response) == '{"key": "value"}'

def test_extract_json_plain_text():
    \"\"\"Test extraction from a response without markdown blocks.\"\"\"
    response = '{"key": "value"}'
    assert _extract_json_from_response(response) == '{"key": "value"}'

def test_extract_json_with_whitespace():
    \"\"\"Test extraction with extra whitespace and newlines.\"\"\"
    response = '\\n  ```json\\n  {"key": "value"}\\n  ```  \\n'
    assert _extract_json_from_response(response) == '{"key": "value"}'

def test_extract_json_text_around_block():
    \"\"\"Test extraction when there is text before and after the code block.\"\"\"
    response = 'Prefix text\\n```json\\n{"key": "value"}\\n```\\nSuffix text'
    assert _extract_json_from_response(response) == '{"key": "value"}'

def test_extract_json_multiple_blocks():
    \"\"\"Test extraction when there are multiple code blocks (should pick the first).\"\"\"
    # Current implementation uses re.search which finds the first match
    response = 'First: ```json {"a": 1} ``` Second: ```json {"b": 2} ```'
    assert _extract_json_from_response(response) == '{"a": 1}'

def test_extract_json_empty_input():
    \"\"\"Test extraction from an empty string.\"\"\"
    assert _extract_json_from_response("") == ""

def test_extract_json_whitespace_only():
    \"\"\"Test extraction from a whitespace-only string.\"\"\"
    assert _extract_json_from_response("   \\n  ") == ""

def test_extract_json_unclosed_block():
    \"\"\"Test extraction when a block is not properly closed (should return stripped response).\"\"\"
    response = '```json {"key": "value"}'
    assert _extract_json_from_response(response) == response.strip()
"""

with open("tests/test_agents_helpers.py", "w") as f:
    f.write(new_content)
