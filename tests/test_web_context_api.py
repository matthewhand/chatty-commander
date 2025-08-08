"""
Integration tests for context-aware web API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from chatty_commander.web.web_mode import WebModeServer


class TestWebContextAPI:
    """Test context-aware web API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client with advisors enabled."""
        config = {
            'advisors': {
                'enabled': True,
                'context': {
                    'personas': {
                        'general': {'system_prompt': 'You are helpful.'},
                        'philosopher': {'system_prompt': 'You are philosophical.'},
                        'discord_default': {'system_prompt': 'You are a Discord bot.'},
                        'slack_default': {'system_prompt': 'You are a Slack app.'}
                    },
                    'default_persona': 'general',
                    'persistence_enabled': False
                },
                'providers': {
                    'llm_api_mode': 'completion',
                    'model': 'gpt-oss20b'
                },
                'memory': {
                    'persistence_enabled': False
                }
            }
        }
        
        server = WebModeServer(config)
        return TestClient(server.app)
    
    def test_advisor_message_creates_context(self, client):
        """Test that sending a message creates a context."""
        response = client.post("/api/v1/advisors/message", json={
            "platform": "discord",
            "channel": "123456789",
            "user": "user123",
            "text": "Hello advisor",
            "username": "testuser"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "reply" in data
        assert "context_key" in data
        assert "persona_id" in data
        assert "model" in data
        assert "api_mode" in data
        
        # Should create Discord-specific persona
        assert data["persona_id"] == "discord_default"
        assert "discord:123456789:user123" in data["context_key"]
    
    def test_advisor_message_existing_context(self, client):
        """Test that existing context is reused."""
        # Send first message
        response1 = client.post("/api/v1/advisors/message", json={
            "platform": "slack",
            "channel": "general",
            "user": "user456",
            "text": "First message"
        })
        
        # Send second message
        response2 = client.post("/api/v1/advisors/message", json={
            "platform": "slack",
            "channel": "general",
            "user": "user456",
            "text": "Second message"
        })
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Should have same context key
        assert data1["context_key"] == data2["context_key"]
        assert data1["persona_id"] == data2["persona_id"]
    
    def test_switch_persona(self, client):
        """Test switching persona for a context."""
        # Create context first
        response = client.post("/api/v1/advisors/message", json={
            "platform": "web",
            "channel": "chat",
            "user": "user789",
            "text": "Hello"
        })
        
        assert response.status_code == 200
        data = response.json()
        context_key = data["context_key"]
        
        # Switch persona
        switch_response = client.post("/api/v1/advisors/context/switch", 
                                   params={"context_key": context_key, "persona_id": "philosopher"})
        
        assert switch_response.status_code == 200
        switch_data = switch_response.json()
        
        assert switch_data["success"] is True
        assert switch_data["context_key"] == context_key
        assert switch_data["persona_id"] == "philosopher"
    
    def test_switch_persona_invalid(self, client):
        """Test switching to invalid persona."""
        # Create context first
        response = client.post("/api/v1/advisors/message", json={
            "platform": "discord",
            "channel": "test",
            "user": "user123",
            "text": "Hello"
        })
        
        assert response.status_code == 200
        data = response.json()
        context_key = data["context_key"]
        
        # Try to switch to invalid persona
        switch_response = client.post("/api/v1/advisors/context/switch", 
                                   params={"context_key": context_key, "persona_id": "nonexistent"})
        
        assert switch_response.status_code == 400
        assert "Invalid persona" in switch_response.json()["detail"]
    
    def test_get_context_stats(self, client):
        """Test getting context statistics."""
        # Create some contexts
        client.post("/api/v1/advisors/message", json={
            "platform": "discord",
            "channel": "channel1",
            "user": "user1",
            "text": "Hello"
        })
        
        client.post("/api/v1/advisors/message", json={
            "platform": "discord",
            "channel": "channel2",
            "user": "user2",
            "text": "Hello"
        })
        
        client.post("/api/v1/advisors/message", json={
            "platform": "slack",
            "channel": "general",
            "user": "user3",
            "text": "Hello"
        })
        
        # Get stats
        response = client.get("/api/v1/advisors/context/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_contexts"] == 3
        assert data["platform_distribution"]["discord"] == 2
        assert data["platform_distribution"]["slack"] == 1
        assert data["persona_distribution"]["discord_default"] == 2
        assert data["persona_distribution"]["slack_default"] == 1
        assert data["persistence_enabled"] is False
    
    def test_clear_context(self, client):
        """Test clearing a specific context."""
        # Create context
        response = client.post("/api/v1/advisors/message", json={
            "platform": "web",
            "channel": "test",
            "user": "user123",
            "text": "Hello"
        })
        
        assert response.status_code == 200
        data = response.json()
        context_key = data["context_key"]
        
        # Clear context
        clear_response = client.delete(f"/api/v1/advisors/context/{context_key}")
        
        assert clear_response.status_code == 200
        clear_data = clear_response.json()
        
        assert clear_data["success"] is True
        assert clear_data["context_key"] == context_key
    
    def test_clear_context_not_found(self, client):
        """Test clearing non-existent context."""
        response = client.delete("/api/v1/advisors/context/nonexistent")
        
        assert response.status_code == 404
        assert "Context not found" in response.json()["detail"]
    
    def test_summarize_command(self, client):
        """Test the summarize command."""
        response = client.post("/api/v1/advisors/message", json={
            "platform": "web",
            "channel": "test",
            "user": "user123",
            "text": "summarize https://example.com"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "Summary of https://example.com" in data["reply"]
        assert data["persona_id"] == "analyst"
        assert data["context_key"] == "summarize"
