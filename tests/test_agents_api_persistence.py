import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import json

from chatty_commander.web.routes.agents import AgentBlueprintModel


def test_agent_persistence():
    # We will simulate starting and stopping by loading module dynamically or clearing state
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "agents.json"

        # Patch the environment variable to use our temporary store path
        with patch.dict(os.environ, {"CHATTY_AGENTS_STORE": str(store_path)}):
            # Important: import module *inside* the patch so the initial path is correct
            import chatty_commander.web.routes.agents as agents_mod
            import importlib

            # Force reload to pick up the mocked env var
            importlib.reload(agents_mod)

            # Start with clear store (ensure tests don't pollute each other)
            agents_mod._STORE.clear()
            agents_mod._TEAM.clear()

            # Make sure the file does not exist yet
            assert not store_path.exists()

            # Create a mock blueprint
            bp = AgentBlueprintModel(
                name="TestAgent",
                description="Test description",
                persona_prompt="You are a test agent.",
                capabilities=["test"],
                team_role="tester"
            )

            # Add to store and save (simulating the endpoint logic)
            # We bypass the endpoints for a pure persistence check,
            # or we could use TestClient.
            # Let's mock the endpoint's behavior manually first
            from chatty_commander.web.routes.agents import AgentBlueprint
            from uuid import uuid4

            uid = str(uuid4())
            ent = AgentBlueprint(id=uid, **bp.model_dump())
            agents_mod._STORE[uid] = ent
            if ent.team_role:
                agents_mod._TEAM.setdefault(ent.team_role, []).append(uid)
            agents_mod._save_store()

            # Verify file was created
            assert store_path.exists()
            with store_path.open("r", encoding="utf-8") as f:
                saved_data = json.load(f)
                assert "agents" in saved_data
                assert len(saved_data["agents"]) == 1
                assert saved_data["agents"][0]["name"] == "TestAgent"

            # Clear memory to simulate restart
            agents_mod._STORE.clear()
            agents_mod._TEAM.clear()

            assert len(agents_mod._STORE) == 0

            # Reload module to simulate process restart
            importlib.reload(agents_mod)

            # Verify data is loaded back
            assert len(agents_mod._STORE) == 1
            assert uid in agents_mod._STORE
            loaded_ent = agents_mod._STORE[uid]
            assert loaded_ent.name == "TestAgent"
            assert loaded_ent.team_role == "tester"
            assert "tester" in agents_mod._TEAM
            assert uid in agents_mod._TEAM["tester"]
