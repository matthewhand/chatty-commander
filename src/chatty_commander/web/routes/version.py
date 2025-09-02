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

from fastapi import APIRouter
from pydantic import BaseModel, Field


class VersionInfo(BaseModel):
    version: str = Field(..., description="Application semantic version")
    git_sha: str | None = Field(
        default=None, description="Short git commit SHA if available"
    )


router = APIRouter()


@router.get("/api/v1/version", response_model=VersionInfo)
async def get_version() -> VersionInfo:
    # Base version should come from a single source of truth if available
    # Here we mirror the SystemStatus default to keep tests stable.
    base_version = "0.2.0"

    git_sha: str | None = None
    try:  # best-effort; avoid failing when git is unavailable
        import subprocess

        git_sha = (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        git_sha = None

    return VersionInfo(version=base_version, git_sha=git_sha)
