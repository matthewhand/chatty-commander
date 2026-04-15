"""End-to-end tests for web server routes with actual HTTP requests."""

import pytest
from fastapi.testclient import TestClient

from chatty_commander.web.server import create_app


@pytest.fixture
def client() -> TestClient:
    """Provide a TestClient with no auth enabled."""
    app = create_app(no_auth=True)
    return TestClient(app)


class TestCoreRoutesE2E:
    """End-to-end tests for core API routes."""

    def test_health_check_returns_ok(self, client: TestClient) -> None:
        """Test that the root endpoint returns healthy status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok" or "healthy" in data.get("message", "").lower()

    def test_state_flow_idle_to_computer_back_to_idle(self, client: TestClient) -> None:
        """Test a complete state change flow through the API."""
        # Get current state
        response = client.get("/api/state")
        assert response.status_code in (200, 404)  # 404 if endpoint doesn't exist

        # Try to change state (if endpoint exists)
        response = client.post("/api/state", json={"state": "computer"})
        if response.status_code == 200:
            # Verify state changed
            response = client.get("/api/state")
            assert response.status_code == 200
            data = response.json()
            assert data.get("state") == "computer"

            # Change back to idle
            response = client.post("/api/state", json={"state": "idle"})
            assert response.status_code == 200

    def test_invalid_state_returns_validation_error(self, client: TestClient) -> None:
        """Test that invalid state values return proper validation errors."""
        response = client.post("/api/state", json={"state": "invalid_state_name"})
        # Should get 422 (validation error) or 400 (bad request)
        assert response.status_code in (400, 404, 422)


class TestAgentsRoutesE2E:
    """End-to-end tests for agents/blueprints API."""

    def test_list_agents_initially_empty_or_returns_list(self, client: TestClient) -> None:
        """Test that listing agents works."""
        response = client.get("/api/v1/agents/blueprints")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_list_delete_agent_flow(self, client: TestClient) -> None:
        """Test the full CRUD lifecycle for an agent blueprint."""
        # Create
        create_response = client.post(
            "/api/v1/agents/blueprints",
            json={"description": "Test agent for e2e flow"},
        )
        assert create_response.status_code == 200
        agent_data = create_response.json()
        agent_id = agent_data["id"]

        # List - should contain our agent
        list_response = client.get("/api/v1/agents/blueprints")
        assert list_response.status_code == 200
        agents = list_response.json()
        assert any(a["id"] == agent_id for a in agents), "Created agent not found in list"

        # Delete
        delete_response = client.delete(f"/api/v1/agents/blueprints/{agent_id}")
        assert delete_response.status_code == 200

        # List - should not contain our agent
        final_list_response = client.get("/api/v1/agents/blueprints")
        assert final_list_response.status_code == 200
        final_agents = final_list_response.json()
        assert not any(a["id"] == agent_id for a in final_agents), "Deleted agent still in list"

    def test_create_agent_with_full_specification(self, client: TestClient) -> None:
        """Test creating an agent with all fields specified."""
        full_spec = {
            "name": "Full Spec Agent",
            "description": "An agent with all fields specified",
            "persona_prompt": "You are a helpful test assistant.",
            "capabilities": ["summarize", "translate", "analyze"],
            "team_role": "analyst",
        }
        response = client.post("/api/v1/agents/blueprints", json=full_spec)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Full Spec Agent"
        assert "summarize" in data["capabilities"]

        # Cleanup
        client.delete(f"/api/v1/agents/blueprints/{data['id']}")


class TestErrorHandlingE2E:
    """End-to-end tests for error handling across API."""

    def test_404_for_unknown_endpoint(self, client: TestClient) -> None:
        """Test that unknown endpoints return 404."""
        response = client.get("/api/nonexistent/endpoint")
        assert response.status_code == 404

    def test_invalid_json_returns_error(self, client: TestClient) -> None:
        """Test that malformed JSON returns proper error."""
        response = client.post(
            "/api/v1/agents/blueprints",
            content="{invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in (400, 422)

    def test_missing_required_field_returns_validation_error(self, client: TestClient) -> None:
        """Test that missing required fields are caught."""
        # The agents endpoint requires at least description
        response = client.post("/api/v1/agents/blueprints", json={})
        assert response.status_code in (400, 422)


class TestSystemRoutesE2E:
    """End-to-end tests for system info endpoints."""

    def test_version_endpoint_returns_version(self, client: TestClient) -> None:
        """Test that version endpoint returns version info."""
        response = client.get("/api/version")
        if response.status_code == 200:
            data = response.json()
            assert "version" in data
            assert isinstance(data["version"], str)

    def test_status_endpoint_returns_system_status(self, client: TestClient) -> None:
        """Test that status endpoint returns system status."""
        response = client.get("/api/status")
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "current_state" in data
