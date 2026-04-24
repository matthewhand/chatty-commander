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

"""Tests for Agent Fleet Management System."""

import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from chatty_commander.ai.agents.fleet import (
    AgentCapability,
    AgentFleet,
    AgentFleetConfig,
    AgentInstance,
    AgentStatus,
)
from chatty_commander.ai.agents.launcher import (
    LaunchConfig,
    launch_preset_fleet,
)
from chatty_commander.avatars.thinking_state import ThinkingState


class TestAgentInstance:
    """Tests for AgentInstance dataclass."""

    def test_agent_instance_creation(self):
        """Test creating an agent instance with defaults."""
        agent = AgentInstance(
            agent_id="agent-1",
            name="Test Agent",
            persona_id="persona-1",
        )
        assert agent.agent_id == "agent-1"
        assert agent.name == "Test Agent"
        assert agent.persona_id == "persona-1"
        assert agent.team_role is None
        assert agent.capabilities == []
        assert agent.status == AgentStatus.PENDING
        assert agent.state == ThinkingState.IDLE
        assert agent.current_task is None
        assert agent.temperature == 0.7

    def test_agent_instance_with_all_fields(self):
        """Test creating an agent instance with all fields specified."""
        agent = AgentInstance(
            agent_id="agent-2",
            name="Coder",
            persona_id="coder-1",
            team_role="developer",
            capabilities=["python", "javascript"],
            status=AgentStatus.READY,
            state=ThinkingState.THINKING,
            current_task="Write code",
            temperature=0.9,
            max_tokens=2048,
        )
        assert agent.team_role == "developer"
        assert agent.capabilities == ["python", "javascript"]
        assert agent.status == AgentStatus.READY
        assert agent.state == ThinkingState.THINKING
        assert agent.current_task == "Write code"
        assert agent.temperature == 0.9

    def test_agent_instance_is_available(self):
        """Test agent availability checking."""
        # Available agent
        agent1 = AgentInstance(
            agent_id="agent-1",
            name="Available",
            persona_id="persona-1",
            status=AgentStatus.READY,
            state=ThinkingState.IDLE,
        )
        assert agent1.is_available() is True

        # Busy agent
        agent2 = AgentInstance(
            agent_id="agent-2",
            name="Busy",
            persona_id="persona-2",
            status=AgentStatus.READY,
            state=ThinkingState.THINKING,
        )
        assert agent2.is_available() is False

        # Not ready agent
        agent3 = AgentInstance(
            agent_id="agent-3",
            name="Not Ready",
            persona_id="persona-3",
            status=AgentStatus.INITIALIZING,
            state=ThinkingState.IDLE,
        )
        assert agent3.is_available() is False

    def test_agent_instance_to_dict(self):
        """Test converting agent instance to dictionary."""
        agent = AgentInstance(
            agent_id="agent-1",
            name="Test",
            persona_id="persona-1",
            team_role="researcher",
            capabilities=["search", "analyze"],
        )
        d = agent.to_dict()
        assert d["agent_id"] == "agent-1"
        assert d["name"] == "Test"
        assert d["persona_id"] == "persona-1"
        assert d["team_role"] == "researcher"
        assert d["capabilities"] == ["search", "analyze"]
        assert d["status"] == "pending"


