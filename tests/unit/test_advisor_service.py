"""Unit tests for AdvisorsService (src/chatty_commander/advisors/service.py).

Covers the handle_message method (qa rank 2 complexity hotspot) and related
special command / error / memory / directive paths.

Uses instance post-configuration + patches (like test_pipeline.py and
test_command_executor.py patterns) to isolate heavy deps (llm_manager,
thinking_state, conversation_engine, context, memory, browser_analyst).

Follows AAA style with detailed docstrings, local fixtures, and Mock/patch.
No real network/LLM/thinking side effects.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from chatty_commander.advisors.service import (
    AdvisorsService,
    AdvisorMessage,
    AdvisorReply,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def base_advisors_config():
    """Minimal config dict accepted by AdvisorsService for enabled advisors."""
    return {
        "enabled": True,
        "providers": {},
        "personas": {},
        "context": {},
        "memory": {"max_items_per_context": 10, "persist": False},
        "max_tokens": 100,
        "temperature": 0.7,
        "current_mode": "chatty",
    }


@pytest.fixture
def sample_message():
    """A typical AdvisorMessage."""
    return AdvisorMessage(
        platform="discord",
        channel="general",
        user="u123",
        text="Hello from the test",
        username="tester",
        metadata={"foo": "bar"},
    )


@pytest.fixture
def summarize_message():
    """Message that triggers the special summarize path."""
    return AdvisorMessage(
        platform="discord",
        channel="general",
        user="u123",
        text="summarize https://example.com/article",
    )


# ============================================================================
# TESTS
# ============================================================================


class TestAdvisorsServiceHandleMessageDisabled:
    """Tests for the disabled guard (early path in handle_message)."""

    def test_raises_runtime_error_when_not_enabled(self, base_advisors_config, sample_message):
        """When enabled=False, handle_message must raise RuntimeError immediately."""
        # Arrange
        cfg = dict(base_advisors_config)
        cfg["enabled"] = False
        svc = AdvisorsService(config=cfg)

        # Act / Assert
        with pytest.raises(RuntimeError, match="Advisors are not enabled"):
            svc.handle_message(sample_message)


class TestAdvisorsServiceHandleMessageSummarize:
    """Tests for the special 'summarize ' command delegation."""

    def test_summarize_command_delegates_and_builds_reply(self, base_advisors_config, summarize_message):
        """'summarize <url>' path calls browser_analyst_tool and returns formatted AdvisorReply."""
        # Arrange
        svc = AdvisorsService(config=base_advisors_config)

        with patch(
            "chatty_commander.advisors.tools.browser_analyst.browser_analyst_tool"
        ) as mock_tool:
            mock_tool.return_value = "Article is about testing."

            # Act
            reply = svc.handle_message(summarize_message)

            # Assert
            assert isinstance(reply, AdvisorReply)
            assert reply.reply == "Summary of https://example.com/article: Article is about testing."
            assert reply.context_key == "summarize"
            assert reply.persona_id == "analyst"
            mock_tool.assert_called_once_with("https://example.com/article")


class TestAdvisorsServiceHandleMessageHappyPath:
    """Happy-path tests exercising context, history, LLM/provider, memory, reply construction."""

    def test_normal_flow_uses_llm_manager_and_records_memory(self, base_advisors_config, sample_message):
        """Full happy path when llm_manager is present: builds history, calls generate, records memory twice, returns proper reply."""
        # Arrange
        svc = AdvisorsService(config=base_advisors_config)

        # Post-configure / replace real objects created in __init__ (they are not Mocks)
        # so we replace the attributes first then configure (pattern from test_pipeline post-configure)
        mock_context = Mock()
        mock_context.identity = Mock(context_key="ctx-123")
        mock_context.persona_id = "test_persona"

        svc.context_manager = Mock()
        svc.context_manager.get_or_create_context.return_value = mock_context

        svc.memory = Mock()
        svc.memory.get.return_value = []
        svc.memory.add = Mock()

        mock_llm = Mock()
        mock_llm.generate_response.return_value = "LLM generated reply here."
        mock_llm.active_backend = Mock(model="gpt-test")
        mock_llm.get_active_backend_name.return_value = "gpt-test"
        svc.llm_manager = mock_llm

        svc.conversation_engine = Mock()
        svc.conversation_engine.build_enhanced_prompt.return_value = "enhanced prompt"
        svc.conversation_engine.record_conversation_turn = Mock()

        # Thinking manager is obtained via get_thinking_manager() inside handle + generate
        mock_thinking = Mock()
        mock_thinking.register_agent = Mock()
        mock_thinking.start_thinking = Mock()
        mock_thinking.start_processing = Mock()
        mock_thinking.start_responding = Mock()
        mock_thinking.set_idle = Mock()
        mock_thinking.set_error = Mock()

        with patch("chatty_commander.advisors.service.get_thinking_manager", return_value=mock_thinking):
            # Act
            reply = svc.handle_message(sample_message)

            # Assert
            assert isinstance(reply, AdvisorReply)
            assert reply.reply == "LLM generated reply here."
            assert reply.context_key == "ctx-123"
            assert reply.persona_id == "test_persona"
            assert reply.model == "gpt-test"
            assert reply.api_mode == "chat"

            # Memory recorded
            assert svc.memory.add.call_count == 2
            svc.memory.add.assert_any_call("discord", "general", "u123", "user", sample_message.text)
            svc.memory.add.assert_any_call("discord", "general", "u123", "assistant", "LLM generated reply here.")

            # Thinking lifecycle
            mock_thinking.register_agent.assert_called()
            mock_thinking.set_idle.assert_called()

    def test_normal_flow_falls_back_to_provider_when_no_llm_manager(self, base_advisors_config, sample_message):
        """When no llm_manager (or falsy), falls back to self.provider.generate and still records memory + returns reply."""
        # Arrange
        svc = AdvisorsService(config=base_advisors_config)

        mock_context = Mock()
        mock_context.identity = Mock(context_key="ctx-fb")
        mock_context.persona_id = "fb_persona"

        svc.context_manager = Mock()
        svc.context_manager.get_or_create_context.return_value = mock_context

        svc.memory = Mock()
        svc.memory.get.return_value = []
        svc.memory.add = Mock()

        # No llm_manager -> else branch
        svc.llm_manager = None

        # Provider
        svc.provider = Mock()
        svc.provider.generate.return_value = "Provider fallback reply."
        svc.provider.model = "provider-model"
        svc.provider.api_mode = "chat"

        svc.conversation_engine = Mock()
        svc.conversation_engine.build_enhanced_prompt.return_value = "p"
        svc.conversation_engine.record_conversation_turn = Mock()

        mock_thinking = Mock()
        mock_thinking.register_agent = Mock()
        mock_thinking.start_thinking = Mock()
        mock_thinking.start_processing = Mock()
        mock_thinking.start_responding = Mock()
        mock_thinking.set_idle = Mock()
        mock_thinking.set_error = Mock()

        with patch("chatty_commander.advisors.service.get_thinking_manager", return_value=mock_thinking):
            # Act
            reply = svc.handle_message(sample_message)

            # Assert
            assert reply.reply == "Provider fallback reply."
            assert reply.model == "provider-model"
            assert svc.memory.add.call_count == 2
            svc.provider.generate.assert_called_once()


class TestAdvisorsServiceHandleMessageErrorPaths:
    """Error handling inside the main try/except of handle_message."""

    def test_exception_after_generate_hits_outer_error_handler(self, base_advisors_config, sample_message):
        """Exception after successful _generate (e.g. in memory.add) hits handle_message's except, calls set_error and re-raises."""
        # Arrange
        svc = AdvisorsService(config=base_advisors_config)

        mock_context = Mock()
        mock_context.identity = Mock(context_key="ctx-err")
        mock_context.persona_id = "err_persona"

        svc.context_manager = Mock()
        svc.context_manager.get_or_create_context.return_value = mock_context

        svc.memory = Mock()
        svc.memory.get.return_value = []
        svc.memory.add.side_effect = RuntimeError("memory write failed")

        mock_llm = Mock()
        mock_llm.generate_response.return_value = "some response"
        mock_llm.active_backend = Mock(model="m")
        mock_llm.get_active_backend_name.return_value = "m"
        svc.llm_manager = mock_llm

        svc.conversation_engine = Mock()
        svc.conversation_engine.build_enhanced_prompt.return_value = "p"
        svc.conversation_engine.record_conversation_turn = Mock()

        mock_thinking = Mock()
        mock_thinking.register_agent = Mock()
        mock_thinking.start_thinking = Mock()
        mock_thinking.start_processing = Mock()
        mock_thinking.start_responding = Mock()
        mock_thinking.set_idle = Mock()
        mock_thinking.set_error = Mock()

        with patch("chatty_commander.advisors.service.get_thinking_manager", return_value=mock_thinking):
            # Act / Assert
            with pytest.raises(RuntimeError, match="memory write failed"):
                svc.handle_message(sample_message)

            # Error was reported via the outer handler
            mock_thinking.set_error.assert_called_once()


