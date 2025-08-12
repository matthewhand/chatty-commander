from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


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
    "idle": ["idle", "rest", "breath", "calm"],
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
    dir: str | None = Query(default=None, description="Directory to scan for animations (optional)")
) -> dict[str, Any]:
    try:
        root = Path(dir) if dir else _default_animations_dir()
        if not root.exists() or not root.is_dir():
            raise HTTPException(status_code=404, detail=f"Animations directory not found: {root}")

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
