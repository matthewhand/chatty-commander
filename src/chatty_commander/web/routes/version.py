from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field


class VersionInfo(BaseModel):
    version: str = Field(..., description="Application semantic version")
    git_sha: str | None = Field(default=None, description="Short git commit SHA if available")


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
