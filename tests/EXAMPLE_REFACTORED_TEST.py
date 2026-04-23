#!/usr/bin/env python3
"""
EXAMPLE: Refactored Test Using New DRY Patterns

This demonstrates the ideal test structure after applying the test strategy.
Compare with legacy tests to see the improvements.
"""

import pytest

# Import from fixtures package
from tests.fixtures.agents import agent_fixtures
from tests.fixtures.commands import command_fixtures
from tests.fixtures.configs import config_fixtures

# Import from helpers package
from tests.helpers import MockFactory, TestAssertions


# ============================================================================
# EXAMPLE 1: Unit Test with Mocks (DRY Pattern)
# ============================================================================

class TestCommandExecutorUnit:
    """
    Unit tests for CommandExecutor with mocked dependencies.
    
    Uses MockFactory for consistent setup and follows AAA pattern.
    """
    
    def test_execute_valid_command_succeeds(self):
        """
        Test that executing a valid registered command returns success.
        
        This is critical because command execution is the primary
        function of the executor.
        """
        # Arrange - Use MockFactory for consistent setup
        config = config_fixtures.create_mock_config({
            "model_actions": {
                "open_browser": {"type": "url", "url": "https://google.com"}
            }
        })
        executor = MockFactory.create_mock_command_executor()
        executor.config = config
        
        # Act
        result = executor.execute_command("open_browser")
        
        # Assert - Use assertion helper for clarity
        TestAssertions.assert_valid_command_result(result, expected_success=True)
        executor.execute_command.assert_called_once_with("open_browser")
    
    def test_execute_invalid_command_fails(self):
        """
        Test that executing an unregistered command returns failure.
        
        Invalid commands should fail gracefully without side effects.
        """
        # Arrange
        config = config_fixtures.create_mock_config({"model_actions": {}})
        executor = MockFactory.create_mock_command_executor()
        executor.config = config
        executor.validate_command.return_value = False
        
        # Act
        result = executor.execute_command("nonexistent")
        
        # Assert
        TestAssertions.assert_valid_command_result(result, expected_success=False)


# ============================================================================
# EXAMPLE 2: Integration Test with Real Components
# ============================================================================

class TestCommandExecutorIntegration:
    """
    Integration tests using real dependencies but isolated services.
    
    These test the actual interaction between components.
    """
    
    @pytest.fixture
    def command_executor(self, mock_config, mock_state_manager):
        """Provide a real CommandExecutor with mocked dependencies."""
        from chatty_commander.app.command_executor import CommandExecutor
        
        return CommandExecutor(
            config=mock_config,
            state_manager=mock_state_manager,
            model_manager=MockFactory.create_mock_model_manager()
        )
    
    def test_command_triggers_state_change(self, command_executor, mock_state_manager):
        """
        Test that command execution notifies state manager.
        
        Integration point between executor and state management.
        """
        # Arrange
        command_executor.config.model_actions = {
            "computer_mode": {"type": "state_change", "state": "computer"}
        }
        
        # Act
        command_executor.execute_command("computer_mode")
        
        # Assert - Use assertion helper for state transitions
        TestAssertions.assert_state_transition(
            mock_state_manager,
            to_state="computer"
        )


# ============================================================================
# EXAMPLE 3: API Test with Fixtures
# ============================================================================

class TestAgentAPI:
    """
    API endpoint tests using FastAPI TestClient.
    
    Tests the full request/response cycle.
    """
    
    def test_create_agent_returns_201(self, client, agent_blueprint):
        """
        Test that creating a new agent returns 201 Created.
        
        HTTP contract test for the agents API.
        """
        # Act
        response = client.post("/agents", json=agent_blueprint)
        
        # Assert - Use assertion helper for API responses
        data = TestAssertions.assert_valid_json_response(
            response,
            expected_keys=["id", "name", "status"],
            status_code=201
        )
        assert data["name"] == agent_blueprint["name"]
    
    def test_get_nonexistent_agent_returns_404(self, client):
        """
        Test that requesting unknown agent returns proper error.
        
        Error handling contract test.
        """
        # Act
        response = client.get("/agents/nonexistent-id-12345")
        
        # Assert
        TestAssertions.assert_error_response(response, expected_status=404)


# ============================================================================
# EXAMPLE 4: Parameterized Tests with Shared Data
# ============================================================================

# Define test cases once, use everywhere
AGENT_COMMAND_CASES = [
    ("open_browser", {"type": "url", "url": "https://google.com"}, True),
    ("play_music", {"type": "shell", "command": "playerctl play"}, True),
    ("stop_music", {"type": "shell", "command": "playerctl stop"}, True),
    ("invalid_command", None, False),
]


class TestCommandVariations:
    """
    Parameterized tests for different command types.
    
    Uses shared test cases to avoid duplication.
    """
    
    @pytest.mark.parametrize("command_name,config,expected_success", AGENT_COMMAND_CASES)
    def test_command_execution(self, command_name, config, expected_success, mock_executor):
        """
        Test command execution for various command types.
        
        Parameterized to cover multiple scenarios without code duplication.
        """
        # Arrange
        if config:
            mock_executor.config.model_actions = {command_name: config}
        mock_executor.validate_command.return_value = config is not None
        
        # Act
        result = mock_executor.execute_command(command_name)
        
        # Assert
        TestAssertions.assert_valid_command_result(result, expected_success)


# ============================================================================
# EXAMPLE 5: E2E Test with Browser Automation
# ============================================================================

@pytest.mark.e2e
class TestVoiceWorkflowE2E:
    """
    End-to-end test of complete voice interaction workflow.
    
    Uses Playwright for browser automation.
    """
    
    def test_full_voice_command_workflow(self, page, e2e_server):
        """
        Test: wake word -> voice input -> command execution -> confirmation.
        
        Critical user journey that spans multiple components.
        """
        # Navigate to app
        page.goto(f"{e2e_server}/app")
        
        # Trigger wake word (simulated)
        page.evaluate("window.simulateWakeWord('hey computer')")
        
        # Wait for listening state
        page.wait_for_selector("[data-state='listening']", timeout=5000)
        
        # Simulate voice input
        page.evaluate("window.simulateVoiceInput('open browser')")
        
        # Wait for processing
        page.wait_for_selector("[data-state='processing']", timeout=5000)
        
        # Verify success
        result = page.evaluate("window.lastCommandResult")
        assert result["success"] is True
        assert result["command"] == "open_browser"


# ============================================================================
# BENEFITS OF THIS APPROACH
# ============================================================================

"""
1. DRY (Don't Repeat Yourself)
   - MockFactory creates consistent mocks
   - Fixtures provide shared test data
   - Assertion helpers reduce duplication

2. Readability
   - Clear AAA structure in every test
   - Descriptive docstrings explain WHY
   - Type hints for clarity

3. Maintainability
   - Change mock behavior in one place
   - Update fixtures, all tests get new data
   - Shared assertion logic

4. Test Pyramid Compliance
   - Unit tests: 70% fast, isolated
   - Integration: 20% service boundaries
   - E2E tests: 10% critical workflows

5. Quality Gates
   - Fast feedback (< 100ms unit tests)
   - Clear failure messages
   - Consistent patterns across codebase
"""
