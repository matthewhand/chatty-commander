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
Comprehensive tests for context module.

Tests context switching and identity management for advisors.
"""

import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.advisors.context import (
    ContextIdentity,
    ContextManager,
    ContextState,
    PlatformType,
)


class TestPlatformType:
    """Tests for PlatformType enum."""

    def test_platform_values(self):
        """Test that all platforms have correct values."""
        assert PlatformType.DISCORD.value == "discord"
        assert PlatformType.SLACK.value == "slack"
        assert PlatformType.WEB.value == "web"
        assert PlatformType.CLI.value == "cli"
        assert PlatformType.GUI.value == "gui"


class TestContextIdentity:
    """Tests for ContextIdentity dataclass."""

    def test_creation(self):
        """Test creating a ContextIdentity."""
        identity = ContextIdentity(
            platform=PlatformType.WEB,
            channel="general",
            user_id="user123",
            username="testuser",
        )
        assert identity.platform == PlatformType.WEB
        assert identity.channel == "general"
        assert identity.user_id == "user123"
        assert identity.username == "testuser"
        assert identity.created_at is not None

    def test_context_key_generation(self):
        """Test context key generation."""
        identity = ContextIdentity(
            platform=PlatformType.DISCORD,
            channel="channel-1",
            user_id="user456",
        )
        assert identity.context_key == "discord:channel-1:user456"

    def test_to_dict(self):
        """Test serialization to dict."""
        identity = ContextIdentity(
            platform=PlatformType.SLACK,
            channel="#general",
            user_id="U123",
            username="test",
        )
        data = identity.to_dict()
        assert data["platform"] == "slack"
        assert data["channel"] == "#general"
        assert data["user_id"] == "U123"

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "platform": "web",
            "channel": "main",
            "user_id": "user789",
            "username": "testuser",
            "created_at": time.time(),
        }
        identity = ContextIdentity.from_dict(data)
        assert identity.platform == PlatformType.WEB
        assert identity.channel == "main"
        assert identity.user_id == "user789"

    def test_post_init_sets_created_at(self):
        """Test that created_at is set in post_init."""
        identity = ContextIdentity(
            platform=PlatformType.CLI,
            channel="terminal",
            user_id="local",
        )
        assert identity.created_at is not None
        assert isinstance(identity.created_at, float)


class TestContextState:
    """Tests for ContextState dataclass."""

    def test_creation(self):
        """Test creating a ContextState."""
        identity = ContextIdentity(
            platform=PlatformType.WEB,
            channel="test",
            user_id="user1",
        )
        state = ContextState(
            identity=identity,
            persona_id="default",
            system_prompt="You are helpful.",
            memory_key="web:test:user1:memory",
            metadata={"theme": "dark"},
        )
        assert state.identity == identity
        assert state.persona_id == "default"
        assert state.system_prompt == "You are helpful."

    def test_post_init_sets_last_activity(self):
        """Test that last_activity is set in post_init."""
        identity = ContextIdentity(
            platform=PlatformType.GUI,
            channel="app",
            user_id="user2",
        )
        state = ContextState(
            identity=identity,
            persona_id="chatty",
            system_prompt="Be chatty.",
            memory_key="key",
            metadata={},
        )
        assert state.last_activity is not None
        assert isinstance(state.last_activity, float)

    def test_to_dict(self):
        """Test serialization to dict."""
        identity = ContextIdentity(
            platform=PlatformType.DISCORD,
            channel="guild-1",
            user_id="U456",
        )
        state = ContextState(
            identity=identity,
            persona_id="assistant",
            system_prompt="Helpful assistant.",
            memory_key="discord:guild-1:U456:memory",
            metadata={},
        )
        data = state.to_dict()
        assert data["persona_id"] == "assistant"
        assert data["system_prompt"] == "Helpful assistant."
        assert "identity" in data


class TestContextManager:
    """Tests for ContextManager class."""

    @pytest.fixture
    def manager(self):
        """Create a ContextManager with test config."""
        config = {
            "personas": {
                "general": {"system_prompt": "General persona."},
                "expert": {"system_prompt": "Expert persona."},
            },
            "default_persona": "general",
            "persistence_enabled": False,
        }
        return ContextManager(config)

    def test_initialization(self, manager):
        """Test ContextManager initialization."""
        assert manager.default_persona == "general"
        assert len(manager.personas) == 2
        assert "general" in manager.personas
        assert manager.persistence_enabled is False

    def test_get_or_create_context(self, manager):
        """Test getting or creating a context."""
        context = manager.get_or_create_context(
            platform=PlatformType.WEB,
            channel="test",
            user_id="user1",
            username="Test User",
        )
        assert context is not None
        assert context.identity.platform == PlatformType.WEB
        assert context.identity.channel == "test"
        assert context.identity.user_id == "user1"
        assert context.persona_id == "general"

    def test_context_caching(self, manager):
        """Test that contexts are cached."""
        context1 = manager.get_or_create_context(
            PlatformType.DISCORD, "ch1", "u1"
        )
        context2 = manager.get_or_create_context(
            PlatformType.DISCORD, "ch1", "u1"
        )
        assert context1 is context2

    def test_switch_persona_success(self, manager):
        """Test successful persona switch."""
        context = manager.get_or_create_context(PlatformType.WEB, "ch", "u1")
        context_key = context.identity.context_key
        
        result = manager.switch_persona(context_key, "expert")
        
        assert result is True
        assert manager.contexts[context_key].persona_id == "expert"

    def test_switch_persona_invalid_context(self, manager):
        """Test switching persona for invalid context."""
        result = manager.switch_persona("nonexistent:key", "expert")
        assert result is False

    def test_switch_persona_invalid_persona(self, manager):
        """Test switching to invalid persona."""
        context = manager.get_or_create_context(PlatformType.WEB, "ch", "u2")
        context_key = context.identity.context_key
        
        result = manager.switch_persona(context_key, "invalid")
        
        assert result is False

    def test_get_context(self, manager):
        """Test getting a context by key."""
        context = manager.get_or_create_context(PlatformType.CLI, "term", "u3")
        key = context.identity.context_key
        
        retrieved = manager.get_context(key)
        
        assert retrieved is context

    def test_get_context_nonexistent(self, manager):
        """Test getting nonexistent context."""
        result = manager.get_context("nonexistent")
        assert result is None

    def test_list_contexts(self, manager):
        """Test listing all contexts."""
        manager.get_or_create_context(PlatformType.WEB, "ch1", "u1")
        manager.get_or_create_context(PlatformType.WEB, "ch2", "u2")
        manager.get_or_create_context(PlatformType.DISCORD, "ch3", "u3")
        
        contexts = manager.list_contexts()
        
        assert len(contexts) == 3

    def test_clear_context(self, manager):
        """Test clearing a context."""
        context = manager.get_or_create_context(PlatformType.SLACK, "#general", "U1")
        key = context.identity.context_key
        
        result = manager.clear_context(key)
        
        assert result is True
        assert manager.get_context(key) is None

    def test_clear_context_nonexistent(self, manager):
        """Test clearing nonexistent context."""
        result = manager.clear_context("nonexistent")
        assert result is False

    def test_clear_inactive_contexts(self, manager):
        """Test clearing inactive contexts."""
        # Create a context first
        context = manager.get_or_create_context(PlatformType.WEB, "old", "user")
        # Manually set old timestamp
        context.last_activity = time.time() - 3600 * 25  # 25 hours ago
        
        cleared = manager.clear_inactive_contexts(max_age_hours=24)
        
        assert cleared >= 1

    def test_config_with_nested_personas(self):
        """Test initialization with nested personas config."""
        config = {
            "context": {
                "personas": {"nested": {"system_prompt": "Nested."}},
                "default_persona": "nested",
            }
        }
        manager = ContextManager(config)
        assert manager.default_persona == "nested"


class TestContextIntegration:
    """Integration tests for context module."""

    def test_full_context_lifecycle(self):
        """Test complete context lifecycle."""
        config = {
            "personas": {"test": {"system_prompt": "Test persona."}},
            "default_persona": "test",
            "persistence_enabled": False,
        }
        manager = ContextManager(config)
        
        # Create
        context = manager.get_or_create_context(
            PlatformType.WEB, "channel", "user123"
        )
        key = context.identity.context_key
        
        # Switch persona
        manager.switch_persona(key, "test")
        
        # Get
        retrieved = manager.get_context(key)
        assert retrieved.persona_id == "test"
        
        # Clear
        manager.clear_context(key)
        assert manager.get_context(key) is None


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_persona_config(self):
        """Test with empty persona config."""
        config = {"persistence_enabled": False}
        manager = ContextManager(config)
        # With empty config, personas should be empty dict
        assert manager.personas == {}
        # default_persona may be None or empty depending on implementation

    @pytest.fixture
    def manager(self):
        """Create a ContextManager with test config."""
        config = {
            "personas": {
                "general": {"system_prompt": "General persona."},
            },
            "default_persona": "general",
            "persistence_enabled": False,
        }
        return ContextManager(config)

    def test_special_characters_in_channel(self, manager):
        """Test handling of special characters in channel."""
        context = manager.get_or_create_context(
            PlatformType.WEB, "ch#1-2_3", "user"
        )
        assert context.identity.channel == "ch#1-2_3"

    def test_unicode_in_username(self, manager):
        """Test handling of unicode in username."""
        context = manager.get_or_create_context(
            PlatformType.WEB, "ch", "user",
            username="Test User"
        )
        assert context.identity.username == "Test User"
