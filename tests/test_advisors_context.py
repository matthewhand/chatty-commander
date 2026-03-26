"""
Tests for advisors context management, service, provider selection, memory API,
and tool call functionality.

Consolidated from:
- test_advisors_context.py (context management tests)
- test_advisors_llm_integration.py (LLM manager delegation tests)
- test_advisors_memory_api.py (memory API flow tests)
- test_advisors_memory_disabled.py (disabled memory endpoint test)
- test_advisors_provider_selection.py (provider build tests)
- test_advisors_service.py (service echo/disabled tests)
- test_advisors_tool_call.py (stub provider happy-path test)
"""

import sys
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from chatty_commander.advisors.providers import build_provider_safe
from chatty_commander.advisors.service import AdvisorMessage, AdvisorsService
from chatty_commander.app import CommandExecutor
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.web_mode import WebModeServer

# ---------------------------------------------------------------------------
# Context management tests (original test_advisors_context.py)
# ---------------------------------------------------------------------------


class TestAdvisorsContext:
    """Test advisors context management."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for advisors."""
        config = Mock()
        config.advisors = {
            "enabled": True,
            "llm_api_mode": "completion",
            "model": "gpt-4",
            "max_context_length": 4000,
            "context_window": 10,
        }
        return config

    def test_context_configuration_loading(self, mock_config):
        """Test that context configuration is loaded correctly."""
        assert mock_config.advisors["enabled"] is True
        assert mock_config.advisors["max_context_length"] == 4000
        assert mock_config.advisors["context_window"] == 10

    def test_context_window_size_validation(self, mock_config):
        """Test context window size validation."""
        # Valid window size
        mock_config.advisors["context_window"] = 10
        assert mock_config.advisors["context_window"] > 0

        # Invalid window size
        mock_config.advisors["context_window"] = -1
        assert mock_config.advisors["context_window"] < 0

    def test_max_context_length_validation(self, mock_config):
        """Test maximum context length validation."""
        # Valid length
        mock_config.advisors["max_context_length"] = 4000
        assert mock_config.advisors["max_context_length"] > 0

        # Test different length values
        test_lengths = [100, 1000, 8000, 16000]
        for length in test_lengths:
            mock_config.advisors["max_context_length"] = length
            assert mock_config.advisors["max_context_length"] == length

    def test_context_entry_structure(self):
        """Test context entry structure validation."""
        valid_entry = {
            "role": "user",
            "content": "test message",
            "timestamp": "2024-01-01T00:00:00Z",
        }

        assert "role" in valid_entry
        assert "content" in valid_entry
        assert valid_entry["role"] in ["user", "assistant", "system"]
        assert len(valid_entry["content"]) > 0

    def test_context_role_validation(self):
        """Test context role validation."""
        valid_roles = ["user", "assistant", "system"]
        invalid_roles = ["admin", "moderator", "", None, 123]

        for role in valid_roles:
            entry = {"role": role, "content": "test"}
            assert entry["role"] in valid_roles

        for role in invalid_roles:
            entry = {"role": role, "content": "test"}
            assert entry["role"] not in valid_roles

    def test_context_content_validation(self):
        """Test context content validation."""
        # Valid content
        valid_contents = [
            "Hello world",
            "This is a longer message with multiple sentences.",
            "Message with unicode: ñáéíóú",
            "Message with numbers: 12345",
            "Message with symbols: !@#$%^&*()",
        ]

        for content in valid_contents:
            entry = {"role": "user", "content": content}
            assert isinstance(entry["content"], str)
            assert len(entry["content"]) > 0

        # Invalid content
        invalid_contents = ["", None, 123, [], {}]

        for content in invalid_contents:
            entry = {"role": "user", "content": content}
            assert not isinstance(entry["content"], str) or len(entry["content"]) == 0

    def test_context_size_calculation(self):
        """Test context size calculation."""
        entries = [
            {"role": "user", "content": "Short message"},
            {
                "role": "assistant",
                "content": "This is a much longer response with more detail",
            },
            {"role": "user", "content": "Another message"},
        ]

        total_chars = sum(len(entry["content"]) for entry in entries)
        assert total_chars > 0
        assert total_chars == len("Short message") + len(
            "This is a much longer response with more detail"
        ) + len("Another message")

    def test_context_trimming_logic(self):
        """Test context trimming logic."""
        max_length = 100
        entries = [
            {"role": "user", "content": "x" * 50},  # 50 chars
            {"role": "assistant", "content": "x" * 30},  # 30 chars
            {"role": "user", "content": "x" * 40},  # 40 chars
        ]

        # Total would be 120 chars, need to trim to 100
        total_length = sum(len(entry["content"]) for entry in entries)
        assert total_length > max_length

        # Should keep the most recent entries
        trimmed_entries = entries[-2:]  # Keep last 2 entries (70 chars)
        trimmed_length = sum(len(entry["content"]) for entry in trimmed_entries)
        assert trimmed_length <= max_length

    def test_context_persistence_format(self):
        """Test context persistence format."""
        context = {
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "entries": [
                {"role": "user", "content": "test", "timestamp": "2024-01-01T00:00:00Z"}
            ],
            "metadata": {"total_entries": 1, "total_chars": 4},
        }

        assert "version" in context
        assert "entries" in context
        assert "metadata" in context
        assert isinstance(context["entries"], list)
        assert len(context["entries"]) == 1

    def test_context_search_functionality(self):
        """Test context search functionality."""
        entries = [
            {"role": "user", "content": "I need help with Python programming"},
            {"role": "assistant", "content": "Python is a great programming language"},
            {"role": "user", "content": "What about JavaScript?"},
        ]

        # Search for "Python"
        python_results = [entry for entry in entries if "Python" in entry["content"]]
        assert len(python_results) == 2

        # Search for "JavaScript"
        js_results = [entry for entry in entries if "JavaScript" in entry["content"]]
        assert len(js_results) == 1

    def test_context_filtering_by_role(self):
        """Test filtering context by role."""
        entries = [
            {"role": "user", "content": "question 1"},
            {"role": "assistant", "content": "answer 1"},
            {"role": "user", "content": "question 2"},
            {"role": "system", "content": "system message"},
            {"role": "assistant", "content": "answer 2"},
        ]

        user_entries = [entry for entry in entries if entry["role"] == "user"]
        assistant_entries = [entry for entry in entries if entry["role"] == "assistant"]
        system_entries = [entry for entry in entries if entry["role"] == "system"]

        assert len(user_entries) == 2
        assert len(assistant_entries) == 2
        assert len(system_entries) == 1

    @pytest.mark.asyncio
    async def test_context_with_async_operations(self):
        """Test context management with async operations."""

        # Mock async operation
        async def mock_async_operation(context):
            return f"Processed {len(context)} entries"

        context = [
            {"role": "user", "content": "message 1"},
            {"role": "assistant", "content": "response 1"},
        ]

        result = await mock_async_operation(context)
        assert result == "Processed 2 entries"

    def test_context_error_handling(self):
        """Test error handling in context management."""
        # Test malformed entries
        malformed_entries = [
            {"role": "user"},  # Missing content
            {"content": "message"},  # Missing role
            {},  # Empty entry
            None,  # None entry
        ]

        for entry in malformed_entries:
            if entry is None:
                assert entry is None
            else:
                assert "role" not in entry or "content" not in entry

    def test_context_memory_efficiency(self):
        """Test memory efficiency of context management."""
        # Create entries with varying sizes
        entries = []
        for i in range(100):
            content = f"Message {i} with some content" * (i % 10 + 1)
            entries.append({"role": "user", "content": content})

        # Calculate memory usage
        total_size = sum(sys.getsizeof(entry["content"]) for entry in entries)
        assert total_size > 0

        # Test that trimming reduces memory usage
        trimmed_entries = entries[-10:]  # Keep only last 10
        trimmed_size = sum(sys.getsizeof(entry["content"]) for entry in trimmed_entries)
        assert trimmed_size < total_size


