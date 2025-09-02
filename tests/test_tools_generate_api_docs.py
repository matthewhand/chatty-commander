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

import importlib
import json
import os
import runpy
from pathlib import Path
from typing import Any


def _run_generator_in(tmp_path: Path) -> Path:
    """
    Execute the docs generator module in a temporary working directory, but avoid
    letting sys.exit(0) Bubble out as a test failure. We catch SystemExit and
    continue, since the tool is a CLI script that exits(0) on success.
    """
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        Path("docs").mkdir(parents=True, exist_ok=True)
        mod_name = "chatty_commander.tools.generate_api_docs"
        spec = importlib.util.find_spec(mod_name)
        assert spec is not None, f"Module {mod_name} not found"
        try:
            # Execute the module as a script (equivalent to: python -m ...)
            runpy.run_module(mod_name, run_name="__main__")
        except SystemExit as e:
            # Accept 0 (success) and re-raise non-zero to surface real failures
            if getattr(e, "code", 0) not in (0, None):
                raise
        return tmp_path / "docs"
    finally:
        os.chdir(old_cwd)


def test_generate_api_docs_creates_expected_files(tmp_path: Path):
    docs_dir = _run_generator_in(tmp_path)

    openapi = docs_dir / "openapi.json"
    api_md = docs_dir / "API.md"
    readme_md = docs_dir / "README.md"

    assert openapi.is_file(), "docs/openapi.json not created"
    assert api_md.is_file(), "docs/API.md not created"
    assert readme_md.is_file(), "docs/README.md not created"

    data: Any
    data = json.loads(openapi.read_text(encoding="utf-8"))
    assert "openapi" in data, "openapi version missing"
    assert "paths" in data and isinstance(data["paths"], dict), "paths section missing"
    assert len(data["paths"]) > 0, "no API paths found in schema"


def test_generate_api_docs_is_idempotent(tmp_path: Path):
    docs_dir = _run_generator_in(tmp_path)
    # Run again should not error and should still produce valid JSON
    docs_dir = _run_generator_in(tmp_path)

    openapi = docs_dir / "openapi.json"
    data = json.loads(openapi.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "openapi" in data and "paths" in data
