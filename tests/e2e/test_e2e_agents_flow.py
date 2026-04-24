"""Comprehensive E2E tests for agents API.

Tests cover full CRUD operations, validation, error handling,
team operations, and edge cases for the agents blueprint system.
"""


from fastapi.testclient import TestClient

from chatty_commander.web.server import create_app


def _reset_agents_store():
    """Reset the agents store for test isolation."""
    try:
        from chatty_commander.web.routes import agents as _agents_mod

        _agents_mod._STORE.clear()
        _agents_mod._TEAM.clear()
    except Exception:
        pass


class TestCreateBlueprint:
    """Tests for creating agent blueprints."""

    def test_create_from_description(self):
        """Create blueprint from natural language description."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post(
            "/api/v1/agents/blueprints", json={"description": "Summarizer agent"}
        )
        assert r.status_code == 200
        bp = r.json()
        assert "id" in bp
        assert bp["name"]  # Should have extracted a name

    def test_create_with_full_payload(self):
        """Create blueprint with structured payload."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        payload = {
            "name": "ExpertAgent",
            "description": "An expert in answering questions",
            "persona_prompt": "You are a helpful expert.",
            "capabilities": ["reasoning", "analysis"],
            "team_role": "specialist",
            "handoff_triggers": ["complex_question"],
        }
        r = client.post("/api/v1/agents/blueprints", json=payload)
        assert r.status_code == 200
        bp = r.json()
        assert bp["name"] == "ExpertAgent"
        assert bp["capabilities"] == ["reasoning", "analysis"]
        assert bp["team_role"] == "specialist"

    def test_create_missing_required_fields(self):
        """Missing required fields should error."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post("/api/v1/agents/blueprints", json={})
        assert r.status_code == 400

    def test_create_missing_name(self):
        """Missing name should error."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post(
            "/api/v1/agents/blueprints",
            json={"description": "desc", "persona_prompt": "prompt"},
        )
        assert r.status_code == 400

    def test_create_empty_strings_accepted(self):
        """Empty strings are accepted (no min_length constraint)."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "",
                "description": "",
                "persona_prompt": "",
            },
        )
        # Pydantic accepts empty strings (no min_length constraint)
        assert r.status_code == 200

    def test_create_name_too_long(self):
        """Name exceeding max_length should error."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "x" * 201,  # Max is 200
                "description": "desc",
                "persona_prompt": "prompt",
            },
        )
        assert r.status_code == 422

    def test_create_description_too_long(self):
        """Description exceeding max_length should error."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "test",
                "description": "x" * 2001,  # Max is 2000
                "persona_prompt": "prompt",
            },
        )
        assert r.status_code == 422

    def test_create_unicode_name(self):
        """Unicode characters in name should work."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "中文代理",  # Chinese characters
                "description": "A Chinese agent",
                "persona_prompt": "你是一个助手",
            },
        )
        assert r.status_code == 200
        assert r.json()["name"] == "中文代理"

    def test_create_invalid_json(self):
        """Invalid JSON should error."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post(
            "/api/v1/agents/blueprints",
            content=b"not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 422


class TestListBlueprints:
    """Tests for listing agent blueprints."""

    def test_list_empty(self):
        """List with no blueprints should return empty list."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.get("/api/v1/agents/blueprints")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_includes_created(self):
        """List should include created blueprints."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        # Create two blueprints
        r1 = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "Agent1",
                "description": "First agent",
                "persona_prompt": "Prompt 1",
            },
        )
        r2 = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "Agent2",
                "description": "Second agent",
                "persona_prompt": "Prompt 2",
            },
        )
        uid1 = r1.json()["id"]
        uid2 = r2.json()["id"]

        r = client.get("/api/v1/agents/blueprints")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 2
        ids = [i["id"] for i in items]
        assert uid1 in ids
        assert uid2 in ids

    def test_list_response_schema(self):
        """List response should match expected schema."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "Test",
                "description": "Test agent",
                "persona_prompt": "Test prompt",
                "capabilities": ["test"],
            },
        )

        r = client.get("/api/v1/agents/blueprints")
        items = r.json()
        assert len(items) == 1
        item = items[0]
        # Verify all expected fields present
        assert "id" in item
        assert "name" in item
        assert "description" in item
        assert "persona_prompt" in item
        assert "capabilities" in item
        assert "team_role" in item
        assert "handoff_triggers" in item