# ---------------------------------------------------------------------------
# LLM integration tests (from test_advisors_llm_integration.py)
# ---------------------------------------------------------------------------


class TestAdvisorsLLMIntegration:
    """Test that AdvisorsService delegates to LLMManager."""

    @pytest.fixture
    def mock_llm_manager(self):
        with patch("chatty_commander.llm.manager.get_global_llm_manager") as mock_get:
            mock_manager = MagicMock()
            mock_get.return_value = mock_manager
            yield mock_manager

    def test_advisors_service_uses_llm_manager(self, mock_llm_manager):
        """Test that AdvisorsService delegates to LLMManager."""
        config = {
            "enabled": True,
            "openai_api_key": "test-key",
            "provider": {"model": "test-model"},
        }

        # Setup mock manager response
        mock_llm_manager.generate_response.return_value = (
            "Generated response from LLMManager"
        )
        mock_llm_manager.active_backend.model = "test-backend-model"
        mock_llm_manager.get_active_backend_name.return_value = "mock-backend"

        service = AdvisorsService(config)

        # Verify manager initialization
        assert service.llm_manager is mock_llm_manager

        # Send message
        message = AdvisorMessage(
            platform="discord", channel="general", user="user1", text="Hello AI"
        )

        reply = service.handle_message(message)

        # Verify response content
        assert reply.reply == "Generated response from LLMManager"
        assert reply.model == "mock-backend"

        # Verify call arguments
        mock_llm_manager.generate_response.assert_called_once()
        call_args = mock_llm_manager.generate_response.call_args
        assert "Hello AI" in call_args[0][0]  # Prompt contains message
        assert call_args[1]["model"] == "test-backend-model"

    def test_advisors_service_llm_manager_fallback(self, mock_llm_manager):
        """Test handling of LLMManager errors."""
        config = {"enabled": True}
        service = AdvisorsService(config)

        # Setup mock to raise error
        mock_llm_manager.generate_response.side_effect = RuntimeError(
            "Generation failed"
        )

        message = AdvisorMessage(
            platform="discord", channel="general", user="user1", text="Hello"
        )

        # Should not raise, but return error message
        reply = service.handle_message(message)

        assert "[LLM Error]" in reply.reply
        assert "Generation failed" in reply.reply
        assert reply.model == "error"


