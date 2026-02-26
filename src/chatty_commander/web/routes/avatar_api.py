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
import logging
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()
logger = logging.getLogger(__name__)


_ALLOWED_EXTS = {
    ".webm",
    ".mp4",
    ".gif",
    ".png",
    ".jpg",
    ".jpeg",
    ".json",
    ".glb",
    ".gltf",
    ".wav",
    ".mp3",
}


_CATEGORY_HINTS = {
    "thinking": ["think", "thought"],
    "tool_calling": ["hack", "tool", "call", "compute", "code"],
    "responding": ["speak", "talk", "voice", "reply"],
    "error": ["error", "fail", "oops"],
    "handoff": ["handoff", "swap", "switch"],
    "processing": ["process", "work", "load", "busy"],
    "idle": ["idle", "rest", "breathe", "calm"],
}


def _default_animations_dir() -> Path:
    # Default to the avatar webui directory; callers can override via query param.
    here = Path(__file__).resolve()
    # src/chatty_commander/web/routes/avatar_api.py -> up to src/chatty_commander
    base = here.parents[2]
    candidate = base / "webui" / "avatar"
    return candidate


def _infer_category(name: str) -> str:
    lower = name.lower()
    for cat, hints in _CATEGORY_HINTS.items():
        for h in hints:
            if h in lower:
                return cat
    return "unknown"


@router.get("/avatar/animations")
async def list_animations(
    dir: str | None = Query(
        default=None, description="Directory to scan for animations (optional)"
    ),
) -> dict[str, Any]:
    try:
        root = Path(dir) if dir else _default_animations_dir()
        if not root.exists() or not root.is_dir():
            raise HTTPException(
                status_code=404, detail=f"Animations directory not found: {root}"
            )

        results: list[dict[str, Any]] = []
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            ext = p.suffix.lower()
            if ext not in _ALLOWED_EXTS:
                continue
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
                    "category": _infer_category(name),
                }
            )
        return {"root": str(root), "count": len(results), "animations": results}
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - unexpected
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/avatar/launch")
async def launch_avatar() -> dict[str, Any]:
    """Launch the PyQt5 avatar in a separate process."""
    try:
        # Get the current Python executable and project root
        python_exe = sys.executable
        project_root = Path(__file__).resolve().parents[4]  # Go up to project root

        # Command to launch the avatar
        cmd = [python_exe, "-m", "src.chatty_commander.main", "--gui"]

        logger.info(f"Launching avatar with command: {' '.join(cmd)}")
        logger.info(f"Working directory: {project_root}")

        # Launch the process in the background
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(project_root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,  # Detach from parent process
        )

        # Don't wait for the process to complete, just check if it started
        await asyncio.sleep(0.1)  # Give it a moment to start

        if process.returncode is None:  # Process is still running
            logger.info(f"Avatar process started successfully with PID: {process.pid}")
            return {
                "status": "success",
                "message": "Avatar launched successfully",
                "pid": process.pid,
            }
        else:
            # Process exited immediately, capture error
            stdout, stderr = await process.communicate()
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"Avatar process failed to start: {error_msg}")
            raise HTTPException(
                status_code=500, detail=f"Avatar failed to start: {error_msg}"
            )

    except Exception as e:
        logger.error(f"Failed to launch avatar: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to launch avatar: {str(e)}"
        ) from e
