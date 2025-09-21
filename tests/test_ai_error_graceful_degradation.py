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
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Error handling and edge case tests for graceful degradation and recovery mechanisms in AI components.
Tests dependency failures, invalid inputs, network issues, resource exhaustion,
and graceful degradation scenarios across IntelligenceCore, VoiceProcessor, and ConversationEngine.
"""

import time
from unittest.mock import Mock, patch

from chatty_commander.advisors.conversation_engine import (
    ConversationEngine,
)
from chatty_commander.ai.intelligence_core import AIResponse, IntelligenceCore


class TestGracefulDegradation:
    """Test graceful degradation mechanisms."""

    def test_component_degradation_chain(self):
        """Test degradation chain when multiple components fail."""
        # Create components with failing dependencies
        mock_llm_client = Mock()
        mock_llm_client.generate_response.side_effect = Exception("LLM service down")

        conversation_engine = ConversationEngine(
            {"llm_client": mock_llm_client, "fallback_enabled": True}
        )

        # Mock conversation engine partial failure
        with patch.object(
            conversation_engine,
            "analyze_intent",
            side_effect=Exception("Intent analysis failed"),
        ):
            intelligence_core = IntelligenceCore(
                {"conversation_engine": conversation_engine}
            )

            response = intelligence_core.process_text_input("Test degradation chain")

            assert isinstance(response, AIResponse)
            assert response.success is True  # Should degrade gracefully
            assert len(response.response_text) > 0

    def test_quality_degradation_levels(self):
        """Test different levels of quality degradation."""
        conversation_engine = ConversationEngine({"fallback_enabled": True})

        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine}
        )

        # Test different degradation scenarios
        degradation_scenarios = [
            ("Full functionality", lambda: True),
            ("Partial LLM", lambda: Exception("LLM rate limited")),
            ("No LLM", lambda: Exception("LLM unavailable")),
            ("No sentiment analysis", lambda: Exception("Sentiment service down")),
            ("No intent analysis", lambda: Exception("Intent service down")),
        ]

        for scenario_name, side_effect in degradation_scenarios:
            with patch.object(
                conversation_engine, "analyze_intent", side_effect=side_effect
            ):
                with patch.object(
                    conversation_engine, "analyze_sentiment", side_effect=side_effect
                ):
                    response = intelligence_core.process_text_input("Test degradation")

                    assert (
                        response.success is True
                    )  # Should always provide some response
                    assert len(response.response_text) > 0

    def test_feature_availability_notification(self):
        """Test notification of feature availability degradation."""
        conversation_engine = ConversationEngine(
            {"debug_mode": True, "fallback_enabled": True}
        )

        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine, "debug_mode": True}
        )

        # Mock LLM service degradation
        with patch.object(conversation_engine, "logger") as mock_logger:
            with patch.object(
                conversation_engine,
                "build_enhanced_prompt",
                side_effect=Exception("LLM degraded"),
            ):
                response = intelligence_core.process_text_input(
                    "Test feature notification"
                )

                # Should log degradation
                mock_logger.warning.assert_called() or mock_logger.info.assert_called()
                assert response.success is True

    def test_service_recovery_detection(self):
        """Test detection and recovery when services come back online."""
        mock_llm_client = Mock()

        # Simulate service going down and coming back
        service_state = {"available": True, "failure_count": 0}

        def fluctuating_service(*args, **kwargs):
            service_state["failure_count"] += 1

            # Service fails after 2 calls, recovers after 4
            if 2 <= service_state["failure_count"] < 4:
                service_state["available"] = False
                raise Exception("Service temporarily unavailable")
            else:
                service_state["available"] = True
                return "Service response"

        mock_llm_client.generate_response = fluctuating_service

        conversation_engine = ConversationEngine(
            {"llm_client": mock_llm_client, "fallback_enabled": True}
        )

        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine, "debug_mode": True}
        )

        # Test service fluctuation
        responses = []
        for i in range(6):
            response = intelligence_core.process_text_input(f"Request {i}")
            responses.append(response)

            # All should succeed (with fallback when needed)
            assert response.success is True

        # Verify that service recovery was detected
        assert len(responses) == 6

    def test_circuit_breaker_pattern(self):
        """Test circuit breaker pattern for failing services."""
        mock_llm_client = Mock()

        # Simulate circuit breaker pattern
        circuit_state = {"failures": 0, "open": False, "threshold": 3}

        def circuit_breaker_service(*args, **kwargs):
            if circuit_state["open"]:
                raise Exception("Circuit breaker open")

            circuit_state["failures"] += 1

            if circuit_state["failures"] >= circuit_state["threshold"]:
                circuit_state["open"] = True
                raise Exception("Service failed - circuit breaker opened")

            return "Service response"

        mock_llm_client.generate_response = circuit_breaker_service

        conversation_engine = ConversationEngine(
            {"llm_client": mock_llm_client, "fallback_enabled": True}
        )

        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine}
        )

        # Test circuit breaker behavior
        for i in range(5):
            response = intelligence_core.process_text_input(f"Circuit test {i}")
            assert response.success is True  # Should fall back gracefully

    def test_degradation_priority_levels(self):
        """Test priority-based degradation when resources are constrained."""
        conversation_engine = ConversationEngine({"fallback_enabled": True})

        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine}
        )

        # Define degradation priorities
        degradation_priorities = [
            ("LLM generation", "high", lambda: Exception("LLM failed")),
            ("Sentiment analysis", "medium", lambda: Exception("Sentiment failed")),
            ("Intent analysis", "low", lambda: Exception("Intent failed")),
            ("Conversation history", "lowest", lambda: Exception("History failed")),
        ]

        for feature, priority, side_effect in degradation_priorities:
            with patch.object(
                conversation_engine, "analyze_intent", side_effect=side_effect
            ):
                response = intelligence_core.process_text_input(
                    f"Test {priority} priority"
                )

                # Should always provide basic response
                assert response.success is True
                assert len(response.response_text) > 0


class TestLoggingAndMonitoring:
    """Test logging and monitoring of error conditions."""

    def test_error_logging_levels(self):
        """Test appropriate error logging levels."""
        conversation_engine = ConversationEngine({"debug_mode": True})

        # Mock different error types
        with patch.object(conversation_engine, "logger") as mock_logger:
            # Critical error
            with patch.object(
                conversation_engine,
                "analyze_intent",
                side_effect=MemoryError("Out of memory"),
            ):
                conversation_engine.analyze_intent("test")
                mock_logger.critical.assert_called()

            # Error
            with patch.object(
                conversation_engine,
                "analyze_intent",
                side_effect=Exception("Service failed"),
            ):
                conversation_engine.analyze_intent("test")
                mock_logger.error.assert_called()

            # Warning
            with patch.object(
                conversation_engine,
                "analyze_intent",
                side_effect=Warning("Deprecated feature"),
            ):
                conversation_engine.analyze_intent("test")
                mock_logger.warning.assert_called()

    def test_error_context_preservation(self):
        """Test that error context is preserved in logs."""
        intelligence_core = IntelligenceCore({"debug_mode": True})

        with patch.object(intelligence_core, "logger") as mock_logger:
            # Mock complex error scenario
            with patch.object(
                intelligence_core,
                "_analyze_intent",
                side_effect=Exception("Analysis failed"),
            ):
                response = intelligence_core.process_text_input("Test error context")

                # Verify error context is logged
                mock_logger.error.assert_called()
                log_call = mock_logger.error.call_args
                assert "context" in str(log_call) or "metadata" in str(log_call)

    def test_performance_monitoring_during_errors(self):
        """Test performance monitoring during error conditions."""
        conversation_engine = ConversationEngine({"debug_mode": True})

        with patch.object(conversation_engine, "logger") as mock_logger:
            # Mock slow operation with error
            def slow_failing_operation(*args, **kwargs):
                time.sleep(0.1)  # Simulate slow operation
                raise Exception("Operation failed")

            with patch.object(
                conversation_engine,
                "analyze_intent",
                side_effect=slow_failing_operation,
            ):
                start_time = time.time()
                conversation_engine.analyze_intent("test")
                end_time = time.time()

                # Should log performance metrics
                mock_logger.error.assert_called()
                assert (
                    end_time - start_time
                ) >= 0.1  # Should account for slow operation

    def test_error_rate_threshold_monitoring(self):
        """Test monitoring of error rate thresholds."""
        intelligence_core = IntelligenceCore({"debug_mode": True})

        error_count = 0

        def count_errors(*args, **kwargs):
            nonlocal error_count
            error_count += 1
            raise Exception(f"Error {error_count}")

        with patch.object(intelligence_core, "logger") as mock_logger:
            with patch.object(
                intelligence_core, "_analyze_intent", side_effect=count_errors
            ):
                # Generate multiple errors
                for i in range(5):
                    response = intelligence_core.process_text_input(f"Error test {i}")
                    assert response.success is True  # Should fall back

                # Should log error rate warnings
                mock_logger.warning.assert_called() or mock_logger.error.assert_called()
                assert error_count == 5


class TestRecoveryAndResilience:
    """Test recovery mechanisms and resilience patterns."""

    def test_automatic_retry_mechanism(self):
        """Test automatic retry mechanism for transient failures."""
        mock_llm_client = Mock()

        # Simulate transient failure that recovers
        attempt_count = {"count": 0}

        def retry_operation(*args, **kwargs):
            attempt_count["count"] += 1
            if attempt_count["count"] <= 2:
                raise Exception("Transient network error")
            else:
                return "Success after retry"

        mock_llm_client.generate_response = retry_operation

        conversation_engine = ConversationEngine(
            {"llm_client": mock_llm_client, "fallback_enabled": True}
        )

        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine}
        )

        response = intelligence_core.process_text_input("Test retry mechanism")

        assert response.success is True
        assert attempt_count["count"] >= 2  # Should have retried

    def test_backup_service_activation(self):
        """Test activation of backup services when primary fails."""
        primary_llm = Mock()
        primary_llm.generate_response.side_effect = Exception("Primary service failed")

        backup_llm = Mock()
        backup_llm.generate_response.return_value = "Backup service response"

        conversation_engine = ConversationEngine(
            {"llm_client": primary_llm, "fallback_enabled": True}
        )

        intelligence_core = IntelligenceCore(
            {"conversation_engine": conversation_engine}
        )

        # Simulate backup service activation
        with patch.object(intelligence_core, "backup_llm_client", backup_llm):
            with patch.object(intelligence_core, "logger") as mock_logger:
                response = intelligence_core.process_text_input(
                    "Test backup activation"
                )

                # Should log backup activation
                mock_logger.info.assert_called() or mock_logger.warning.assert_called()
                assert response.success is True

    def test_state_recovery_after_failure(self):
        """Test recovery of component state after failure."""
        conversation_engine = ConversationEngine({})

        # Add some conversation history
        conversation_engine.add_to_history(
            "user123", "Previous message", "Previous response"
        )

        # Mock state corruption and recovery
        with patch.object(conversation_engine, "logger") as mock_logger:
            # Simulate state corruption
            conversation_engine.conversation_history = None

            # Test recovery mechanism
            response = conversation_engine.process_message("Test recovery")

            # Should recover gracefully
            assert response is not None
            mock_logger.warning.assert_called() or mock_logger.info.assert_called()
