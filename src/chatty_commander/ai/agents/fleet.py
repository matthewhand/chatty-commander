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
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHER DEALS INCIENTS,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

"""Agent Fleet Management.

Manages a collection of AI agents with different personas, capabilities, and roles.
Enables coordinated multi-agent workflows and team-based task execution.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from chatty_commander.avatars.thinking_state import ThinkingState

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Runtime status of an agent instance."""

    PENDING = "pending"
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class AgentCapability:
    """Represents a capability that an agent possesses."""

    name: str
    description: str
    confidence: float = 1.0  # 0.0 to 1.0


@dataclass
class AgentInstance:
    """Represents a running instance of an AI agent."""

    agent_id: str
    name: str
    persona_id: str
    team_role: str | None = None
    capabilities: list[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.PENDING
    state: ThinkingState = ThinkingState.IDLE
    current_task: str | None = None
    message_queue: asyncio.Queue[str] = field(default_factory=asyncio.Queue)
    error: str | None = None

    # LLM configuration
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None

    # Conversation history
    context: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.message_queue, dict):
            self.message_queue = asyncio.Queue()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "persona_id": self.persona_id,
            "team_role": self.team_role,
            "capabilities": self.capabilities,
            "status": self.status.value,
            "state": self.state.value,
            "current_task": self.current_task,
            "error": self.error,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "context_length": len(self.context),
        }

    def is_available(self) -> bool:
        """Check if agent is available to accept new tasks."""
        return (
            self.status == AgentStatus.READY
            and self.state == ThinkingState.IDLE
        )


@dataclass
class AgentFleetConfig:
    """Configuration for launching an agent fleet."""

    # Default agent configuration
    default_model: str = "gpt-4"
    default_temperature: float = 0.7
    default_max_tokens: int | None = None

    # Fleet size limits
    max_agents: int = 10
    max_concurrent_tasks: int = 5

    # Team composition
    team_roles: list[str] = field(default_factory=list)
    capability_distribution: dict[str, list[str]] = field(default_factory=dict)

    # Persistence
    persistence_dir: str = "~/.chatty_commander/fleet"

    # Lifecycle callbacks
    on_agent_ready: Callable[[AgentInstance], None] | None = None
    on_agent_error: Callable[[AgentInstance, str], None] | None = None
    on_task_complete: Callable[[AgentInstance, str], None] | None = None


