"""
Unit tests for tab-aware context switching system.
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from chatty_commander.advisors.context import (
    ContextManager, ContextIdentity, ContextState, PlatformType
)


class TestContextIdentity:
    """Test ContextIdentity dataclass."""
    
    def test_context_key_generation(self):
        """Test context key generation."""
        identity = ContextIdentity(
            platform=PlatformType.DISCORD,
            channel="123456789",
            user_id="user123"
        )
        
        expected_key = "discord:123456789:user123"
        assert identity.context_key == expected_key
    
    def test_serialization(self):
        """Test serialization to/from dict."""
        identity = ContextIdentity(
            platform=PlatformType.SLACK,
            channel="general",
            user_id="user456",
            username="testuser",
            display_name="Test User"
        )
        
        data = identity.to_dict()
        restored = ContextIdentity.from_dict(data)
        
        assert restored.platform == identity.platform
        assert restored.channel == identity.channel
        assert restored.user_id == identity.user_id
        assert restored.username == identity.username
        assert restored.display_name == identity.display_name
    
    def test_created_at_default(self):
        """Test that created_at is set automatically."""
        identity = ContextIdentity(
            platform=PlatformType.WEB,
            channel="chat",
            user_id="user789"
        )
        
        assert identity.created_at is not None
        assert isinstance(identity.created_at, float)


class TestContextState:
    """Test ContextState dataclass."""
    
    def test_serialization(self):
        """Test serialization to/from dict."""
        identity = ContextIdentity(
            platform=PlatformType.DISCORD,
            channel="test-channel",
            user_id="user123"
        )
        
        state = ContextState(
            identity=identity,
            persona_id="philosopher",
            system_prompt="You are a philosophical advisor.",
            memory_key="discord:test-channel:user123:memory",
            last_activity=time.time(),
            metadata={"last_topic": "ethics"}
        )
        
        data = state.to_dict()
        restored = ContextState.from_dict(data)
        
        assert restored.identity.context_key == state.identity.context_key
        assert restored.persona_id == state.persona_id
        assert restored.system_prompt == state.system_prompt
        assert restored.memory_key == state.memory_key
        assert restored.metadata == state.metadata
    
    def test_last_activity_default(self):
        """Test that last_activity is set automatically."""
        identity = ContextIdentity(
            platform=PlatformType.SLACK,
            channel="general",
            user_id="user456"
        )
        
        state = ContextState(
            identity=identity,
            persona_id="general",
            system_prompt="You are a helpful assistant.",
            memory_key="slack:general:user456:memory",
            metadata={}
        )
        
        assert state.last_activity is not None
        assert isinstance(state.last_activity, float)


class TestContextManager:
    """Test ContextManager class."""
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        return {
            'personas': {
                'general': {
                    'system_prompt': 'You are a helpful assistant.'
                },
                'philosopher': {
                    'system_prompt': 'You are a philosophical advisor.'
                },
                'discord_default': {
                    'system_prompt': 'You are a Discord bot assistant.'
                },
                'slack_default': {
                    'system_prompt': 'You are a Slack app assistant.'
                }
            },
            'default_persona': 'general',
            'persistence_enabled': False
        }
    
    @pytest.fixture
    def context_manager(self, config):
        """Context manager instance."""
        return ContextManager(config)
    
    def test_get_or_create_context_new(self, context_manager):
        """Test creating a new context."""
        context = context_manager.get_or_create_context(
            platform=PlatformType.DISCORD,
            channel="123456789",
            user_id="user123",
            username="testuser"
        )
        
        assert context.identity.platform == PlatformType.DISCORD
        assert context.identity.channel == "123456789"
        assert context.identity.user_id == "user123"
        assert context.identity.username == "testuser"
        assert context.persona_id == "discord_default"  # Platform-specific persona
        assert context.system_prompt == "You are a Discord bot assistant."
        assert context.memory_key == "discord:123456789:user123:memory"
    
    def test_get_or_create_context_existing(self, context_manager):
        """Test retrieving an existing context."""
        # Create context
        context1 = context_manager.get_or_create_context(
            platform=PlatformType.SLACK,
            channel="general",
            user_id="user456"
        )
        
        # Get same context again
        context2 = context_manager.get_or_create_context(
            platform=PlatformType.SLACK,
            channel="general",
            user_id="user456"
        )
        
        assert context1 is context2
        assert context2.persona_id == "slack_default"
    
    def test_switch_persona(self, context_manager):
        """Test switching persona for a context."""
        context = context_manager.get_or_create_context(
            platform=PlatformType.WEB,
            channel="chat",
            user_id="user789"
        )
        
        # Switch to philosopher persona
        success = context_manager.switch_persona(context.identity.context_key, "philosopher")
        
        assert success is True
        assert context.persona_id == "philosopher"
        assert context.system_prompt == "You are a philosophical advisor."
    
    def test_switch_persona_invalid(self, context_manager):
        """Test switching to invalid persona."""
        context = context_manager.get_or_create_context(
            platform=PlatformType.DISCORD,
            channel="test",
            user_id="user123"
        )
        
        # Try to switch to non-existent persona
        success = context_manager.switch_persona(context.identity.context_key, "nonexistent")
        
        assert success is False
        assert context.persona_id == "discord_default"  # Unchanged
    
    def test_clear_context(self, context_manager):
        """Test clearing a context."""
        context = context_manager.get_or_create_context(
            platform=PlatformType.SLACK,
            channel="general",
            user_id="user456"
        )
        
        context_key = context.identity.context_key
        assert context_manager.get_context(context_key) is not None
        
        # Clear the context
        success = context_manager.clear_context(context_key)
        
        assert success is True
        assert context_manager.get_context(context_key) is None
    
    def test_clear_inactive_contexts(self, context_manager):
        """Test clearing inactive contexts."""
        # Create contexts
        context1 = context_manager.get_or_create_context(
            platform=PlatformType.DISCORD,
            channel="channel1",
            user_id="user1"
        )
        
        context2 = context_manager.get_or_create_context(
            platform=PlatformType.SLACK,
            channel="channel2",
            user_id="user2"
        )
        
        # Make one context inactive
        context1.last_activity = time.time() - 25 * 3600  # 25 hours ago
        
        # Clear inactive contexts (default 24 hours)
        cleared_count = context_manager.clear_inactive_contexts()
        
        assert cleared_count == 1
        assert context_manager.get_context(context1.identity.context_key) is None
        assert context_manager.get_context(context2.identity.context_key) is not None
    
    def test_get_stats(self, context_manager):
        """Test getting context statistics."""
        # Create contexts
        context_manager.get_or_create_context(
            platform=PlatformType.DISCORD,
            channel="channel1",
            user_id="user1"
        )
        
        context_manager.get_or_create_context(
            platform=PlatformType.DISCORD,
            channel="channel2",
            user_id="user2"
        )
        
        context_manager.get_or_create_context(
            platform=PlatformType.SLACK,
            channel="general",
            user_id="user3"
        )
        
        stats = context_manager.get_stats()
        
        assert stats['total_contexts'] == 3
        assert stats['platform_distribution']['discord'] == 2
        assert stats['platform_distribution']['slack'] == 1
        assert stats['persona_distribution']['discord_default'] == 2
        assert stats['persona_distribution']['slack_default'] == 1
        assert stats['persistence_enabled'] is False
    
    def test_persistence(self):
        """Test context persistence."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'personas': {
                    'general': {'system_prompt': 'You are helpful.'}
                },
                'default_persona': 'general',
                'persistence_enabled': True,
                'persistence_path': str(Path(temp_dir) / 'contexts.json')
            }
            
            # Create manager and add context
            manager1 = ContextManager(config)
            context = manager1.get_or_create_context(
                platform=PlatformType.WEB,
                channel="test",
                user_id="user123"
            )
            
            # Create new manager (should load existing context)
            manager2 = ContextManager(config)
            loaded_context = manager2.get_context(context.identity.context_key)
            
            assert loaded_context is not None
            assert loaded_context.identity.context_key == context.identity.context_key
            assert loaded_context.persona_id == context.persona_id
    
    def test_persona_resolution_logic(self, context_manager):
        """Test persona resolution logic."""
        # Discord should get discord_default persona
        discord_context = context_manager.get_or_create_context(
            platform=PlatformType.DISCORD,
            channel="test",
            user_id="user123"
        )
        assert discord_context.persona_id == "discord_default"
        
        # Slack should get slack_default persona
        slack_context = context_manager.get_or_create_context(
            platform=PlatformType.SLACK,
            channel="test",
            user_id="user456"
        )
        assert slack_context.persona_id == "slack_default"
        
        # Web should get general persona (no platform-specific available)
        web_context = context_manager.get_or_create_context(
            platform=PlatformType.WEB,
            channel="test",
            user_id="user789"
        )
        assert web_context.persona_id == "general"
    
    def test_identity_update(self, context_manager):
        """Test updating identity information."""
        context = context_manager.get_or_create_context(
            platform=PlatformType.DISCORD,
            channel="test",
            user_id="user123"
        )
        
        # Update with new username
        updated_context = context_manager.get_or_create_context(
            platform=PlatformType.DISCORD,
            channel="test",
            user_id="user123",
            username="newusername"
        )
        
        assert updated_context is context  # Same context object
        assert context.identity.username == "newusername"