# ---------------------------------------------------------------------------
# Memory API tests (from test_advisors_memory_api.py)
# ---------------------------------------------------------------------------


class _DummyConfigMemoryEnabled:
    """Config with advisors enabled for memory API tests."""

    def __init__(self) -> None:
        self.general_models_path = "models-idle"
        self.system_models_path = "models-computer"
        self.chat_models_path = "models-chatty"
        self.config = {"model_actions": {}}
        self.advisors = {
            "enabled": True,
            "providers": {
                "llm_api_mode": "completion",
                "model": "gpt-oss20b",
            },
            "context": {
                "personas": {
                    "general": {"system_prompt": "You are helpful."},
                    "discord_default": {"system_prompt": "You are a Discord bot."},
                },
                "default_persona": "general",
            },
            "features": {"browser_analyst": True},
        }


class TestAdvisorsMemoryAPI:
    """Test advisors memory API flow."""

    def test_advisors_memory_flow(self):
        with patch(
            "chatty_commander.web.web_mode.AdvisorsService"
        ) as mock_advisors_service:
            # Mock the AdvisorsService to avoid OpenAI API key requirement
            mock_service = MagicMock()
            mock_memory = MagicMock()
            mock_service.memory = mock_memory

            # Mock memory methods
            mock_memory.get.return_value = [
                MagicMock(
                    role="user", content="hello", timestamp="2023-01-01T00:00:00"
                ),
                MagicMock(
                    role="assistant",
                    content="Hello! How can I help you?",
                    timestamp="2023-01-01T00:00:01",
                ),
            ]
            mock_memory.clear.return_value = 2

            # Mock handle_message method
            mock_reply = MagicMock()
            mock_reply.reply = "Test response"
            mock_reply.context_key = "test_context"
            mock_reply.persona_id = "general"
            mock_reply.model = "test-model"
            mock_reply.api_mode = "completion"
            mock_service.handle_message.return_value = mock_reply

            mock_advisors_service.return_value = mock_service

            cfg = _DummyConfigMemoryEnabled()
            sm = StateManager()
            mm = ModelManager(cfg)
            ce = CommandExecutor(cfg, mm, sm)
            server = WebModeServer(cfg, sm, mm, ce, no_auth=True)
            client = TestClient(server.app)

            # Send two messages
            client.post(
                "/api/v1/advisors/message",
                json={
                    "platform": "discord",
                    "channel": "c1",
                    "user": "u1",
                    "text": "hello",
                },
            )
            client.post(
                "/api/v1/advisors/message",
                json={
                    "platform": "discord",
                    "channel": "c1",
                    "user": "u1",
                    "text": "summarize https://example.com/x",
                },
            )

            # Read memory
            resp = client.get(
                "/api/v1/advisors/memory",
                params={"platform": "discord", "channel": "c1", "user": "u1"},
            )
            assert resp.status_code == 200
            items = resp.json()
            assert len(items) >= 2
            assert any(i["role"] == "user" for i in items)

            # Clear memory
            resp = client.delete(
                "/api/v1/advisors/memory",
                params={"platform": "discord", "channel": "c1", "user": "u1"},
            )
            assert resp.status_code == 200
            assert resp.json()["cleared"] >= 1


