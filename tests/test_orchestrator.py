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

"""Tests for orchestrator module."""

from unittest.mock import MagicMock

import pytest

from src.chatty_commander.app.orchestrator import (
    DummyAdapter,
    OrchestratorFlags,
    TextInputAdapter,
)


class TestOrchestratorFlags:
    """Tests for OrchestratorFlags dataclass."""

    def test_default_values(self):
        """Test default flag values."""
        flags = OrchestratorFlags()
        assert flags.enable_text is False
        assert flags.enable_gui is False
        assert flags.enable_web is False
        assert flags.enable_openwakeword is False
        assert flags.enable_computer_vision is False
        assert flags.enable_discord_bridge is False

    def test_custom_values(self):
        """Test setting custom flag values."""
        flags = OrchestratorFlags(
            enable_text=True,
            enable_gui=True,
            enable_web=True,
        )
        assert flags.enable_text is True
        assert flags.enable_gui is True
        assert flags.enable_web is True


class TestDummyAdapter:
    """Tests for DummyAdapter."""

    def test_initialization(self):
        """Test adapter initialization."""
        adapter = DummyAdapter("test_adapter")
        assert adapter.name == "test_adapter"
        assert adapter._started is False

    def test_start(self):
        """Test starting adapter."""
        adapter = DummyAdapter("test")
        adapter.start()
        assert adapter._started is True

    def test_stop(self):
        """Test stopping adapter."""
        adapter = DummyAdapter("test")
        adapter.start()
        adapter.stop()
        assert adapter._started is False

    def test_stop_without_start(self):
        """Test stopping without starting."""
        adapter = DummyAdapter("test")
        adapter.stop()
        assert adapter._started is False


class TestTextInputAdapter:
    """Tests for TextInputAdapter."""

    def test_initialization(self):
        """Test adapter initialization."""
        callback = MagicMock()
        adapter = TextInputAdapter(callback)
        assert adapter._on_command == callback
        assert adapter._started is False
        assert adapter.name == "text"

    def test_start(self):
        """Test starting adapter."""
        callback = MagicMock()
        adapter = TextInputAdapter(callback)
        adapter.start()
        assert adapter._started is True

    def test_stop(self):
        """Test stopping adapter."""
        callback = MagicMock()
        adapter = TextInputAdapter(callback)
        adapter.start()
        adapter.stop()
        assert adapter._started is False

    def test_feed_when_started(self):
        """Test feed method when started."""
        callback = MagicMock()
        adapter = TextInputAdapter(callback)
        adapter.start()
        adapter.feed("test command")
        callback.assert_called_once_with("test command")

    def test_feed_when_not_started(self):
        """Test feed method when not started."""
        callback = MagicMock()
        adapter = TextInputAdapter(callback)
        adapter.feed("test command")
        callback.assert_not_called()

    def test_feed_multiple(self):
        """Test multiple feed calls."""
        callback = MagicMock()
        adapter = TextInputAdapter(callback)
        adapter.start()
        adapter.feed("command 1")
        adapter.feed("command 2")
        adapter.feed("command 3")
        assert callback.call_count == 3


class TestTextInputAdapterEdgeCases:
    """Edge case tests."""

    def test_feed_empty_string(self):
        """Test feeding empty string."""
        callback = MagicMock()
        adapter = TextInputAdapter(callback)
        adapter.start()
        adapter.feed("")
        callback.assert_called_once_with("")

    def test_feed_special_characters(self):
        """Test feeding special characters."""
        callback = MagicMock()
        adapter = TextInputAdapter(callback)
        adapter.start()
        adapter.feed("hello! @#$%")
        callback.assert_called_once_with("hello! @#$%")
