"""
Thinking State Management for TalkingHead Avatar

This module manages the thinking state of AI agents and broadcasts state changes
to connected avatar UIs for synchronized animations and visual feedback.
"""

import logging
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Any, Optional, Callable, Set
import json

logger = logging.getLogger(__name__)


class ThinkingState(Enum):
    """States that an agent can be in during conversation."""
    IDLE = "idle"
    THINKING = "thinking"
    PROCESSING = "processing"
    RESPONDING = "responding"
    LISTENING = "listening"
    ERROR = "error"


@dataclass
class AgentStateInfo:
    """Information about an agent's current state."""
    agent_id: str
    avatar_id: Optional[str]
    persona_id: str
    state: ThinkingState
    message: Optional[str] = None
    progress: Optional[float] = None  # 0.0 to 1.0 for progress bars
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['state'] = self.state.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentStateInfo':
        """Create from dictionary."""
        data['state'] = ThinkingState(data['state'])
        return cls(**data)


class ThinkingStateManager:
    """
    Manages thinking states for multiple agents and broadcasts changes to avatar UIs.
    
    This enables synchronized animations between AI processing and avatar displays.
    """
    
    def __init__(self):
        self.agent_states: Dict[str, AgentStateInfo] = {}
        self.avatar_mappings: Dict[str, str] = {}  # agent_id -> avatar_id
        self.broadcast_callbacks: Set[Callable[[Dict[str, Any]], None]] = set()
        
    def register_agent(self, agent_id: str, persona_id: str, avatar_id: Optional[str] = None) -> None:
        """Register a new agent with optional avatar mapping."""
        self.agent_states[agent_id] = AgentStateInfo(
            agent_id=agent_id,
            avatar_id=avatar_id,
            persona_id=persona_id,
            state=ThinkingState.IDLE
        )
        
        if avatar_id:
            self.avatar_mappings[agent_id] = avatar_id
            
        self._broadcast_state_change(agent_id)
        
    def set_agent_state(self, agent_id: str, state: ThinkingState, 
                       message: Optional[str] = None, progress: Optional[float] = None) -> None:
        """Update an agent's thinking state."""
        if agent_id not in self.agent_states:
            logger.warning(f"Agent {agent_id} not registered, creating default entry")
            self.register_agent(agent_id, "default")
            
        agent_info = self.agent_states[agent_id]
        agent_info.state = state
        agent_info.message = message
        agent_info.progress = progress
        agent_info.timestamp = time.time()
        
        self._broadcast_state_change(agent_id)
        
    def get_agent_state(self, agent_id: str) -> Optional[AgentStateInfo]:
        """Get current state of an agent."""
        return self.agent_states.get(agent_id)
        
    def get_all_states(self) -> Dict[str, AgentStateInfo]:
        """Get all agent states."""
        return self.agent_states.copy()
        
    def map_agent_to_avatar(self, agent_id: str, avatar_id: str) -> None:
        """Map an agent to a specific avatar for visual correlation."""
        self.avatar_mappings[agent_id] = avatar_id
        
        if agent_id in self.agent_states:
            self.agent_states[agent_id].avatar_id = avatar_id
            self._broadcast_state_change(agent_id)
            
    def add_broadcast_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add a callback to receive state change broadcasts."""
        self.broadcast_callbacks.add(callback)
        
    def remove_broadcast_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Remove a broadcast callback."""
        self.broadcast_callbacks.discard(callback)
        
    def _broadcast_state_change(self, agent_id: str) -> None:
        """Broadcast state change to all registered callbacks."""
        agent_info = self.agent_states.get(agent_id)
        if not agent_info:
            return
            
        message = {
            "type": "agent_state_change",
            "data": agent_info.to_dict(),
            "timestamp": time.time()
        }
        
        for callback in self.broadcast_callbacks.copy():
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Error in broadcast callback: {e}")
                
    def start_thinking(self, agent_id: str, message: Optional[str] = None) -> None:
        """Convenience method to set thinking state."""
        self.set_agent_state(agent_id, ThinkingState.THINKING, message)
        
    def start_processing(self, agent_id: str, message: Optional[str] = None) -> None:
        """Convenience method to set processing state."""
        self.set_agent_state(agent_id, ThinkingState.PROCESSING, message)
        
    def start_responding(self, agent_id: str, message: Optional[str] = None) -> None:
        """Convenience method to set responding state."""
        self.set_agent_state(agent_id, ThinkingState.RESPONDING, message)
        
    def set_idle(self, agent_id: str) -> None:
        """Convenience method to set idle state."""
        self.set_agent_state(agent_id, ThinkingState.IDLE)
        
    def set_error(self, agent_id: str, error_message: str) -> None:
        """Convenience method to set error state."""
        self.set_agent_state(agent_id, ThinkingState.ERROR, error_message)


# Global instance for application-wide use
_global_thinking_manager: Optional[ThinkingStateManager] = None


def get_thinking_manager() -> ThinkingStateManager:
    """Get the global thinking state manager instance."""
    global _global_thinking_manager
    if _global_thinking_manager is None:
        _global_thinking_manager = ThinkingStateManager()
    return _global_thinking_manager


def reset_thinking_manager() -> None:
    """Reset the global thinking manager (useful for tests)."""
    global _global_thinking_manager
    _global_thinking_manager = None


class ThinkingStateContext:
    """Context manager for automatic thinking state transitions."""
    
    def __init__(self, agent_id: str, thinking_message: str = "Processing...", 
                 responding_message: str = "Generating response..."):
        self.agent_id = agent_id
        self.thinking_message = thinking_message
        self.responding_message = responding_message
        self.manager = get_thinking_manager()
        
    def __enter__(self):
        self.manager.start_thinking(self.agent_id, self.thinking_message)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.manager.set_error(self.agent_id, f"Error: {exc_val}")
        else:
            self.manager.set_idle(self.agent_id)
            
    def start_responding(self):
        """Transition to responding state."""
        self.manager.start_responding(self.agent_id, self.responding_message)


# Decorator for automatic thinking state management
def with_thinking_state(agent_id: str, thinking_msg: str = "Processing...", 
                       responding_msg: str = "Generating response..."):
    """Decorator to automatically manage thinking states during function execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with ThinkingStateContext(agent_id, thinking_msg, responding_msg) as ctx:
                result = func(*args, **kwargs)
                ctx.start_responding()
                return result
        return wrapper
    return decorator