class TestUpdateBlueprint:
    """Tests for updating agent blueprints."""

    def test_update_name(self):
        """Update blueprint name."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "Original",
                "description": "desc",
                "persona_prompt": "prompt",
            },
        )
        uid = r.json()["id"]

        r = client.put(
            f"/api/v1/agents/blueprints/{uid}",
            json={
                "name": "Updated",
                "description": "desc",
                "persona_prompt": "prompt",
            },
        )
        assert r.status_code == 200
        assert r.json()["name"] == "Updated"

    def test_update_capabilities(self):
        """Update blueprint capabilities."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "Test",
                "description": "desc",
                "persona_prompt": "prompt",
            },
        )
        uid = r.json()["id"]

        r = client.put(
            f"/api/v1/agents/blueprints/{uid}",
            json={
                "name": "Test",
                "description": "desc",
                "persona_prompt": "prompt",
                "capabilities": ["new_cap"],
            },
        )
        assert r.status_code == 200
        assert r.json()["capabilities"] == ["new_cap"]

    def test_update_team_role(self):
        """Update blueprint team role."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "Test",
                "description": "desc",
                "persona_prompt": "prompt",
                "team_role": "worker",
            },
        )
        uid = r.json()["id"]

        r = client.put(
            f"/api/v1/agents/blueprints/{uid}",
            json={
                "name": "Test",
                "description": "desc",
                "persona_prompt": "prompt",
                "team_role": "leader",
            },
        )
        assert r.status_code == 200
        assert r.json()["team_role"] == "leader"

    def test_update_nonexistent(self):
        """Update non-existent blueprint should error."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.put(
            "/api/v1/agents/blueprints/nonexistent-id",
            json={
                "name": "Test",
                "description": "desc",
                "persona_prompt": "prompt",
            },
        )
        assert r.status_code == 404


