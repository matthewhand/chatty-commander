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

import json
from pathlib import Path

from chatty_commander.web.web_mode import create_app


def test_runtime_openapi_matches_docs_file_on_key_paths():
    """
    Parity check: ensure key API paths exist in both runtime schema and docs/openapi.json.
    This is a tolerant check to avoid flakiness when non-key paths change.
    """
    app = create_app(no_auth=True)
    runtime = app.openapi()

    docs_path = Path("docs/openapi.json")
    assert (
        docs_path.is_file()
    ), "docs/openapi.json is missing; generate with make api-docs"
    docs_schema = json.loads(docs_path.read_text(encoding="utf-8"))

    assert "paths" in runtime and isinstance(runtime["paths"], dict)
    assert "paths" in docs_schema and isinstance(docs_schema["paths"], dict)

    runtime_paths = set(runtime["paths"].keys())
    docs_paths = set(docs_schema["paths"].keys())

    # Key endpoints we expect to exist in both
    key = {
        "/api/v1/health",
        "/api/v1/status",
        "/api/v1/config",
        "/api/v1/state",
        "/api/v1/command",
    }

    missing_in_runtime = key - runtime_paths
    missing_in_docs = key - docs_paths

    assert (
        not missing_in_runtime
    ), f"Runtime schema missing key paths: {sorted(missing_in_runtime)}"
    assert (
        not missing_in_docs
    ), f"docs/openapi.json missing key paths: {sorted(missing_in_docs)}"
