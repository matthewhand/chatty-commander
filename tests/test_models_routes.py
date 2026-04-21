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

"""Tests for models routes module."""

import pytest

from src.chatty_commander.web.routes.models import (
    DeleteResponse,
    ModelFileInfo,
    ModelListResponse,
    UploadResponse,
    _format_size,
)


class TestModelFileInfo:
    """Tests for ModelFileInfo model."""

    def test_valid_creation(self):
        """Test valid model file info creation."""
        info = ModelFileInfo(
            name="test.onnx",
            path="/models/test.onnx",
            size_bytes=1024,
            size_human="1.0 KB",
            modified="2024-01-01T00:00:00",
        )
        assert info.name == "test.onnx"
        assert info.path == "/models/test.onnx"
        assert info.size_bytes == 1024
        assert info.state is None

    def test_with_state(self):
        """Test model file info with state."""
        info = ModelFileInfo(
            name="idle.onnx",
            path="/models/idle.onnx",
            size_bytes=2048,
            size_human="2.0 KB",
            modified="2024-01-01T00:00:00",
            state="idle",
        )
        assert info.state == "idle"


class TestModelListResponse:
    """Tests for ModelListResponse model."""

    def test_empty_list(self):
        """Test empty model list response."""
        response = ModelListResponse(
            models=[],
            total_count=0,
            total_size_bytes=0,
            total_size_human="0 B",
        )
        assert response.total_count == 0
        assert response.models == []

    def test_with_models(self):
        """Test response with models."""
        model = ModelFileInfo(
            name="test.onnx",
            path="/models/test.onnx",
            size_bytes=1024,
            size_human="1.0 KB",
            modified="2024-01-01T00:00:00",
        )
        response = ModelListResponse(
            models=[model],
            total_count=1,
            total_size_bytes=1024,
            total_size_human="1.0 KB",
        )
        assert response.total_count == 1
        assert len(response.models) == 1


class TestUploadResponse:
    """Tests for UploadResponse model."""

    def test_successful_upload(self):
        """Test successful upload response."""
        response = UploadResponse(
            success=True,
            message="Upload successful",
            filename="model.onnx",
            size_bytes=1024,
        )
        assert response.success is True
        assert response.filename == "model.onnx"

    def test_failed_upload(self):
        """Test failed upload response."""
        response = UploadResponse(
            success=False,
            message="Upload failed",
            filename="model.onnx",
            size_bytes=0,
        )
        assert response.success is False


class TestDeleteResponse:
    """Tests for DeleteResponse model."""

    def test_successful_delete(self):
        """Test successful delete response."""
        response = DeleteResponse(
            success=True,
            message="File deleted",
            filename="model.onnx",
        )
        assert response.success is True
        assert response.message == "File deleted"

    def test_failed_delete(self):
        """Test failed delete response."""
        response = DeleteResponse(
            success=False,
            message="File not found",
            filename="model.onnx",
        )
        assert response.success is False


class TestFormatSize:
    """Tests for _format_size function."""

    def test_bytes(self):
        """Test formatting bytes."""
        assert _format_size(0) == "0.0 B"
        assert _format_size(512) == "512.0 B"

    def test_kilobytes(self):
        """Test formatting kilobytes."""
        assert _format_size(1024) == "1.0 KB"
        assert _format_size(1536) == "1.5 KB"

    def test_megabytes(self):
        """Test formatting megabytes."""
        assert _format_size(1024 * 1024) == "1.0 MB"

    def test_gigabytes(self):
        """Test formatting gigabytes."""
        assert _format_size(1024 * 1024 * 1024) == "1.0 GB"

    def test_terabytes(self):
        """Test formatting terabytes."""
        assert _format_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"


class TestFormatSizeEdgeCases:
    """Edge case tests for format_size."""

    def test_negative_size(self):
        """Test negative size handling."""
        # Should handle gracefully
        result = _format_size(-1)
        assert "-0.0" in result or "B" in result

    def test_very_large_size(self):
        """Test very large size."""
        result = _format_size(1024 ** 5)  # 1024 TB
        assert "TB" in result
