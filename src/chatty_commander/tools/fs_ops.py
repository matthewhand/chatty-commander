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

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

import aiofiles
import aiofiles.os


def ensure_dir(path: Path) -> None:
    """
    Ensure the directory exists.
    """
    path.mkdir(parents=True, exist_ok=True)


async def ensure_dir_async(path: Path) -> None:
    """
    Ensure the directory exists asynchronously.
    """
    await aiofiles.os.makedirs(path, exist_ok=True)


def write_json(path: Path, data: dict[str, Any]) -> None:
    """
    Write a JSON file with pretty formatting.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


async def write_json_async(path: Path, data: dict[str, Any]) -> None:
    """
    Write a JSON file asynchronously with pretty formatting.
    """
    path = Path(path)
    await ensure_dir_async(path.parent)
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, indent=2))


def write_text(path: Path, data: str) -> None:
    """
    Write a text file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(data)


async def write_text_async(path: Path, data: str) -> None:
    """
    Write a text file asynchronously.
    """
    path = Path(path)
    await ensure_dir_async(path.parent)
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(data)


def write_atomic_json(path: Path, data: dict[str, Any]) -> None:
    """
    Write a JSON file atomically.
    Writes to a temporary file first, then renames it to the target path.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create temp file in same directory to ensure atomic rename is possible
    temp_fd, temp_path = tempfile.mkstemp(dir=path.parent, text=True)
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is on disk

        os.replace(temp_path, path)
    except Exception:
        # Clean up temp file if something goes wrong
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def write_atomic_text(path: Path, data: str) -> None:
    """
    Write a text file atomically.
    Writes to a temporary file first, then renames it to the target path.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create temp file in same directory to ensure atomic rename is possible
    temp_fd, temp_path = tempfile.mkstemp(dir=path.parent, text=True)
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is on disk

        os.replace(temp_path, path)
    except Exception:
        # Clean up temp file if something goes wrong
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
