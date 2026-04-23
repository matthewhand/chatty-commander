# fixtures/agents.py
"""Test fixtures for agent-related tests."""

from unittest.mock import Mock

import pytest


class AgentFixtures:
    """Factory for agent test data."""
    
    @staticmethod
    def create_agent_blueprint(
        name="Test Agent",
        capabilities=None,
        personality="helpful",
        avatar="default"
    ):
        """Create a standard agent blueprint for testing."""
        return {
            "name": name,
            "capabilities": capabilities or ["speak", "listen", "process"],
            "personality": personality,
            "avatar": avatar,
            "status": "active",
            "version": "1.0.0"
        }
    
    @staticmethod
    def create_mock_agent():
        """Create a mock agent with common methods stubbed."""
        agent = Mock()
        agent.name = "TestAgent"
        agent.process_command.return_value = {"success": True}
        agent.get_status.return_value = "idle"
        agent.is_available.return_value = True
        return agent
    
    @staticmethod
    def create_agent_team(count=3):
        """Create a team of test agents."""
        return [
            AgentFixtures.create_agent_blueprint(f"Agent {i}")
            for i in range(count)
        ]


# Pytest fixtures
@pytest.fixture
def agent_blueprint():
    """Provide a standard agent blueprint."""
    return AgentFixtures.create_agent_blueprint()


@pytest.fixture
def mock_agent():
    """Provide a mock agent."""
    return AgentFixtures.create_mock_agent()


@pytest.fixture
def agent_team():
    """Provide a team of test agents."""
    return AgentFixtures.create_agent_team()


# Keep old name for compatibility
agent_fixtures = AgentFixtures