class TestDeleteBlueprint:
    """Tests for deleting agent blueprints."""

    def test_delete_existing(self):
        """Delete existing blueprint."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "ToDelete",
                "description": "desc",
                "persona_prompt": "prompt",
            },
        )
        uid = r.json()["id"]

        r = client.delete(f"/api/v1/agents/blueprints/{uid}")
        assert r.status_code == 200
        assert r.json()["deleted"] is True

        # Verify not in list
        r = client.get("/api/v1/agents/blueprints")
        ids = [i["id"] for i in r.json()]
        assert uid not in ids

    def test_delete_nonexistent(self):
        """Delete non-existent blueprint should error."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.delete("/api/v1/agents/blueprints/nonexistent-id")
        assert r.status_code == 404

    def test_delete_removes_from_team(self):
        """Deleting agent should remove from team relations."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        # Create with team role
        r = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "TeamMember",
                "description": "desc",
                "persona_prompt": "prompt",
                "team_role": "worker",
            },
        )
        uid = r.json()["id"]

        # Delete
        client.delete(f"/api/v1/agents/blueprints/{uid}")

        # Check team endpoint
        r = client.get("/api/v1/agents/team")
        team = r.json()
        # Agent should not appear in team roles
        for role_ids in team["roles"].values():
            assert uid not in role_ids


class TestTeamOperations:
    """Tests for team-related operations."""

    def test_get_team_empty(self):
        """Get team with no agents."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.get("/api/v1/agents/team")
        assert r.status_code == 200
        team = r.json()
        assert team["roles"] == {}
        assert team["agents"] == []

    def test_get_team_with_agents(self):
        """Get team with agents."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "Leader",
                "description": "desc",
                "persona_prompt": "prompt",
                "team_role": "leader",
            },
        )
        client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "Worker",
                "description": "desc",
                "persona_prompt": "prompt",
                "team_role": "worker",
            },
        )
        client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "NoRole",
                "description": "desc",
                "persona_prompt": "prompt",
                "team_role": None,
            },
        )

        r = client.get("/api/v1/agents/team")
        assert r.status_code == 200
        team = r.json()
        assert "leader" in team["roles"]
        assert "worker" in team["roles"]
        assert len(team["agents"]) == 3


class TestHandoff:
    """Tests for agent handoff operations."""

    def test_handoff_success(self):
        """Successful handoff between agents."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r1 = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "Agent1",
                "description": "desc",
                "persona_prompt": "prompt",
            },
        )
        r2 = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "Agent2",
                "description": "desc",
                "persona_prompt": "prompt",
            },
        )
        uid1 = r1.json()["id"]
        uid2 = r2.json()["id"]

        r = client.post(
            "/api/v1/agents/team/handoff",
            json={"from_agent_id": uid1, "to_agent_id": uid2, "reason": "test"},
        )
        assert r.status_code == 200
        result = r.json()
        assert result["ok"] is True
        assert result["from"] == uid1
        assert result["to"] == uid2

    def test_handoff_nonexistent_from(self):
        """Handoff from non-existent agent should error."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post(
            "/api/v1/agents/team/handoff",
            json={"from_agent_id": "nonexistent", "to_agent_id": "also-nonexistent"},
        )
        assert r.status_code == 404

    def test_handoff_missing_fields(self):
        """Handoff missing required fields should error."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post("/api/v1/agents/team/handoff", json={})
        assert r.status_code == 422


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_special_characters_in_name(self):
        """Special characters in name should work."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "Agent-123_test!@#",
                "description": "desc",
                "persona_prompt": "prompt",
            },
        )
        assert r.status_code == 200

    def test_very_long_persona_prompt(self):
        """Long persona prompt up to limit should work."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        long_prompt = "x" * 9999  # Max is 10000
        r = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "Test",
                "description": "desc",
                "persona_prompt": long_prompt,
            },
        )
        assert r.status_code == 200

    def test_empty_capabilities_list(self):
        """Empty capabilities list should work."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "Test",
                "description": "desc",
                "persona_prompt": "prompt",
                "capabilities": [],
            },
        )
        assert r.status_code == 200
        assert r.json()["capabilities"] == []

    def test_many_capabilities(self):
        """Many capabilities up to limit should work."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        # Max is 50
        caps = [f"cap_{i}" for i in range(50)]
        r = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "Test",
                "description": "desc",
                "persona_prompt": "prompt",
                "capabilities": caps,
            },
        )
        assert r.status_code == 200

    def test_too_many_capabilities(self):
        """Capabilities exceeding limit should error."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        # Max is 50
        caps = [f"cap_{i}" for i in range(51)]
        r = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "Test",
                "description": "desc",
                "persona_prompt": "prompt",
                "capabilities": caps,
            },
        )
        assert r.status_code == 422

    def test_extra_fields_rejected(self):
        """Extra fields should be rejected (extra='forbid')."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        r = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "Test",
                "description": "desc",
                "persona_prompt": "prompt",
                "unknown_field": "should_fail",
            },
        )
        assert r.status_code == 422


class TestCRUDRoundtrip:
    """End-to-end CRUD roundtrip tests."""

    def test_full_crud_roundtrip(self):
        """Complete CRUD roundtrip: create, read, update, delete."""
        _reset_agents_store()
        app = create_app(no_auth=True)
        client = TestClient(app)

        # CREATE
        r = client.post(
            "/api/v1/agents/blueprints",
            json={
                "name": "CRUDTest",
                "description": "Original description",
                "persona_prompt": "Original prompt",
                "capabilities": ["test"],
                "team_role": "tester",
            },
        )
        assert r.status_code == 200
        uid = r.json()["id"]

        # READ (via list)
        r = client.get("/api/v1/agents/blueprints")
        assert any(a["id"] == uid for a in r.json())

        # UPDATE
        r = client.put(
            f"/api/v1/agents/blueprints/{uid}",
            json={
                "name": "CRUDTest-Updated",
                "description": "Updated description",
                "persona_prompt": "Updated prompt",
                "capabilities": ["test", "updated"],
                "team_role": None,
            },
        )
        assert r.status_code == 200
        updated = r.json()
        assert updated["name"] == "CRUDTest-Updated"
        assert "updated" in updated["capabilities"]

        # DELETE
        r = client.delete(f"/api/v1/agents/blueprints/{uid}")
        assert r.status_code == 200

        # VERIFY DELETED
        r = client.get("/api/v1/agents/blueprints")
        assert not any(a["id"] == uid for a in r.json())
