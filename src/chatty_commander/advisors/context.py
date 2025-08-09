"""
Tab-aware context switching for advisors.

This module manages persistent identity and context switching across different
applications, allowing advisors to maintain appropriate personas and memory
per application/tab context.
"""

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional, List, Any
from enum import Enum


class PlatformType(Enum):
    """Supported platform types for context switching."""
    DISCORD = "discord"
    SLACK = "slack"
    WEB = "web"
    CLI = "cli"
    GUI = "gui"


@dataclass
class ContextIdentity:
    """Represents a user's identity in a specific context."""
    platform: PlatformType
    channel: str
    user_id: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
    
    @property
    def context_key(self) -> str:
        """Generate a unique context key for this identity."""
        return f"{self.platform.value}:{self.channel}:{self.user_id}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['platform'] = self.platform.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextIdentity':
        """Create from dictionary."""
        data['platform'] = PlatformType(data['platform'])
        return cls(**data)


@dataclass
class ContextState:
    """Represents the current state of a context."""
    identity: ContextIdentity
    persona_id: str
    system_prompt: str
    memory_key: str
    metadata: Dict[str, Any]
    last_activity: float = None
    
    def __post_init__(self):
        if self.last_activity is None:
            self.last_activity = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['identity'] = self.identity.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextState':
        """Create from dictionary."""
        data['identity'] = ContextIdentity.from_dict(data['identity'])
        return cls(**data)


class ContextManager:
    """
    Manages tab-aware context switching for advisors.
    
    This class handles:
    - Persistent identity tracking across applications
    - Context-aware persona switching
    - Memory isolation per context
    - State persistence and recovery
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.contexts: Dict[str, ContextState] = {}
        self.personas: Dict[str, Dict[str, Any]] = config.get('personas', {})
        self.default_persona = config.get('default_persona', 'general')
        
        # Persistence settings
        self.persistence_enabled = config.get('persistence_enabled', True)
        self.persistence_path = Path(config.get('persistence_path', 'data/contexts.json'))
        
        # Load existing contexts
        if self.persistence_enabled:
            self._load_contexts()
    
    def get_or_create_context(self, platform: PlatformType, channel: str, 
                            user_id: str, username: Optional[str] = None,
                            **kwargs) -> ContextState:
        """
        Get existing context or create new one for the given identity.
        
        Args:
            platform: The platform type (Discord, Slack, etc.)
            channel: Channel or conversation ID
            user_id: Unique user identifier
            username: Optional username for display
            **kwargs: Additional identity metadata
            
        Returns:
            ContextState for the identity
        """
        identity = ContextIdentity(
            platform=platform,
            channel=channel,
            user_id=user_id,
            username=username,
            **kwargs
        )
        
        context_key = identity.context_key
        
        if context_key not in self.contexts:
            # Create new context
            persona_id = self._resolve_persona_for_context(identity)
            system_prompt = self.personas.get(persona_id, {}).get('system_prompt', '')
            memory_key = f"{context_key}:memory"
            
            context = ContextState(
                identity=identity,
                persona_id=persona_id,
                system_prompt=system_prompt,
                memory_key=memory_key,
                last_activity=time.time(),
                metadata={}
            )
            
            self.contexts[context_key] = context
            
            if self.persistence_enabled:
                self._save_contexts()
        
        else:
            # Update existing context
            context = self.contexts[context_key]
            context.last_activity = time.time()
            
            # Update identity if new info provided
            if username and username != context.identity.username:
                context.identity.username = username
            
            if self.persistence_enabled:
                self._save_contexts()
        
        return self.contexts[context_key]
    
    def switch_persona(self, context_key: str, persona_id: str) -> bool:
        """
        Switch the persona for a specific context.
        
        Args:
            context_key: The context to switch
            persona_id: New persona ID
            
        Returns:
            True if switch successful, False if persona not found
        """
        if context_key not in self.contexts:
            return False
        
        if persona_id not in self.personas:
            return False
        
        context = self.contexts[context_key]
        context.persona_id = persona_id
        context.system_prompt = self.personas[persona_id]['system_prompt']
        context.last_activity = time.time()
        
        if self.persistence_enabled:
            self._save_contexts()
        
        return True
    
    def get_context(self, context_key: str) -> Optional[ContextState]:
        """Get context by key."""
        return self.contexts.get(context_key)
    
    def list_contexts(self) -> List[ContextState]:
        """List all active contexts."""
        return list(self.contexts.values())
    
    def clear_context(self, context_key: str) -> bool:
        """
        Clear a specific context.
        
        Args:
            context_key: The context to clear
            
        Returns:
            True if context was cleared, False if not found
        """
        if context_key in self.contexts:
            del self.contexts[context_key]
            
            if self.persistence_enabled:
                self._save_contexts()
            
            return True
        
        return False
    
    def clear_inactive_contexts(self, max_age_hours: float = 24.0) -> int:
        """
        Clear contexts that haven't been active for the specified time.
        
        Args:
            max_age_hours: Maximum age in hours before clearing
            
        Returns:
            Number of contexts cleared
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        to_clear = []
        for context_key, context in self.contexts.items():
            if current_time - context.last_activity > max_age_seconds:
                to_clear.append(context_key)
        
        for context_key in to_clear:
            del self.contexts[context_key]
        
        if to_clear and self.persistence_enabled:
            self._save_contexts()
        
        return len(to_clear)
    
    def _resolve_persona_for_context(self, identity: ContextIdentity) -> str:
        """
        Resolve which persona to use for a given context.
        
        This can be extended to implement more sophisticated persona
        selection logic based on platform, channel, user, etc.
        """
        # Simple logic: use platform-specific persona if available
        platform_persona = f"{identity.platform.value}_default"
        
        if platform_persona in self.personas:
            return platform_persona
        
        # Fall back to default persona
        return self.default_persona
    
    def _load_contexts(self) -> None:
        """Load contexts from persistence file."""
        if not self.persistence_path.exists():
            return
        
        try:
            with open(self.persistence_path, 'r') as f:
                data = json.load(f)
            
            for context_key, context_data in data.items():
                try:
                    context = ContextState.from_dict(context_data)
                    self.contexts[context_key] = context
                except Exception as e:
                    # Skip invalid contexts
                    continue
                    
        except Exception as e:
            # Log error but continue
            pass
    
    def _save_contexts(self) -> None:
        """Save contexts to persistence file."""
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {}
        for context_key, context in self.contexts.items():
            data[context_key] = context.to_dict()
        
        with open(self.persistence_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about current contexts."""
        platform_counts = {}
        persona_counts = {}
        
        for context in self.contexts.values():
            platform = context.identity.platform.value
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
            
            persona_counts[context.persona_id] = persona_counts.get(context.persona_id, 0) + 1
        
        return {
            'total_contexts': len(self.contexts),
            'platform_distribution': platform_counts,
            'persona_distribution': persona_counts,
            'persistence_enabled': self.persistence_enabled,
            'persistence_path': str(self.persistence_path)
        }
