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
Tests for avatar animation selector API routes.

Tests animation classification endpoint.
"""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.chatty_commander.web.routes.avatar_selector import (
    AnimationChooseRequest,
    AnimationChooseResponse,
    AllowedLabel,
    router,
    _HINTS,
)


class TestAnimationChooseRequest:
    """Tests for AnimationChooseRequest model."""

    def test_creation_with_text_only(self):
        """Test creating request with just text."""
        req = AnimationChooseRequest(text="Hello world")
        assert req.text == "Hello world"
        assert req.candidate_labels is None

    def test_creation_with_candidate_labels(self):
        """Test creating request with candidate labels."""
        req = AnimationChooseRequest(
            text="Processing data",
            candidate_labels=["hacking", "success"]
        )
        assert req.text == "Processing data"
        assert req.candidate_labels == ["hacking", "success"]

    def test_text_required(self):
        """Test that text field is required."""
        with pytest.raises(Exception):
            AnimationChooseRequest()


class TestAnimationChooseResponse:
    """Tests for AnimationChooseResponse model."""

    def test_creation_with_label_only(self):
        """Test creating response with just label."""
        resp = AnimationChooseResponse(label="neutral")
        assert resp.label == "neutral"
        assert resp.confidence == 0.5
        assert resp.rationale is None

    def test_creation_with_all_fields(self):
        """Test creating response with all fields."""
        resp = AnimationChooseResponse(
            label="success",
            confidence=0.9,
            rationale="Detected success keywords"
        )
        assert resp.label == "success"
        assert resp.confidence == 0.9
        assert resp.rationale == "Detected success keywords"

    def test_default_confidence(self):
        """Test default confidence value."""
        resp = AnimationChooseResponse(label="neutral")
        assert resp.confidence == 0.5


class TestAllowedLabel:
    """Tests for AllowedLabel type."""

    def test_allowed_labels_defined(self):
        """Test that allowed labels are defined."""
        labels = [
            "excited", "calm", "curious", "warning", 
            "success", "error", "neutral", "hacking"
        ]
        for label in labels:
            # Should be valid literal values
            assert label in _HINTS.keys() or label == "neutral"


class TestHints:
    """Tests for _HINTS keyword mapping."""

    def test_hints_contains_expected_labels(self):
        """Test that hints contains expected animation labels."""
        expected_labels = ["hacking", "error", "warning", "success", "excited", "curious", "calm"]
        for label in expected_labels:
            assert label in _HINTS

    def test_hints_are_lists(self):
        """Test that each hint is a list of strings."""
        for label, keywords in _HINTS.items():
            assert isinstance(keywords, list)
            assert all(isinstance(k, str) for k in keywords)

    def test_hacking_hints(self):
        """Test hacking animation hints."""
        assert "tool" in _HINTS["hacking"]
        assert "call" in _HINTS["hacking"]
        assert "mcp" in _HINTS["hacking"]

    def test_error_hints(self):
        """Test error animation hints."""
        assert "error" in _HINTS["error"]
        assert "fail" in _HINTS["error"]

    def test_success_hints(self):
        """Test success animation hints."""
        assert "success" in _HINTS["success"]
        assert "done" in _HINTS["success"]


class TestChooseAnimationEndpoint:
    """Tests for choose_animation endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client with router."""
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_endpoint_exists(self, client):
        """Test that endpoint exists."""
        response = client.post("/avatar/animation/choose", json={"text": "test"})
        assert response.status_code in [200, 422]  # 422 if validation fails

    def test_classifies_hacking_text(self, client):
        """Test classification of hacking-related text."""
        response = client.post(
            "/avatar/animation/choose",
            json={"text": "I need to use a tool"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "hacking"
        assert data["confidence"] == 0.8

    def test_classifies_error_text(self, client):
        """Test classification of error-related text."""
        response = client.post(
            "/avatar/animation/choose",
            json={"text": "An error occurred"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "error"

    def test_classifies_success_text(self, client):
        """Test classification of success-related text."""
        response = client.post(
            "/avatar/animation/choose",
            json={"text": "Task completed successfully"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "success"

    def test_defaults_to_neutral(self, client):
        """Test that unknown text defaults to neutral."""
        response = client.post(
            "/avatar/animation/choose",
            json={"text": "Some random text without keywords"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "neutral"
        assert data["confidence"] == 0.5

    def test_respects_candidate_labels(self, client):
        """Test that candidate_labels filter is respected."""
        # Even with "error" keywords, should return neutral if error not in candidates
        response = client.post(
            "/avatar/animation/choose",
            json={"text": "error occurred", "candidate_labels": ["success", "neutral"]}
        )
        assert response.status_code == 200
        data = response.json()
        # Should be neutral since error is not in candidate labels
        assert data["label"] == "neutral"

    def test_empty_text(self, client):
        """Test handling of empty text."""
        response = client.post(
            "/avatar/animation/choose",
            json={"text": ""}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "neutral"

    def test_case_insensitive_matching(self, client):
        """Test that keyword matching is case insensitive."""
        response = client.post(
            "/avatar/animation/choose",
            json={"text": "ERROR occurred"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "error"

    def test_returns_json(self, client):
        """Test that endpoint returns JSON."""
        response = client.post(
            "/avatar/animation/choose",
            json={"text": "test"}
        )
        assert response.headers["content-type"] == "application/json"


class TestEdgeCases:
    """Edge case tests."""

    @pytest.fixture
    def client(self):
        """Create test client with router."""
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_multiple_keywords_same_label(self, client):
        """Test text with multiple keywords for same label."""
        response = client.post(
            "/avatar/animation/choose",
            json={"text": "error fail exception"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "error"

    def test_none_text_handled(self, client):
        """Test handling of None text converted to empty."""
        response = client.post(
            "/avatar/animation/choose",
            json={"text": None}
        )
        # FastAPI will reject None for required str field
        assert response.status_code in [200, 422]

    def test_invalid_candidate_labels_filtered(self, client):
        """Test that invalid candidate labels are filtered out."""
        response = client.post(
            "/avatar/animation/choose",
            json={"text": "error", "candidate_labels": ["error", "invalid_label"]}
        )
        assert response.status_code == 200
        data = response.json()
        # Should still match error since it's in candidates
        assert data["label"] == "error"
