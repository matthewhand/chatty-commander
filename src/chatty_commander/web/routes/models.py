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

"""Model file management routes for ONNX voice command models."""

from __future__ import annotations

import logging
from datetime import datetime
import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ModelFileInfo(BaseModel):
    """Information about a model file."""

    name: str = Field(..., description="Filename of the model")
    path: str = Field(..., description="Full path to the model file")
    size_bytes: int = Field(..., description="File size in bytes")
    size_human: str = Field(..., description="Human-readable file size")
    modified: str = Field(..., description="Last modification timestamp")
    state: str | None = Field(default=None, description="Associated state (idle/computer/chatty)")


class ModelListResponse(BaseModel):
    """Response for listing model files."""

    models: list[ModelFileInfo] = Field(default_factory=list, description="List of model files")
    total_count: int = Field(..., description="Total number of models")
    total_size_bytes: int = Field(..., description="Total size in bytes")
    total_size_human: str = Field(..., description="Human-readable total size")


class UploadResponse(BaseModel):
    """Response for file upload."""

    success: bool = Field(..., description="Whether upload was successful")
    message: str = Field(..., description="Status message")
    filename: str = Field(..., description="Uploaded filename")
    size_bytes: int = Field(..., description="File size in bytes")


class DeleteResponse(BaseModel):
    """Response for file deletion."""

    success: bool = Field(..., description="Whether deletion was successful")
    message: str = Field(..., description="Status message")
    filename: str = Field(..., description="Deleted filename")


# Default model directories
DEFAULT_MODEL_DIRS = ["models-idle", "models-computer", "models-chatty", "wakewords"]


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _get_model_dirs() -> list[Path]:
    """Get list of model directories to scan."""
    # Check for model directories in current working directory
    dirs = []
    for dir_name in DEFAULT_MODEL_DIRS:
        path = Path(dir_name)
        if path.exists() and path.is_dir():
            dirs.append(path)
    return dirs


def _scan_model_files() -> list[ModelFileInfo]:
    """Scan all model directories for ONNX files."""
    models = []
    model_dirs = _get_model_dirs()

    for model_dir in model_dirs:
        # Determine state from directory name
        dir_name = model_dir.name
        if "idle" in dir_name:
            state = "idle"
        elif "computer" in dir_name:
            state = "computer"
        elif "chatty" in dir_name:
            state = "chatty"
        else:
            state = None

        # Scan for ONNX files
        for file_path in model_dir.glob("*.onnx"):
            try:
                stat = file_path.stat()
                models.append(ModelFileInfo(
                    name=file_path.name,
                    path=str(file_path),
                    size_bytes=stat.st_size,
                    size_human=_format_size(stat.st_size),
                    modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    state=state,
                ))
            except OSError:
                continue

    return models


def create_models_router(upload_dir: str = "wakewords") -> APIRouter:
    """Create router for model file management.

    Args:
        upload_dir: Directory to upload new models to (default: wakewords)

    Returns:
        FastAPI router with model management endpoints
    """
    router = APIRouter(prefix="/api/v1/models", tags=["models"])

    @router.get("/files", response_model=ModelListResponse)
    async def list_model_files():
        """List all available ONNX model files."""
        models = _scan_model_files()
        total_size = sum(m.size_bytes for m in models)

        return ModelListResponse(
            models=models,
            total_count=len(models),
            total_size_bytes=total_size,
            total_size_human=_format_size(total_size),
        )

    @router.post("/upload", response_model=UploadResponse)
    async def upload_model_file(
        file: UploadFile = File(...),
        state: str | None = None,
    ):
        """Upload a new ONNX model file.

        Args:
            file: The uploaded file
            state: Optional state to associate (idle/computer/chatty)

        Returns:
            Upload confirmation
        """
        # Validate file extension
        if not file.filename or not file.filename.lower().endswith(".onnx"):
            raise HTTPException(
                status_code=400,
                detail="Only ONNX files (.onnx) are allowed"
            )

        # Determine target directory
        if state and state in ["idle", "computer", "chatty"]:
            target_dir = Path(f"models-{state}")
        else:
            target_dir = Path(upload_dir)

        # Create directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize filename to prevent path traversal attacks
        # Use only the basename (strip any directory components)
        safe_filename = Path(file.filename).name
        if not safe_filename or safe_filename != file.filename:
            raise HTTPException(
                status_code=400,
                detail="Invalid filename: directory traversal not allowed"
            )

        # Save file
        file_path = target_dir / safe_filename

        # Verify the resolved path is still within the target directory
        try:
            file_path.resolve().relative_to(target_dir.resolve())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid filename: path escapes target directory"
            )

        # Check if file already exists
        if file_path.exists():
            raise HTTPException(
                status_code=409,
                detail=f"File '{safe_filename}' already exists. Delete it first to replace."
            )

        try:
            # Write file
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            return UploadResponse(
                success=True,
                message=f"Model '{safe_filename}' uploaded successfully to {target_dir}",
                filename=safe_filename,
                size_bytes=len(content),
            )
        except Exception as e:
            logger.error("Failed to save uploaded model file: %s", e)
            raise HTTPException(
                status_code=500,
                detail="Failed to save file. Check server logs for details."
            ) from e

    @router.get("/download/{filename}")
    async def download_model_file(filename: str):
        """Download an ONNX model file.

        Args:
            filename: Name of the file to download

        Returns:
            File download response
        """
        # Find the file in model directories
        models = _scan_model_files()
        matching = [m for m in models if m.name == filename]

        if not matching:
            raise HTTPException(
                status_code=404,
                detail=f"Model file '{filename}' not found"
            )

        file_path = Path(matching[0].path)

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Model file '{filename}' not found"
            )

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream",
        )

    @router.delete("/files/{filename}", response_model=DeleteResponse)
    async def delete_model_file(filename: str):
        """Delete an ONNX model file.

        Args:
            filename: Name of the file to delete

        Returns:
            Deletion confirmation
        """
        # Find the file in model directories
        models = _scan_model_files()
        matching = [m for m in models if m.name == filename]

        if not matching:
            raise HTTPException(
                status_code=404,
                detail=f"Model file '{filename}' not found"
            )

        file_path = Path(matching[0].path)

        try:
            file_path.unlink()
            return DeleteResponse(
                success=True,
                message=f"Model '{filename}' deleted successfully",
                filename=filename,
            )
        except Exception as e:
            logger.error("Failed to delete model file '%s': %s", filename, e)
            raise HTTPException(
                status_code=500,
                detail="Failed to delete file. Check server logs for details."
            ) from e

    @router.get("/directories")
    async def list_model_directories():
        """List available model directories."""
        dirs = _get_model_dirs()
        return {
            "directories": [
                {
                    "name": d.name,
                    "path": str(d),
                    "state": "idle" if "idle" in d.name
                    else "computer" if "computer" in d.name
                    else "chatty" if "chatty" in d.name
                    else None,
                }
                for d in dirs
            ]
        }

    return router


# Create default router instance
router = create_models_router()
