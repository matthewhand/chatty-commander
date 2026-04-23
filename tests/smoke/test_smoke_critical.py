"""Smoke tests - critical path verification.
Fast tests to verify basic system health.
"""

import pytest


class TestSystemHealth:
    """Critical health checks."""
    
    def test_imports_work(self):
        """Verify core modules can be imported."""
        from chatty_commander import app
        from chatty_commander.llm import manager
        from chatty_commander.voice import wakeword
        assert True
    
    def test_config_loads(self):
        """Verify configuration can be loaded."""
        # TODO: Add config loading test
        pass
    
    def test_voice_pipeline_init(self):
        """Verify voice pipeline can be initialized."""
        # TODO: Add voice pipeline test
        pass


class TestAPIHealth:
    """API endpoint health checks."""
    
    def test_version_endpoint(self, client):
        """Version endpoint returns 200."""
        response = client.get("/version")
        assert response.status_code == 200
    
    def test_health_endpoint(self, client):
        """Health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"


class TestCriticalFlows:
    """Critical user flows."""
    
    def test_cli_help_works(self):
        """CLI help command executes."""
        import subprocess
        result = subprocess.run(
            ["python", "-m", "chatty_commander", "--help"],
            capture_output=True,
            timeout=5
        )
        assert result.returncode == 0
