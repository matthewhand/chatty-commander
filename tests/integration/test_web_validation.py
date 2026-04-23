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

"""Tests for web validation module."""

import uuid

import pytest
from fastapi import HTTPException

from src.chatty_commander.web.validation import ValidationError, validate_uuid


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_validation_error_is_exception(self):
        """Test that ValidationError is an Exception."""
        err = ValidationError("test message")
        assert isinstance(err, Exception)
        assert str(err) == "test message"


class TestValidateUUID:
    """Tests for validate_uuid function."""

    def test_valid_uuid_v4(self):
        """Test validating a valid UUID v4."""
        valid_uuid = str(uuid.uuid4())
        result = validate_uuid(valid_uuid)
        assert result == valid_uuid

    def test_valid_uuid_v1(self):
        """Test validating a valid UUID v1."""
        valid_uuid = str(uuid.uuid1())
        result = validate_uuid(valid_uuid)
        assert result == valid_uuid

    def test_empty_string_raises(self):
        """Test that empty string raises HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            validate_uuid("")
        assert exc_info.value.status_code == 400
        assert "cannot be empty" in exc_info.value.detail

    def test_invalid_uuid_raises(self):
        """Test that invalid UUID raises HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            validate_uuid("not-a-uuid")
        assert exc_info.value.status_code == 400
        assert "must be a valid UUID" in exc_info.value.detail

    def test_custom_field_name_in_error(self):
        """Test that custom field name appears in error."""
        with pytest.raises(HTTPException) as exc_info:
            validate_uuid("invalid", field_name="Agent ID")
        assert "agent id" in exc_info.value.detail.lower()

    def test_malformed_uuid(self):
        """Test various malformed UUIDs."""
        malformed = [
            "12345",
            "uuid-1234-5678",
            "gibberish",
            "123e4567-e89b-12d3-a456-42661417400g",  # invalid char 'g'
        ]
        for invalid in malformed:
            with pytest.raises(HTTPException):
                validate_uuid(invalid)

    def test_uuid_with_whitespace_raises(self):
        """Test that UUID with whitespace raises error."""
        with pytest.raises(HTTPException):
            validate_uuid("  " + str(uuid.uuid4()))


class TestValidateUUIDEdgeCases:
    """Edge case tests for UUID validation."""

    def test_none_raises_error(self):
        """Test that None raises error (though type hint expects str)."""
        # uuid.UUID(None) would raise TypeError
        with pytest.raises((HTTPException, TypeError)):
            validate_uuid(None)  # type: ignore

    def test_uppercase_uuid(self):
        """Test that uppercase UUID works."""
        valid_uuid = str(uuid.uuid4()).upper()
        result = validate_uuid(valid_uuid)
        assert result.lower() == valid_uuid.lower()

    def test_different_uuid_versions(self):
        """Test various UUID versions."""
        versions = [
            uuid.uuid1(),
            uuid.uuid3(uuid.NAMESPACE_DNS, "test"),
            uuid.uuid4(),
            uuid.uuid5(uuid.NAMESPACE_DNS, "test"),
        ]
        for u in versions:
            result = validate_uuid(str(u))
            assert result == str(u)
