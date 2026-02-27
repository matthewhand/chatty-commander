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

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger(__name__)


def ensure_dir(path: Path) -> None:
    """
    Ensure the directory exists.
    """
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: dict[str, Any]) -> None:
    """
    Write a JSON file with pretty formatting.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def write_text(path: Path, data: str) -> None:
    """
    Write a text file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")


def scan_directory(
    root: Path, extensions: Iterable[str] | None = None
) -> list[dict[str, Any]]:
    """
    Synchronously scan a directory recursively for files with matching extensions.
    Returns a list of dictionaries with file metadata:
      - name: file stem
      - file: path relative to root (posix style)
      - ext: file suffix (lowercase)
      - size: file size in bytes (or None on error)
    """
    results: list[dict[str, Any]] = []
    if not root.exists() or not root.is_dir():
        return results

    allowed = set(ext.lower() for ext in extensions) if extensions else None

    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if allowed and ext not in allowed:
            continue

        try:
            rel = p.relative_to(root)
            name = p.stem
            try:
                size = p.stat().st_size
            except Exception:
                size = None

            results.append(
                {
                    "name": name,
                    "file": str(rel).replace("\\", "/"),
                    "ext": ext,
                    "size": size,
                }
            )
        except Exception as e:
            logger.debug(f"Error processing file {p}: {e}")
            continue

    return results