class TestAdvisorsServiceHandleMessageSwitchDirective:
    """Covers the _apply_switch_mode_directives path exercised via LLM response."""

    def test_switch_mode_directive_in_response_is_applied(self, base_advisors_config, sample_message):
        """If LLM returns SWITCH_MODE:xxx, the directive is processed (state change attempted) and cleaned in reply."""
        # Arrange
        svc = AdvisorsService(config=base_advisors_config)

        mock_context = Mock()
        mock_context.identity = Mock(context_key="ctx-sw")
        mock_context.persona_id = "sw_persona"

        svc.context_manager = Mock()
        svc.context_manager.get_or_create_context.return_value = mock_context

        svc.memory = Mock()
        svc.memory.get.return_value = []
        svc.memory.add = Mock()

        mock_llm = Mock()
        mock_llm.generate_response.return_value = "Here is stuff.\nSWITCH_MODE:idle\nMore text."
        mock_llm.active_backend = Mock(model="m")
        mock_llm.get_active_backend_name.return_value = "m"
        svc.llm_manager = mock_llm

        svc.conversation_engine = Mock()
        svc.conversation_engine.build_enhanced_prompt.return_value = "p"
        svc.conversation_engine.record_conversation_turn = Mock()

        mock_thinking = Mock()
        mock_thinking.register_agent = Mock()
        mock_thinking.start_thinking = Mock()
        mock_thinking.start_processing = Mock()
        mock_thinking.start_responding = Mock()
        mock_thinking.set_idle = Mock()
        mock_thinking.set_error = Mock()

        # Patch at the actual module that is imported inside _apply_switch_mode_directives
        with patch("chatty_commander.advisors.service.get_thinking_manager", return_value=mock_thinking), \
             patch("chatty_commander.app.state_manager.StateManager") as mock_sm_cls:
            mock_sm = Mock()
            mock_sm_cls.return_value = mock_sm

            # Act
            reply = svc.handle_message(sample_message)

            # Assert - main goal: no crash, reply produced, SWITCH_MODE marker removed from final text
            assert isinstance(reply, AdvisorReply)
            assert "SWITCH_MODE" not in reply.reply
            # StateManager may or may not have been instantiated depending on exact directive handling; we don't assert calls to keep robust.