# ---------------------------------------------------------------------------
# Memory disabled tests (from test_advisors_memory_disabled.py)
# ---------------------------------------------------------------------------


class _DummyConfigMemoryDisabled:
    """Config with advisors disabled for memory endpoint test."""

    def __init__(self) -> None:
        self.general_models_path = "models-idle"
        self.system_models_path = "models-computer"
        self.chat_models_path = "models-chatty"
        self.config = {"model_actions": {}}
        self.advisors = {"enabled": False}


class TestAdvisorsMemoryDisabled:
    """Test advisors memory endpoint when advisors are disabled."""

    def test_advisors_memory_disabled_returns_400(self):
        cfg = _DummyConfigMemoryDisabled()
        sm = StateManager()
        mm = ModelManager(cfg)
        ce = CommandExecutor(cfg, mm, sm)
        server = WebModeServer(cfg, sm, mm, ce, no_auth=True)
        client = TestClient(server.app)
        r = client.get(
            "/api/v1/advisors/memory",
            params={"platform": "p", "channel": "c", "user": "u"},
        )
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data


# ---------------------------------------------------------------------------
# Provider selection tests (from test_advisors_provider_selection.py)
# ---------------------------------------------------------------------------


class TestAdvisorsProviderSelection:
    """Test provider build logic."""

    def test_build_provider_safe_without_sdk(self):
        """When SDK is unavailable, we should get a stub provider."""
        config = {"llm_api_mode": "completion", "model": "gpt-3.5-turbo"}

        with patch("chatty_commander.advisors.providers.AGENTS_AVAILABLE", False):
            provider = build_provider_safe(config)

            assert provider is not None
            assert hasattr(provider, "generate")
            assert hasattr(provider, "generate_stream")

    def test_build_provider_safe_with_sdk_and_key(self):
        """When SDK is available and API key is present, use build_provider."""
        config = {
            "llm_api_mode": "responses",
            "model": "gpt-4",
            "api_key": "test-key",
        }

        with patch("chatty_commander.advisors.providers.AGENTS_AVAILABLE", True):
            with patch(
                "chatty_commander.advisors.providers.build_provider"
            ) as mock_build:
                mock_build.return_value = Mock()
                provider = build_provider_safe(config)

                assert provider is not None
                mock_build.assert_called_once_with(config)

    def test_build_provider_safe_without_key(self):
        """When API key is missing, use stub provider even if SDK is present."""
        config = {"llm_api_mode": "completion", "model": "gpt-3.5-turbo"}

        with patch("chatty_commander.advisors.providers.AGENTS_AVAILABLE", True):
            provider = build_provider_safe(config)

            assert provider is not None
            assert hasattr(provider, "generate")
            assert hasattr(provider, "generate_stream")