class AgentFleet:
    """Manages a fleet of AI agent instances.

    The fleet can contain multiple agents with different personas, capabilities,
    and team roles. Agents can be launched, assigned tasks, and coordinated
    for complex multi-agent workflows.

    Example usage:
        >>> fleet = AgentFleet(max_agents=5)
        >>> fleet.launch_agent(name="Researcher", role="research")
        >>> fleet.launch_agent(name="Analyst", role="analysis")
        >>> fleet.assign_task("agent-1", "Analyze this data")
    """

    def __init__(
        self,
        config: AgentFleetConfig | None = None,
        thinking_state_manager: Any = None,
    ):
        """Initialize the agent fleet.

        Args:
            config: Fleet configuration, or None for defaults
            thinking_state_manager: Optional ThinkingStateManager for state sync
        """
        self.config = config or AgentFleetConfig()
        self.thinking_state_manager = thinking_state_manager

        # Agent registry
        self.agents: dict[str, AgentInstance] = {}
        self.agents_by_role: dict[str, list[str]] = {}
        self.agents_by_capability: dict[str, list[str]] = {}

        # Task tracking
        self.active_tasks: dict[str, str] = {}  # task_id -> agent_id
        self.pending_tasks: list[tuple[str, str]] = []  # (task, agent_id_hint)

        # State
        self._running = False
        self._lock = asyncio.Lock()

        logger.info(
            "AgentFleet initialized with max_agents=%d, max_concurrent_tasks=%d",
            self.config.max_agents,
            self.config.max_concurrent_tasks,
        )

    def __len__(self) -> int:
        """Return number of agents in the fleet."""
        return len(self.agents)

    def __contains__(self, agent_id: str) -> bool:
        """Check if an agent exists in the fleet."""
        return agent_id in self.agents

    async def start(self) -> None:
        """Start the fleet manager."""
        if self._running:
            logger.warning("AgentFleet is already running")
            return

        self._running = True
        logger.info("AgentFleet started")

    async def stop(self, graceful: bool = True) -> None:
        """Stop the fleet and all agents.

        Args:
            graceful: If True, wait for active tasks to complete
        """
        if not self._running:
            logger.warning("AgentFleet is not running")
            return

        self._running = False

        if graceful:
            # Wait for active tasks
            for task_id, agent_id in list(self.active_tasks.items()):
                logger.info("Waiting for task %s on agent %s to complete", task_id, agent_id)
                # In a real implementation, we'd wait for task completion
                pass

        # Stop all agents
        for agent_id, agent in list(self.agents.items()):
            agent.status = AgentStatus.STOPPED
            agent.state = ThinkingState.IDLE
            logger.info("Stopped agent %s (%s)", agent_id, agent.name)

        self.agents.clear()
        self.agents_by_role.clear()
        self.agents_by_capability.clear()
        self.active_tasks.clear()
        self.pending_tasks.clear()

        logger.info("AgentFleet stopped")

    def launch_agent(
        self,
        name: str,
        persona_id: str | None = None,
        team_role: str | None = None,
        capabilities: list[str] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AgentInstance:
        """Launch a new agent instance.

        Args:
            name: Human-readable name for the agent
            persona_id: Unique persona identifier
            team_role: Team role (e.g., "researcher", "analyst", "coder")
            capabilities: List of capability names
            model: LLM model to use
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens for responses

        Returns:
            The created AgentInstance

        Raises:
            RuntimeError: If fleet is not running or max agents reached
        """
        if not self._running:
            raise RuntimeError("AgentFleet is not running. Call start() first.")

        if len(self.agents) >= self.config.max_agents:
            raise RuntimeError(
                f"Maximum agents reached ({self.config.max_agents}). "
                "Stop some agents first."
            )

        agent_id = str(uuid.uuid4())
        persona_id = persona_id or f"persona-{agent_id[:8]}"

        capabilities = capabilities or self.config.capability_distribution.get(
            team_role or "", []
        )

        agent = AgentInstance(
            agent_id=agent_id,
            name=name,
            persona_id=persona_id,
            team_role=team_role,
            capabilities=capabilities,
            model=model or self.config.default_model,
            temperature=temperature or self.config.default_temperature,
            max_tokens=max_tokens or self.config.default_max_tokens,
        )

        self.agents[agent_id] = agent

        # Index by role
        if team_role:
            self.agents_by_role.setdefault(team_role, []).append(agent_id)

        # Index by capability
        for cap in capabilities:
            self.agents_by_capability.setdefault(cap, []).append(agent_id)

        # Update thinking state
        if self.thinking_state_manager:
            self.thinking_state_manager.register_agent(
                agent_id=agent_id,
                persona_id=persona_id,
                avatar_id=None,  # Would be set if avatar is assigned
            )
            self.thinking_state_manager.update_agent_state(
                agent_id=agent_id,
                state=ThinkingState.IDLE,
                progress=0.0,
                message="Agent launched and ready",
            )

        # Update agent status
        agent.status = AgentStatus.READY

        logger.info(
            "Launched agent %s (%s) with role=%s, capabilities=%s",
            agent_id[:8],
            name,
            team_role,
            capabilities,
        )

        # Callback
        if self.config.on_agent_ready:
            self.config.on_agent_ready(agent)

        return agent

    async def launch_agents_from_blueprints(
        self,
        blueprints_path: str | None = None,
        blueprint_ids: list[str] | None = None,
    ) -> list[AgentInstance]:
        """Launch multiple agents from stored blueprints.

        Args:
            blueprints_path: Path to agents.json store file
            blueprint_ids: Specific blueprint IDs to launch, or None for all

        Returns:
            List of launched AgentInstance objects
        """
        # Import here to avoid circular dependencies
        import json
        from pathlib import Path

        blueprints_path = blueprints_path or str(
            Path.home() / ".chatty_commander" / "agents.json"
        )

        launched_agents: list[AgentInstance] = []

        try:
            with open(blueprints_path) as f:
                data = json.load(f)

            blueprints = data.get("agents", [])

            for bp in blueprints:
                if blueprint_ids and bp.get("id") not in blueprint_ids:
                    continue

                agent = self.launch_agent(
                    name=bp.get("name", "Agent"),
                    persona_id=bp.get("id", str(uuid.uuid4())),
                    team_role=bp.get("team_role"),
                    capabilities=bp.get("capabilities", []),
                )
                launched_agents.append(agent)

                # Limit concurrent launches
                if len(launched_agents) >= self.config.max_agents:
                    break

        except FileNotFoundError:
            logger.warning("No agent blueprints found at %s", blueprints_path)
        except Exception as e:
            logger.error("Error loading agent blueprints: %s", e)
            raise

        return launched_agents

    async def assign_task(
        self,
        task: str,
        agent_id: str | None = None,
        role: str | None = None,
        capability: str | None = None,
    ) -> str | None:
        """Assign a task to an agent.

        The task will be assigned to:
        1. The specified agent_id if provided
        2. An available agent with the specified role
        3. An available agent with the specified capability
        4. Any available agent

        Args:
            task: The task description/prompt
            agent_id: Specific agent to assign to, or None for auto-selection
            role: Required team role, or None
            capability: Required capability, or None

        Returns:
            task_id if assigned, None if no agent available
        """
        task_id = str(uuid.uuid4())

        # Find suitable agent
        agent: AgentInstance | None = None

        if agent_id and agent_id in self.agents:
            agent = self.agents[agent_id]
        else:
            agent = self._find_available_agent(role=role, capability=capability)

        if agent is None:
            # Queue the task
            self.pending_tasks.append((task, agent_id or role or capability or ""))
            logger.info(
                "No agent available for task %s, queued (queue size: %d)",
                task_id,
                len(self.pending_tasks),
            )
            return None

        # Assign task to agent
        agent.current_task = task
        agent.state = ThinkingState.THINKING
        self.active_tasks[task_id] = agent.agent_id

        # Update thinking state
        if self.thinking_state_manager:
            self.thinking_state_manager.update_agent_state(
                agent_id=agent.agent_id,
                state=ThinkingState.THINKING,
                progress=0.0,
                message=f"Processing: {task[:50]}...",
            )

        logger.info("Assigned task %s to agent %s (%s)", task_id, agent.agent_id[:8], agent.name)

        return task_id

    def _find_available_agent(
        self,
        role: str | None = None,
        capability: str | None = None,
    ) -> AgentInstance | None:
        """Find an available agent matching the criteria."""
        candidates: list[AgentInstance] = []

        for agent in self.agents.values():
            if not agent.is_available():
                continue

            # Match by role
            if role and agent.team_role != role:
                continue

            # Match by capability
            if capability and capability not in agent.capabilities:
                continue

            candidates.append(agent)

        # Prefer agents with matching role or capability
        if role:
            for agent in self.agents.values():
                if agent.is_available() and agent.team_role == role:
                    return agent

        if capability:
            for agent in self.agents.values():
                if agent.is_available() and capability in agent.capabilities:
                    return agent

        # Return any available agent
        return candidates[0] if candidates else None

    async def complete_task(
        self,
        task_id: str,
        result: str,
        agent_id: str | None = None,
    ) -> None:
        """Mark a task as complete.

        Args:
            task_id: The task identifier
            result: The task result
            agent_id: Optional agent ID (inferred from task_id if not provided)
        """
        if task_id not in self.active_tasks:
            logger.warning("Task %s not found in active tasks", task_id)
            return

        agent_id = agent_id or self.active_tasks.pop(task_id)
        if agent_id not in self.agents:
            logger.warning("Agent %s not found", agent_id)
            return

        agent = self.agents[agent_id]
        agent.current_task = None
        agent.state = ThinkingState.IDLE

        # Add result to context
        agent.context.append(
            {
                "role": "assistant",
                "content": result,
                "task_id": task_id,
            }
        )

        # Update thinking state
        if self.thinking_state_manager:
            self.thinking_state_manager.update_agent_state(
                agent_id=agent.agent_id,
                state=ThinkingState.IDLE,
                progress=1.0,
                message="Task completed",
            )

        logger.info("Task %s completed by agent %s", task_id, agent_id[:8])

        # Callback
        if self.config.on_task_complete:
            self.config.on_task_complete(agent, task_id)

        # Try to assign pending tasks
        await self._process_pending_tasks()

    async def _process_pending_tasks(self) -> None:
        """Process queued tasks if agents become available."""
        while self.pending_tasks and len(self.active_tasks) < self.config.max_concurrent_tasks:
            task, hint = self.pending_tasks.pop(0)

            # Try to assign with the hint (could be agent_id, role, or capability)
            if hint in self.agents:
                # It's an agent_id
                await self.assign_task(task, agent_id=hint)
            elif hint in self.agents_by_role:
                # It's a role
                await self.assign_task(task, role=hint)
            elif hint in self.agents_by_capability:
                # It's a capability
                await self.assign_task(task, capability=hint)
            else:
                # Try without hint
                await self.assign_task(task)

    def get_agents_by_role(self, role: str) -> list[AgentInstance]:
        """Get all agents with a specific role."""
        return [self.agents[aid] for aid in self.agents_by_role.get(role, [])]

    def get_agents_with_capability(self, capability: str) -> list[AgentInstance]:
        """Get all agents with a specific capability."""
        return [self.agents[aid] for aid in self.agents_by_capability.get(capability, [])]

    def list_agents(self) -> list[dict[str, Any]]:
        """List all agents in the fleet."""
        return [agent.to_dict() for agent in self.agents.values()]

    def get_fleet_stats(self) -> dict[str, Any]:
        """Get fleet statistics."""
        return {
            "total_agents": len(self.agents),
            "running": self._running,
            "active_tasks": len(self.active_tasks),
            "pending_tasks": len(self.pending_tasks),
            "by_role": {k: len(v) for k, v in self.agents_by_role.items()},
            "by_capability": {k: len(v) for k, v in self.agents_by_capability.items()},
            "agents": [a.to_dict() for a in self.agents.values()],
        }