class TestAgentFleet:
    """Tests for AgentFleet class."""

    @pytest.fixture
    def fleet(self):
        """Create a test fleet instance."""
        config = AgentFleetConfig(max_agents=5)
        fleet = AgentFleet(config=config)
        return fleet

    @pytest.fixture
    def running_fleet(self):
        """Create and start a test fleet."""
        config = AgentFleetConfig(max_agents=5)
        fleet = AgentFleet(config=config)
        # Run async start
        asyncio.run(fleet.start())
        return fleet

    def test_fleet_creation(self, fleet):
        """Test creating a fleet."""
        assert len(fleet) == 0
        assert fleet.config.max_agents == 5
        assert fleet._running is False

    def test_fleet_start_stop(self, running_fleet):
        """Test starting and stopping a fleet."""
        assert running_fleet._running is True
        asyncio.run(running_fleet.stop())
        assert running_fleet._running is False

    def test_fleet_launch_agent(self, running_fleet):
        """Test launching an agent in the fleet."""
        agent = running_fleet.launch_agent(
            name="Researcher-1",
            persona_id="researcher-1",
            team_role="researcher",
            capabilities=["search", "analyze"],
        )
        assert len(running_fleet) == 1
        assert agent.agent_id in running_fleet.agents
        assert "researcher" in running_fleet.agents_by_role
        assert running_fleet.agents_by_role["researcher"] == [agent.agent_id]
        assert agent in running_fleet.agents_by_role["researcher"]

    def test_fleet_launch_multiple_agents(self, running_fleet):
        """Test launching multiple agents."""
        agents = []
        for i in range(3):
            agent = running_fleet.launch_agent(
                name=f"Agent-{i}",
                persona_id=f"persona-{i}",
                team_role="general",
            )
            agents.append(agent)

        assert len(running_fleet) == 3
        assert len(running_fleet.agents_by_role["general"]) == 3

    def test_fleet_max_agents(self, running_fleet):
        """Test that fleet enforces max agents limit."""
        for i in range(5):
            running_fleet.launch_agent(
                name=f"Agent-{i}",
                persona_id=f"persona-{i}",
            )

        with pytest.raises(RuntimeError, match="Maximum agents reached"):
            running_fleet.launch_agent(
                name="Agent-6",
                persona_id="persona-6",
            )

    def test_fleet_not_running(self, fleet):
        """Test that launching fails if fleet is not running."""
        with pytest.raises(RuntimeError, match="AgentFleet is not running"):
            fleet.launch_agent(
                name="Test",
                persona_id="persona-1",
            )

    def test_fleet_assign_task(self, running_fleet):
        """Test assigning a task to an agent."""
        agent = running_fleet.launch_agent(
            name="Worker",
            persona_id="worker-1",
        )

        task_id = asyncio.run(
            running_fleet.assign_task("Test task", agent_id=agent.agent_id)
        )
        assert task_id is not None
        assert task_id in running_fleet.active_tasks
        assert running_fleet.active_tasks[task_id] == agent.agent_id
        assert agent.current_task == "Test task"

    def test_fleet_complete_task(self, running_fleet):
        """Test completing a task."""
        agent = running_fleet.launch_agent(
            name="Worker",
            persona_id="worker-1",
        )

        task_id = asyncio.run(
            running_fleet.assign_task("Test task", agent_id=agent.agent_id)
        )

        asyncio.run(running_fleet.complete_task(task_id, "Task result"))

        assert task_id not in running_fleet.active_tasks
        assert agent.current_task is None
        assert len(agent.context) == 1
        assert agent.context[0]["content"] == "Task result"

    def test_fleet_get_agents_by_role(self, fleet):
        """Test getting agents by role."""
        asyncio.run(fleet.start())

        fleet.launch_agent(name="R1", persona_id="r1", team_role="researcher")
        fleet.launch_agent(name="R2", persona_id="r2", team_role="researcher")
        fleet.launch_agent(name="A1", persona_id="a1", team_role="analyst")

        researchers = fleet.get_agents_by_role("researcher")
        assert len(researchers) == 2

        analysts = fleet.get_agents_by_role("analyst")
        assert len(analysts) == 1

    def test_fleet_get_fleet_stats(self, running_fleet):
        """Test getting fleet statistics."""
        running_fleet.launch_agent(name="A1", persona_id="a1", team_role="researcher")
        running_fleet.launch_agent(name="A2", persona_id="a2", team_role="analyst")

        stats = running_fleet.get_fleet_stats()
        assert stats["total_agents"] == 2
        assert stats["running"] is True
        assert stats["active_tasks"] == 0
        assert stats["by_role"]["researcher"] == 1
        assert stats["by_role"]["analyst"] == 1

    def test_fleet_list_agents(self, running_fleet):
        """Test listing all agents."""
        running_fleet.launch_agent(name="A1", persona_id="a1", team_role="researcher")
        running_fleet.launch_agent(name="A2", persona_id="a2")

        agents = running_fleet.list_agents()
        assert len(agents) == 2
        assert agents[0]["name"] == "A1"
        assert agents[1]["name"] == "A2"