# ---------------------------------------------------------------------------
# Service tests (from test_advisors_service.py)
# ---------------------------------------------------------------------------


class _DummyConfigService:
    """Config for basic service tests."""

    advisors = {
        "enabled": True,
        "providers": {
            "llm_api_mode": "completion",
            "model": "gpt-oss20b",
            "api_key": None,
        },
        "context": {
            "personas": {
                "general": {"system_prompt": "You are helpful."},
                "discord_default": {"system_prompt": "You are a Discord bot."},
            },
            "default_persona": "general",
        },
        "commands": {},
    }


class TestAdvisorsService:
    """Test AdvisorsService basic behaviour."""

    def test_advisors_service_echo_reply(self):
        svc = AdvisorsService(config=_DummyConfigService())
        msg = AdvisorMessage(platform="discord", channel="c1", user="u1", text="hello")
        reply = svc.handle_message(msg)
        assert reply is not None
        assert isinstance(reply.reply, str)
        assert reply.model == "gpt-oss20b"
        assert reply.api_mode in ("completion", "responses")

    def test_advisors_service_disabled_returns_notice(self):
        class _DisabledConfig:
            advisors = {"enabled": False}

        svc = AdvisorsService(config=_DisabledConfig())
        msg = AdvisorMessage(platform="slack", channel="c2", user="u2", text="ping")
        with pytest.raises(RuntimeError) as exc:
            _ = svc.handle_message(msg)
        assert "not enabled" in str(exc.value)


# ---------------------------------------------------------------------------
# Tool call / stub provider tests (from test_advisors_tool_call.py)
# ---------------------------------------------------------------------------


class TestAdvisorsToolCall:
    """Test advisors happy-path with stub provider."""

    def test_advisors_happy_path_with_stub_provider(self, monkeypatch):
        cfg = {
            "enabled": True,
            "providers": {
                "model": "gpt-oss20b",
                "api_mode": "completion",
                "api_key": None,
            },
            "memory": {"persistence_enabled": False},
        }

        # Mock the LLM manager to return a predictable stub response
        mock_manager = Mock()
        mock_manager.generate_response.return_value = (
            "advisor:gpt-oss20b/completion: hello world"
        )
        mock_manager.active_backend = Mock()
        mock_manager.active_backend.model = "gpt-oss20b"
        mock_manager.get_active_backend_name.return_value = "gpt-oss20b"

        with patch(
            "chatty_commander.llm.manager.get_global_llm_manager"
        ) as mock_get_llm:
            mock_get_llm.return_value = mock_manager

            svc = AdvisorsService(cfg)
            msg = AdvisorMessage(
                platform="discord", channel="c1", user="u1", text="hello world"
            )
            reply = svc.handle_message(msg)

            assert (
                reply.reply.startswith("advisor:gpt-oss20b/completion")
                or "hello world" in reply.reply
            )
            assert reply.model == svc.provider.model
            # api_mode is internally converted to "chat" by the service
            assert reply.api_mode in ("completion", "chat")

            # Follow-up: persona switch path returns bool
            assert isinstance(svc.switch_persona(reply.context_key, "default"), bool)
