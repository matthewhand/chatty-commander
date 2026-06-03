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

"""
Comprehensive tests for version route module.

Tests version API endpoint and VersionInfo model.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.chatty_commander.web.routes.version import (
    VersionInfo,
    get_version,
    router,
)


class TestVersionInfo:
    """Tests for VersionInfo Pydantic model."""

    def test_version_info_creation(self):
        """Test creating VersionInfo with version only."""
        info = VersionInfo(version="1.0.0")
        assert info.version == "1.0.0"
        assert info.git_sha is None

    def test_version_info_with_git_sha(self):
        """Test creating VersionInfo with git SHA."""
        info = VersionInfo(version="1.0.0", git_sha="abc123")
        assert info.version == "1.0.0"
        assert info.git_sha == "abc123"

    def test_version_info_default_git_sha(self):
        """Test that git_sha defaults to None."""
        info = VersionInfo(version="0.5.0")
        assert info.git_sha is None

    def test_version_info_validation(self):
        """Test VersionInfo field validation."""
        # Version is required
        with pytest.raises(Exception):
            VersionInfo()


class TestGetVersion:
    """Tests for get_version endpoint function."""

    @pytest.mark.asyncio
    async def test_returns_version_info(self):
        """Test that get_version returns VersionInfo."""
        result = await get_version()
        
        assert isinstance(result, VersionInfo)
        assert result.version == "0.2.0"

    @pytest.mark.asyncio
    async def test_includes_git_sha_when_available(self):
        """Test that git SHA is included when git is available."""
        mock_output = b"abc1234\n"
        
        with patch("subprocess.check_output", return_value=mock_output):
            result = await get_version()
            
            assert result.git_sha == "abc1234"

    @pytest.mark.asyncio
    async def test_handles_git_failure(self):
        """Test that git failure is handled gracefully."""
        with patch("subprocess.check_output", side_effect=Exception("git not found")):
            result = await get_version()
            
            assert result.git_sha is None
            assert result.version == "0.2.0"

    @pytest.mark.asyncio
    async def test_handles_git_not_installed(self):
        """Test handling when git is not installed."""
        with patch("subprocess.check_output", side_effect=FileNotFoundError()):
            result = await get_version()
            
            assert result.git_sha is None

    @pytest.mark.asyncio
    async def test_strips_git_sha_whitespace(self):
        """Test that git SHA whitespace is stripped."""
        mock_output = b"  abc123  \n"
        
        with patch("subprocess.check_output", return_value=mock_output):
            result = await get_version()
            
            assert result.git_sha == "abc123"


class TestVersionRouter:
    """Tests for version API router."""

    @pytest.fixture
    def client(self):
        """Create test client with version router."""
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_version_endpoint_exists(self, client):
        """Test that version endpoint exists."""
        response = client.get("/api/v1/version")
        assert response.status_code == 200

    def test_version_endpoint_returns_json(self, client):
        """Test that version endpoint returns JSON."""
        response = client.get("/api/v1/version")
        
        assert response.headers["content-type"] == "application/json"

    def test_version_endpoint_structure(self, client):
        """Test version endpoint response structure."""
        response = client.get("/api/v1/version")
        data = response.json()
        
        assert "version" in data
        assert data["version"] == "0.2.0"

    def test_version_endpoint_with_git(self, client):
        """Test version endpoint when git is available."""
        mock_output = b"def789\n"
        
        with patch("subprocess.check_output", return_value=mock_output):
            response = client.get("/api/v1/version")
            data = response.json()
            
            assert data["git_sha"] == "def789"


class TestVersionIntegration:
    """Integration tests for version module."""

    @pytest.mark.asyncio
    async def test_end_to_end_version_fetch(self):
        """Test end-to-end version fetching."""
        result = await get_version()
        
        assert result.version is not None
        assert isinstance(result.version, str)


class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_git_sha_none_when_subprocess_fails(self):
        """Test git_sha is None when subprocess fails."""
        with patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "git")):
            result = await get_version()
            assert result.git_sha is None

    @pytest.mark.asyncio
    async def test_empty_git_sha_handled(self):
        """Test empty git SHA is handled."""
        mock_output = b"\n"
        
        with patch("subprocess.check_output", return_value=mock_output):
            result = await get_version()
            assert result.git_sha == ""
