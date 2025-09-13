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
Thinking State Management for TalkingHead Avatar

This module manages the thinking state of AI agents and broadcasts state changes
to connected avatar UIs for synchronized animations and visual feedback.
"""

import asyncio
import inspect
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ThinkingState(Enum):
    """States that an agent can be in during conversation."""

    IDLE = "idle"
    THINKING = "thinking"
    PROCESSING = "processing"
    RESPONDING = "responding"
    LISTENING = "listening"
    TOOL_CALLING = "tool_calling"
    HANDOFF = "handoff"
    ERROR = "error"


@dataclass
class AgentStateInfo:
    """Information about an agent's current state."""

    agent_id: str
    avatar_id: str | None
    persona_id: str
    state: ThinkingState
    message: str | None = None
    progress: float | None = None  # 0.0 to 1.0 for progress bars
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["state"] = self.state.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentStateInfo":
        """Create from dictionary."""
        data["state"] = ThinkingState(data["state"])
        return cls(**data)


class ThinkingStateManager:
    """
    Manages thinking states for multiple agents and broadcasts changes to avatar UIs.

    This enables synchronized animations between AI processing and avatar displays.
    """

    def __init__(self):
        self.agent_states: dict[str, AgentStateInfo] = {}
        self.avatar_mappings: dict[str, str] = {}  # agent_id -> avatar_id
        self.broadcast_callbacks: set[Callable[[dict[str, Any]], None]] = set()

    def register_agent(
        self, agent_id: str, persona_id: str, avatar_id: str | None = None
    ) -> None:
        """Register a new agent with optional avatar mapping."""
        self.agent_states[agent_id] = AgentStateInfo(
            agent_id=agent_id,
            avatar_id=avatar_id,
            persona_id=persona_id,
            state=ThinkingState.IDLE,
        )

        if avatar_id:
            self.avatar_mappings[agent_id] = avatar_id

        self._broadcast_state_change(agent_id)

    def set_agent_state(
        self,
        agent_id: str,
        state: ThinkingState,
        message: str | None = None,
        progress: float | None = None,
    ) -> None:
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

    def get_agent_state(self, agent_id: str) -> AgentStateInfo | None:
        """Get current state of an agent."""
        return self.agent_states.get(agent_id)

    def get_all_states(self) -> dict[str, AgentStateInfo]:
        """Get all agent states."""
        return self.agent_states.copy()

    def map_agent_to_avatar(self, agent_id: str, avatar_id: str) -> None:
        """Map an agent to a specific avatar for visual correlation."""
        self.avatar_mappings[agent_id] = avatar_id

        if agent_id in self.agent_states:
            self.agent_states[agent_id].avatar_id = avatar_id
            self._broadcast_state_change(agent_id)

    def add_broadcast_callback(
        self,
        callback: (
            Callable[[dict[str, Any]], None]
            | Callable[[dict[str, Any]], Awaitable[None]]
        ),
    ) -> None:
        """Add a callback to receive state change broadcasts."""
        self.broadcast_callbacks.add(callback)

    def remove_broadcast_callback(
        self,
        callback: (
            Callable[[dict[str, Any]], None]
            | Callable[[dict[str, Any]], Awaitable[None]]
        ),
    ) -> None:
        """Remove a broadcast callback."""
        self.broadcast_callbacks.discard(callback)

    def _broadcast(self, message: dict[str, Any]) -> None:
        callbacks = list(self.broadcast_callbacks.copy())
        for callback in callbacks:
            try:
                if inspect.iscoroutinefunction(callback):
                    # If we're in an event loop, schedule the coroutine, else run it
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(callback(message))
                    except RuntimeError:
                        asyncio.run(callback(message))
                else:
                    callback(message)
            except Exception as e:
                logger.error(f"Error in broadcast callback: {e}")

    def _broadcast_state_change(self, agent_id: str) -> None:
        """Broadcast state change to all registered callbacks."""
        agent_info = self.agent_states.get(agent_id)
        if not agent_info:
            return
        message = {
            "type": "agent_state_change",
            "data": agent_info.to_dict(),
            "timestamp": time.time(),
        }
        self._broadcast(message)

    # Tool calling lifecycle events
    def start_tool_call(self, agent_id: str, tool_name: str | None = None) -> None:
        self.set_agent_state(
            agent_id,
            ThinkingState.TOOL_CALLING,
            f"Calling tool {tool_name or ''}".strip(),
        )
        self._broadcast(
            {
                "type": "tool_call_start",
                "data": {"agent_id": agent_id, "tool": tool_name},
                "timestamp": time.time(),
            }
        )

    def end_tool_call(self, agent_id: str, tool_name: str | None = None) -> None:
        # Return to processing by default
        self.set_agent_state(agent_id, ThinkingState.PROCESSING)
        self._broadcast(
            {
                "type": "tool_call_end",
                "data": {"agent_id": agent_id, "tool": tool_name},
                "timestamp": time.time(),
            }
        )

    # Agent handoff lifecycle
    def handoff_start(
        self, agent_id: str, to_agent_persona: str, reason: str | None = None
    ) -> None:
        self.set_agent_state(agent_id, ThinkingState.HANDOFF, reason)
        self._broadcast(
            {
                "type": "handoff_start",
                "data": {
                    "agent_id": agent_id,
                    "to_persona": to_agent_persona,
                    "reason": reason,
                },
                "timestamp": time.time(),
            }
        )

    def handoff_complete(self, agent_id: str, new_persona_id: str) -> None:
        # Update persona mapping and return to idle
        if agent_id in self.agent_states:
            self.agent_states[agent_id].persona_id = new_persona_id
        self.set_agent_state(agent_id, ThinkingState.IDLE)
        self._broadcast(
            {
                "type": "handoff_complete",
                "data": {"agent_id": agent_id, "persona_id": new_persona_id},
                "timestamp": time.time(),
            }
        )

    def start_thinking(self, agent_id: str, message: str | None = None) -> None:
        """Convenience method to set thinking state."""
        self.set_agent_state(agent_id, ThinkingState.THINKING, message)

    def start_processing(self, agent_id: str, message: str | None = None) -> None:
        """Convenience method to set processing state."""
        self.set_agent_state(agent_id, ThinkingState.PROCESSING, message)

    def start_responding(self, agent_id: str, message: str | None = None) -> None:
        """Convenience method to set responding state."""
        self.set_agent_state(agent_id, ThinkingState.RESPONDING, message)

    def set_idle(self, agent_id: str) -> None:
        """Convenience method to set idle state."""
        self.set_agent_state(agent_id, ThinkingState.IDLE)

    def set_error(self, agent_id: str, error_message: str) -> None:
        """Convenience method to set error state."""
        self.set_agent_state(agent_id, ThinkingState.ERROR, error_message)


# Global instance for application-wide use
_global_thinking_manager: ThinkingStateManager | None = None


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

    def __init__(
        self,
        agent_id: str,
        thinking_message: str = "Processing...",
        responding_message: str = "Generating response...",
    ):
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
def with_thinking_state(
    agent_id: str,
    thinking_msg: str = "Processing...",
    responding_msg: str = "Generating response...",
):
    """Decorator to automatically manage thinking states during function execution."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            with ThinkingStateContext(agent_id, thinking_msg, responding_msg) as ctx:
                result = func(*args, **kwargs)
                ctx.start_responding()
                return result

        return wrapper

    return decorator
