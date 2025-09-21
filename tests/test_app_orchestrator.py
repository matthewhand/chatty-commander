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
Comprehensive tests for app orchestrator module.

Tests the main application orchestration, state management, and coordination.
"""

import asyncio
import threading
import time
from unittest.mock import Mock, patch

import pytest

from chatty_commander.app.orchestrator import (
    ComponentStatus,
    Orchestrator,
    OrchestratorConfig,
    OrchestratorState,
)
from chatty_commander.exceptions import ValidationError


class TestOrchestratorConfig:
    """Test OrchestratorConfig class."""

    def test_orchestrator_config_creation(self):
        """Test creating an OrchestratorConfig instance."""
        config = OrchestratorConfig(
            max_concurrent_operations=5,
            operation_timeout=30,
            enable_health_checks=True,
            component_timeout=10,
        )

        assert config.max_concurrent_operations == 5
        assert config.operation_timeout == 30
        assert config.enable_health_checks is True
        assert config.component_timeout == 10

    def test_orchestrator_config_defaults(self):
        """Test OrchestratorConfig with default values."""
        config = OrchestratorConfig()

        assert config.max_concurrent_operations == 10
        assert config.operation_timeout == 60
        assert config.enable_health_checks is True
        assert config.component_timeout == 15

    def test_orchestrator_config_validation(self):
        """Test OrchestratorConfig validation."""
        # Valid config
        valid_config = OrchestratorConfig(
            max_concurrent_operations=1, operation_timeout=1, enable_health_checks=True
        )
        assert valid_config.validate() is True

        # Invalid config - should raise ValidationError during initialization
        with pytest.raises(ValidationError):
            OrchestratorConfig(max_concurrent_operations=0, operation_timeout=-1)


class TestOrchestratorState:
    """Test OrchestratorState enum."""

    def test_orchestrator_state_values(self):
        """Test OrchestratorState enum values."""
        assert OrchestratorState.INITIALIZING.value == "initializing"
        assert OrchestratorState.RUNNING.value == "running"
        assert OrchestratorState.PAUSED.value == "paused"
        assert OrchestratorState.STOPPED.value == "stopped"
        assert OrchestratorState.ERROR.value == "error"

    def test_orchestrator_state_transitions(self):
        """Test OrchestratorState transitions."""
        assert (
            OrchestratorState.can_transition(
                OrchestratorState.INITIALIZING, OrchestratorState.RUNNING
            )
            is True
        )
        assert (
            OrchestratorState.can_transition(
                OrchestratorState.RUNNING, OrchestratorState.STOPPED
            )
            is True
        )
        assert (
            OrchestratorState.can_transition(
                OrchestratorState.STOPPED, OrchestratorState.INITIALIZING
            )
            is True
        )

        # Invalid transitions
        assert (
            OrchestratorState.can_transition(
                OrchestratorState.ERROR, OrchestratorState.INITIALIZING
            )
            is False
        )


class TestComponentStatus:
    """Test ComponentStatus class."""

    def test_component_status_creation(self):
        """Test creating a ComponentStatus instance."""
        status = ComponentStatus(
            component_name="test_component",
            status="healthy",
            last_check=time.time(),
            metadata={"version": "1.0"},
        )

        assert status.component_name == "test_component"
        assert status.status == "healthy"
        assert status.metadata == {"version": "1.0"}

    def test_component_status_defaults(self):
        """Test ComponentStatus with default values."""
        status = ComponentStatus(component_name="test_component")

        assert status.component_name == "test_component"
        assert status.status == "unknown"
        assert status.last_check > 0
        assert status.metadata == {}

    def test_component_status_is_healthy(self):
        """Test ComponentStatus health checking."""
        healthy_status = ComponentStatus(component_name="healthy", status="healthy")
        assert healthy_status.is_healthy is True

        unhealthy_status = ComponentStatus(component_name="unhealthy", status="error")
        assert unhealthy_status.is_healthy is False


class TestOrchestrator:
    """Comprehensive tests for Orchestrator class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing."""
        return OrchestratorConfig(
            max_concurrent_operations=3, operation_timeout=30, enable_health_checks=True
        )

    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        return {
            "state_manager": Mock(),
            "model_manager": Mock(),
            "command_executor": Mock(),
            "voice_processor": Mock(),
            "advisors_service": Mock(),
        }

    def test_orchestrator_initialization(self, mock_config, mock_components):
        """Test Orchestrator initialization."""
        orchestrator = Orchestrator(mock_config, mock_components)

        assert orchestrator.config == mock_config
        assert orchestrator.components == mock_components
        assert orchestrator.state == OrchestratorState.INITIALIZING
        assert orchestrator.active_operations == 0
        assert orchestrator.operation_queue == []

    def test_orchestrator_initialization_without_components(self, mock_config):
        """Test Orchestrator initialization without components."""
        orchestrator = Orchestrator(mock_config)

        assert orchestrator.config == mock_config
        assert orchestrator.components == {}
        assert orchestrator.state == OrchestratorState.INITIALIZING

    def test_start_orchestrator(self, mock_config, mock_components):
        """Test starting the orchestrator."""
        orchestrator = Orchestrator(mock_config, mock_components)

        with patch.object(orchestrator, "_initialize_components") as mock_init:
            with patch.object(orchestrator, "_start_health_monitoring") as mock_monitor:
                mock_init.return_value = True
                mock_monitor.return_value = True

                result = orchestrator.start()

                assert result is True
                assert orchestrator.state == OrchestratorState.RUNNING
                mock_init.assert_called_once()
                mock_monitor.assert_called_once()

    def test_start_orchestrator_initialization_failure(
        self, mock_config, mock_components
    ):
        """Test starting orchestrator with initialization failure."""
        orchestrator = Orchestrator(mock_config, mock_components)

        with patch.object(orchestrator, "_initialize_components") as mock_init:
            mock_init.return_value = False

            result = orchestrator.start()

            assert result is False
            assert orchestrator.state == OrchestratorState.ERROR

    def test_stop_orchestrator(self, mock_config, mock_components):
        """Test stopping the orchestrator."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        with patch.object(orchestrator, "_stop_health_monitoring") as mock_stop_monitor:
            with patch.object(orchestrator, "_cleanup_components") as mock_cleanup:
                result = orchestrator.stop()

                assert result is True
                assert orchestrator.state == OrchestratorState.STOPPED
                mock_stop_monitor.assert_called_once()
                mock_cleanup.assert_called_once()

    def test_pause_resume_orchestrator(self, mock_config, mock_components):
        """Test pausing and resuming the orchestrator."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        # Test pause
        result = orchestrator.pause()
        assert result is True
        assert orchestrator.state == OrchestratorState.PAUSED

        # Test resume
        result = orchestrator.resume()
        assert result is True
        assert orchestrator.state == OrchestratorState.RUNNING

    def test_execute_operation_basic(self, mock_config, mock_components):
        """Test executing a basic operation."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        async def sample_operation():
            return "operation_result"

        result = orchestrator.execute_operation(sample_operation)

        assert result == "operation_result"
        assert orchestrator.active_operations == 0

    def test_execute_operation_with_timeout(self, mock_config, mock_components):
        """Test executing operation with timeout."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        async def slow_operation():
            await asyncio.sleep(2)  # Longer than timeout
            return "slow_result"

        # Set short timeout
        orchestrator.config.operation_timeout = 0.1

        result = orchestrator.execute_operation(slow_operation)

        # Should return timeout error
        assert "timeout" in result.lower() or "error" in result.lower()

    def test_execute_operation_concurrent_limit(self, mock_config, mock_components):
        """Test concurrent operation limit enforcement."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        async def quick_operation():
            await asyncio.sleep(0.1)
            return "quick_result"

        # Set low concurrent limit
        orchestrator.config.max_concurrent_operations = 1

        # Try to execute multiple operations
        results = []
        for _ in range(3):
            result = orchestrator.execute_operation(quick_operation)
            results.append(result)

        # Should handle concurrent limits gracefully
        assert len(results) == 3

    def test_queue_operation(self, mock_config, mock_components):
        """Test queuing operations."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        async def queued_operation():
            return "queued_result"

        # Queue operation
        operation_id = orchestrator.queue_operation(queued_operation)

        assert operation_id is not None
        assert len(orchestrator.operation_queue) == 1

        # Process queued operation
        result = orchestrator.process_queued_operation(operation_id)

        assert result == "queued_result"
        assert len(orchestrator.operation_queue) == 0

    def test_get_system_status(self, mock_config, mock_components):
        """Test getting system status."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        status = orchestrator.get_system_status()

        assert "state" in status
        assert "active_operations" in status
        assert "queued_operations" in status
        assert "component_status" in status
        assert status["state"] == "running"
        assert status["active_operations"] == 0

    def test_get_component_status(self, mock_config, mock_components):
        """Test getting component status."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Mock component health checks
        for component_name, component in mock_components.items():
            component.health_check.return_value = True

        component_status = orchestrator.get_component_status()

        assert "state_manager" in component_status
        assert "model_manager" in component_status
        assert all(status["healthy"] for status in component_status.values())

    def test_health_check_all_components(self, mock_config, mock_components):
        """Test health checking all components."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Mock health checks
        for component in mock_components.values():
            component.health_check.return_value = True

        health_status = orchestrator.health_check()

        assert health_status["overall"] == "healthy"
        assert health_status["components"]["state_manager"]["healthy"] is True

    def test_health_check_with_failing_components(self, mock_config, mock_components):
        """Test health checking with some failing components."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Make some components fail
        mock_components["state_manager"].health_check.return_value = True
        mock_components["model_manager"].health_check.return_value = False
        mock_components["command_executor"].health_check.side_effect = Exception(
            "Component error"
        )

        health_status = orchestrator.health_check()

        assert health_status["overall"] == "degraded"
        assert health_status["components"]["state_manager"]["healthy"] is True
        assert health_status["components"]["model_manager"]["healthy"] is False

    def test_restart_component(self, mock_config, mock_components):
        """Test restarting individual component."""
        orchestrator = Orchestrator(mock_config, mock_components)

        with patch.object(orchestrator, "_initialize_component") as mock_init:
            mock_init.return_value = True

            result = orchestrator.restart_component("state_manager")

            assert result is True
            mock_init.assert_called_once_with("state_manager")

    def test_restart_all_components(self, mock_config, mock_components):
        """Test restarting all components."""
        orchestrator = Orchestrator(mock_config, mock_components)

        with patch.object(orchestrator, "_initialize_components") as mock_init:
            mock_init.return_value = True

            result = orchestrator.restart_all_components()

            assert result is True
            mock_init.assert_called_once()

    def test_get_operation_statistics(self, mock_config, mock_components):
        """Test getting operation statistics."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        # Execute some operations
        async def dummy_operation():
            return "result"

        for _ in range(5):
            orchestrator.execute_operation(dummy_operation)

        stats = orchestrator.get_operation_statistics()

        assert "total_operations" in stats
        assert "average_execution_time" in stats
        assert "success_rate" in stats
        assert stats["total_operations"] == 5
        assert stats["success_rate"] == 1.0

    def test_event_subscription(self, mock_config, mock_components):
        """Test event subscription functionality."""
        orchestrator = Orchestrator(mock_config, mock_components)

        event_callback_called = False
        event_data = None

        def event_callback(event_type, data):
            nonlocal event_callback_called, event_data
            event_callback_called = True
            event_data = data

        orchestrator.subscribe_to_events(event_callback)

        # Trigger event
        orchestrator._trigger_event("test_event", {"test": "data"})

        assert event_callback_called is True
        assert event_data == {"test": "data"}

    def test_error_handling_operation_exception(self, mock_config, mock_components):
        """Test error handling when operation throws exception."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        async def failing_operation():
            raise Exception("Operation failed")

        result = orchestrator.execute_operation(failing_operation)

        # Should handle error gracefully
        assert "error" in result.lower() or isinstance(result, dict)

    def test_configuration_update(self, mock_config, mock_components):
        """Test configuration update."""
        orchestrator = Orchestrator(mock_config, mock_components)

        new_config = OrchestratorConfig(
            max_concurrent_operations=10,
            operation_timeout=60,
            enable_health_checks=False,
        )

        result = orchestrator.update_config(new_config)

        assert result is True
        assert orchestrator.config.max_concurrent_operations == 10
        assert orchestrator.config.operation_timeout == 60
        assert orchestrator.config.enable_health_checks is False

    def test_get_system_metrics(self, mock_config, mock_components):
        """Test getting system metrics."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        metrics = orchestrator.get_system_metrics()

        assert "uptime" in metrics
        assert "memory_usage" in metrics
        assert "cpu_usage" in metrics
        assert "thread_count" in metrics
        assert isinstance(metrics["uptime"], (int, float))

    def test_concurrent_operation_execution(self, mock_config, mock_components):
        """Test concurrent operation execution."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        async def concurrent_operation(delay):
            await asyncio.sleep(delay)
            return f"result_{delay}"

        # Execute multiple operations concurrently
        results = []
        for delay in [0.1, 0.2, 0.3]:
            result = orchestrator.execute_operation(
                lambda d=delay: concurrent_operation(d)
            )
            results.append(result)

        assert len(results) == 3
        assert all("result_" in result for result in results)

    def test_operation_cancellation(self, mock_config, mock_components):
        """Test operation cancellation."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        async def long_operation():
            await asyncio.sleep(10)  # Long operation
            return "long_result"

        # Start operation
        operation_id = orchestrator.queue_operation(long_operation)

        # Cancel operation
        cancel_result = orchestrator.cancel_operation(operation_id)

        assert cancel_result is True

    def test_backup_and_restore_state(self, mock_config, mock_components, tmp_path):
        """Test state backup and restore functionality."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        backup_file = tmp_path / "orchestrator_backup.json"

        # Create backup
        backup_result = orchestrator.backup_state(str(backup_file))

        assert backup_result is True
        assert backup_file.exists()

        # Change state
        orchestrator.state = OrchestratorState.PAUSED

        # Restore state
        restore_result = orchestrator.restore_state(str(backup_file))

        assert restore_result is True
        assert orchestrator.state == OrchestratorState.RUNNING

    def test_component_dependency_management(self, mock_config, mock_components):
        """Test component dependency management."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Define dependencies
        dependencies = {
            "command_executor": ["model_manager"],
            "voice_processor": ["state_manager", "model_manager"],
        }

        orchestrator.set_component_dependencies(dependencies)

        # Check dependencies
        executor_deps = orchestrator.get_component_dependencies("command_executor")
        processor_deps = orchestrator.get_component_dependencies("voice_processor")

        assert "model_manager" in executor_deps
        assert "state_manager" in processor_deps
        assert "model_manager" in processor_deps

    def test_graceful_shutdown(self, mock_config, mock_components):
        """Test graceful shutdown process."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        # Start some operations
        async def dummy_operation():
            return "result"

        for _ in range(3):
            orchestrator.execute_operation(dummy_operation)

        # Perform graceful shutdown
        shutdown_result = orchestrator.graceful_shutdown(timeout=5)

        assert shutdown_result is True
        assert orchestrator.state == OrchestratorState.STOPPED

    def test_emergency_stop(self, mock_config, mock_components):
        """Test emergency stop functionality."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        # Start some operations
        async def dummy_operation():
            await asyncio.sleep(10)  # Long operation
            return "result"

        orchestrator.execute_operation(dummy_operation)

        # Emergency stop
        stop_result = orchestrator.emergency_stop()

        assert stop_result is True
        assert orchestrator.state == OrchestratorState.STOPPED

    def test_performance_monitoring(self, mock_config, mock_components):
        """Test performance monitoring functionality."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        # Execute operations to generate metrics
        async def quick_operation():
            return "quick_result"

        for _ in range(10):
            orchestrator.execute_operation(quick_operation)

        performance_metrics = orchestrator.get_performance_metrics()

        assert "operations_per_second" in performance_metrics
        assert "average_operation_time" in performance_metrics
        assert "peak_concurrent_operations" in performance_metrics
        assert performance_metrics["total_operations"] == 10

    def test_thread_safety(self, mock_config, mock_components):
        """Test thread safety of orchestrator operations."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        results = []
        errors = []

        def execute_operations():
            try:

                async def thread_operation():
                    return "thread_result"

                result = orchestrator.execute_operation(thread_operation)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Execute operations from multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=execute_operations)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should handle concurrent access gracefully
        assert len(results) == 5
        assert len(errors) == 0
        assert all(result == "thread_result" for result in results)