class TestLaunchConfig:
    """Tests for LaunchConfig and launcher functions."""

    def test_launch_config_defaults(self):
        """Test LaunchConfig defaults."""
        config = LaunchConfig()
        assert config.fleet_name == "default"
        assert config.max_agents == 10
        assert config.default_model == "gpt-4"
        assert config.default_temperature == 0.7

    def test_launch_preset_fleet_balanced(self):
        """Test launching a balanced preset fleet."""
        fleet, _ = launch_preset_fleet("balanced", count=1)
        assert fleet.config.fleet_name == "balanced"

    def test_launch_preset_fleet_research(self):
        """Test launching a research preset fleet."""
        fleet, _ = launch_preset_fleet("research", count=1)
        assert fleet.config.fleet_name == "research"

    def test_launch_preset_fleet_development(self):
        """Test launching a development preset fleet."""
        fleet, _ = launch_preset_fleet("development", count=1)
        assert fleet.config.fleet_name == "development"

    def test_launch_preset_fleet_writing(self):
        """Test launching a writing preset fleet."""
        fleet, _ = launch_preset_fleet("writing", count=1)
        assert fleet.config.fleet_name == "writing"


class TestAgentFleetConfig:
    """Tests for AgentFleetConfig."""

    def test_fleet_config_defaults(self):
        """Test AgentFleetConfig defaults."""
        config = AgentFleetConfig()
        assert config.default_model == "gpt-4"
        assert config.default_temperature == 0.7
        assert config.max_agents == 10
        assert config.max_concurrent_tasks == 5

    def test_fleet_config_custom(self):
        """Test custom AgentFleetConfig."""
        config = AgentFleetConfig(
            default_model="gpt-3.5-turbo",
            default_temperature=0.9,
            max_agents=20,
            max_concurrent_tasks=10,
        )
        assert config.default_model == "gpt-3.5-turbo"
        assert config.default_temperature == 0.9
        assert config.max_agents == 20
        assert config.max_concurrent_tasks == 10


class TestFleetFromBlueprints:
    """Tests for launching fleet from blueprints."""

    @pytest.fixture
    def blueprints_file(self):
        """Create a temporary blueprints file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            blueprints = {
                "agents": [
                    {
                        "id": "agent-1",
                        "name": "Researcher",
                        "description": "Research agent",
                        "persona_prompt": "You are a researcher.",
                        "capabilities": ["search", "analyze"],
                        "team_role": "researcher",
                        "handoff_triggers": [],
                    },
                    {
                        "id": "agent-2",
                        "name": "Analyst",
                        "description": "Analysis agent",
                        "persona_prompt": "You are an analyst.",
                        "capabilities": ["analyze", "interpret"],
                        "team_role": "analyst",
                        "handoff_triggers": [],
                    },
                ]
            }
            json.dump(blueprints, f)
            f.flush()
            yield f.name
            Path(f.name).unlink(missing_ok=True)

    def test_launch_from_blueprints(self, blueprints_file):
        """Test launching agents from blueprints file."""
        import asyncio

        async def _test():
            fleet = AgentFleet()
            await fleet.start()
            agents = await fleet.launch_agents_from_blueprints(
                blueprints_path=blueprints_file
            )
            return fleet, agents

        fleet, agents = asyncio.run(_test())
        assert len(fleet) == 2
        assert len(agents) == 2

    def test_launch_specific_blueprints(self, blueprints_file):
        """Test launching specific blueprints by ID."""
        import asyncio

        async def _test():
            fleet = AgentFleet()
            await fleet.start()
            agents = await fleet.launch_agents_from_blueprints(
                blueprints_path=blueprints_file,
                blueprint_ids=["agent-1"],
            )
            return fleet, agents

        fleet, agents = asyncio.run(_test())
        assert len(fleet) == 1
        assert agents[0].name == "Researcher"


class TestAgentCapability:
    """Tests for AgentCapability dataclass."""

    def test_agent_capability_creation(self):
        """Test creating an agent capability."""
        cap = AgentCapability(
            name="search",
            description="Search the web",
            confidence=0.95,
        )
        assert cap.name == "search"
        assert cap.description == "Search the web"
        assert cap.confidence == 0.95

    def test_agent_capability_default_confidence(self):
        """Test default confidence value."""
        cap = AgentCapability(name="test", description="Test capability")
        assert cap.confidence == 1.0
