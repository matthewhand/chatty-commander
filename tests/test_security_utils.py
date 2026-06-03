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

"""Tests for security utilities module."""

import pytest

from src.chatty_commander.utils.security import constant_time_compare, mask_sensitive_data


class TestConstantTimeCompare:
    """Tests for constant_time_compare function."""

    def test_matching_strings(self):
        """Test that matching strings return True."""
        assert constant_time_compare("secret", "secret") is True

    def test_different_strings(self):
        """Test that different strings return False."""
        assert constant_time_compare("secret", "different") is False

    def test_empty_provided(self):
        """Test that empty provided returns False."""
        assert constant_time_compare("", "secret") is False

    def test_empty_expected(self):
        """Test that empty expected returns False."""
        assert constant_time_compare("secret", "") is False

    def test_both_empty(self):
        """Test that both empty returns False."""
        assert constant_time_compare("", "") is False

    def test_none_provided(self):
        """Test that None provided returns False."""
        assert constant_time_compare(None, "secret") is False

    def test_none_expected(self):
        """Test that None expected returns False."""
        assert constant_time_compare("secret", None) is False

    def test_both_none(self):
        """Test that both None returns False."""
        assert constant_time_compare(None, None) is False

    def test_case_sensitive(self):
        """Test that comparison is case sensitive."""
        assert constant_time_compare("Secret", "secret") is False

    def test_different_lengths(self):
        """Test that different length strings return False."""
        assert constant_time_compare("short", "longer string") is False


class TestMaskSensitiveData:
    """Tests for mask_sensitive_data function."""

    def test_simple_api_key(self):
        """Test masking simple API key."""
        data = {"api_key": "secret123"}
        result = mask_sensitive_data(data)
        assert result["api_key"] == "********"

    def test_simple_password(self):
        """Test masking password."""
        data = {"password": "mysecret"}
        result = mask_sensitive_data(data)
        assert result["password"] == "********"

    def test_token(self):
        """Test masking token."""
        data = {"token": "bearer123"}
        result = mask_sensitive_data(data)
        assert result["token"] == "********"

    def test_nested_dict(self):
        """Test masking in nested dictionary."""
        data = {
            "config": {
                "api_key": "secret",
                "normal_key": "visible",
            }
        }
        result = mask_sensitive_data(data)
        assert result["config"]["api_key"] == "********"
        assert result["config"]["normal_key"] == "visible"

    def test_list_of_dicts(self):
        """Test masking in list of dictionaries."""
        data = [
            {"api_key": "secret1"},
            {"api_key": "secret2"},
        ]
        result = mask_sensitive_data(data)
        assert result[0]["api_key"] == "********"
        assert result[1]["api_key"] == "********"

    def test_mixed_data(self):
        """Test masking mixed data structure."""
        data = {
            "users": [
                {"name": "Alice", "password": "alice123"},
                {"name": "Bob", "secret": "bob123"},
            ],
            "api_key": "master_key",
        }
        result = mask_sensitive_data(data)
        assert result["users"][0]["password"] == "********"
        assert result["users"][0]["name"] == "Alice"
        assert result["users"][1]["secret"] == "********"
        assert result["api_key"] == "********"

    def test_auth_dict(self):
        """Test that auth dict contents are masked."""
        data = {
            "auth": {
                "username": "admin",
                "password": "secret",
            }
        }
        result = mask_sensitive_data(data)
        assert result["auth"]["password"] == "********"

    def test_auth_non_dict(self):
        """Test that non-dict auth value is masked."""
        data = {"auth": "bearer_token_string"}
        result = mask_sensitive_data(data)
        assert result["auth"] == "********"

    def test_non_sensitive_keys_preserved(self):
        """Test that non-sensitive keys are preserved."""
        data = {
            "name": "test",
            "value": 123,
            "enabled": True,
            "items": [1, 2, 3],
        }
        result = mask_sensitive_data(data)
        assert result["name"] == "test"
        assert result["value"] == 123
        assert result["enabled"] is True
        assert result["items"] == [1, 2, 3]

    def test_various_sensitive_patterns(self):
        """Test various sensitive key patterns."""
        data = {
            "api_token": "token1",
            "access_token": "token2",
            "auth_token": "token3",
            "bridge_token": "token4",
            "database_url": "postgres://...",
        }
        result = mask_sensitive_data(data)
        for key in data:
            assert result[key] == "********"

    def test_empty_dict(self):
        """Test with empty dictionary."""
        data = {}
        result = mask_sensitive_data(data)
        assert result == {}

    def test_empty_list(self):
        """Test with empty list."""
        data = []
        result = mask_sensitive_data(data)
        assert result == []

    def test_primitive_values(self):
        """Test with primitive values."""
        assert mask_sensitive_data("string") == "string"
        assert mask_sensitive_data(123) == 123
        assert mask_sensitive_data(None) is None
        assert mask_sensitive_data(True) is True
