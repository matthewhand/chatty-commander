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

"""Tests for command authoring routes module."""

import pytest

from src.chatty_commander.web.routes.command_authoring import (
    CommandAction,
    GenerateCommandRequest,
)


class TestCommandAction:
    """Tests for CommandAction model."""

    def test_valid_keypress_action(self):
        """Test creating valid keypress action."""
        action = CommandAction(type="keypress", keys="ctrl+alt+t")
        assert action.type == "keypress"
        assert action.keys == "ctrl+alt+t"

    def test_valid_url_action(self):
        """Test creating valid URL action."""
        action = CommandAction(type="url", url="https://example.com")
        assert action.type == "url"
        assert action.url == "https://example.com"

    def test_valid_shell_action(self):
        """Test creating valid shell action."""
        action = CommandAction(type="shell", cmd="ls -la")
        assert action.type == "shell"
        assert action.cmd == "ls -la"

    def test_valid_custom_message_action(self):
        """Test creating valid custom message action."""
        action = CommandAction(type="custom_message", message="Hello!")
        assert action.type == "custom_message"
        assert action.message == "Hello!"

    def test_invalid_action_type(self):
        """Test that invalid action type raises error."""
        with pytest.raises(ValueError):
            CommandAction(type="invalid", keys="ctrl+t")


class TestGenerateCommandRequest:
    """Tests for GenerateCommandRequest model."""

    def test_valid_request(self):
        """Test creating valid request."""
        request = GenerateCommandRequest(description="Open a terminal")
        assert request.description == "Open a terminal"

    def test_empty_description_raises(self):
        """Test that empty description raises error."""
        with pytest.raises(ValueError):
            GenerateCommandRequest(description="")

    def test_description_too_long(self):
        """Test that too long description raises error."""
        with pytest.raises(ValueError):
            GenerateCommandRequest(description="x" * 2001)


class TestCommandActionEdgeCases:
    """Edge case tests."""

    def test_keypress_without_keys(self):
        """Test keypress action without keys field."""
        action = CommandAction(type="keypress")
        assert action.keys is None

    def test_url_without_url(self):
        """Test url action without url field."""
        action = CommandAction(type="url")
        assert action.url is None

    def test_all_fields_none(self):
        """Test action with only type specified."""
        action = CommandAction(type="shell")
        assert action.keys is None
        assert action.url is None
        assert action.cmd is None
        assert action.message is None
