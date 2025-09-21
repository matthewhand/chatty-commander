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
Expanded comprehensive tests for orchestrator module.

Additional test coverage for edge cases, error scenarios, and advanced functionality.
"""

import asyncio
import json
import threading
import time
from unittest.mock import Mock, patch

import pytest

from chatty_commander.app.orchestrator import (
    ComponentStatus,
    DummyAdapter,
    InputAdapter,
    ModeOrchestrator,
    OpenWakeWordAdapter,
    Orchestrator,
    OrchestratorConfig,
    OrchestratorFlags,
    OrchestratorState,
    TextInputAdapter,
)
from chatty_commander.exceptions import ValidationError


class TestOrchestratorConfigEdgeCases:
    """Test OrchestratorConfig edge cases and validation."""

    def test_config_validation_boundary_values(self):
        """Test configuration validation with boundary values."""
        # Test with minimum valid values
        config = OrchestratorConfig(
            max_concurrent_operations=1,
            operation_timeout=1,
            component_timeout=1,
            health_check_interval=1,
            backup_interval=1,
            max_backup_files=1,
            metrics_interval=1,
        )
        assert config.validate() is True

    def test_config_validation_zero_values(self):
        """Test configuration validation with zero values."""
        with pytest.raises(ValidationError):
            OrchestratorConfig(max_concurrent_operations=0)

        with pytest.raises(ValidationError):
            OrchestratorConfig(operation_timeout=0)

        with pytest.raises(ValidationError):
            OrchestratorConfig(component_timeout=0)

    def test_config_validation_negative_values(self):
        """Test configuration validation with negative values."""
        with pytest.raises(ValidationError):
            OrchestratorConfig(max_concurrent_operations=-1)

        with pytest.raises(ValidationError):
            OrchestratorConfig(operation_timeout=-5)

        with pytest.raises(ValidationError):
            OrchestratorConfig(health_check_interval=-10)

    def test_config_validation_large_values(self):
        """Test configuration with very large values."""
        config = OrchestratorConfig(
            max_concurrent_operations=1000,
            operation_timeout=3600,
            component_timeout=300,
            health_check_interval=86400,  # 24 hours
            backup_interval=604800,  # 1 week
            max_backup_files=1000,
            metrics_interval=3600,
        )
        assert config.validate() is True

    def test_config_post_init_validation_failure(self):
        """Test that invalid config raises ValidationError in __post_init__."""
        with patch.object(OrchestratorConfig, 'validate', return_value=False):
            with pytest.raises(ValidationError):
                OrchestratorConfig()

    def test_config_field_types(self):
        """Test configuration with different field types."""
        config = OrchestratorConfig(
            max_concurrent_operations=10.0,  # Float instead of int
            operation_timeout=60.5,  # Float instead of int
        )
        # Should still work as dataclass handles type conversion
        assert isinstance(config.max_concurrent_operations, int)
        assert isinstance(config.operation_timeout, int)


class TestComponentStatusAdvanced:
    """Advanced tests for ComponentStatus class."""

    def test_component_status_update_status(self):
        """Test updating component status."""
        status = ComponentStatus(
            component_name="test_component",
            status="unknown",
            metadata={"version": "1.0"}
        )

        # Update status
        new_metadata = {"version": "2.0", "uptime": "1h"}
        status.update_status("healthy", new_metadata)

        assert status.status == "healthy"
        assert status.last_check > 0
        assert status.metadata["version"] == "2.0"
        assert status.metadata["uptime"] == "1h"

    def test_component_status_update_status_no_metadata(self):
        """Test updating status without metadata."""
        status = ComponentStatus(component_name="test_component")
        original_check_time = status.last_check

        # Small delay to ensure time difference
        time.sleep(0.01)

        status.update_status("error")

        assert status.status == "error"
        assert status.last_check > original_check_time
        assert status.metadata == {}

    def test_component_status_health_property_variations(self):
        """Test is_healthy property with various status values."""
        test_cases = [
            ("healthy", True),
            ("ok", True),
            ("running", True),
            ("active", True),
            ("HEALTHY", True),
            ("OK", True),
            ("error", False),
            ("unhealthy", False),
            ("down", False),
            ("stopped", False),
            ("unknown", False),
            ("", False),
        ]

        for status_value, expected_healthy in test_cases:
            status = ComponentStatus("test", status=status_value)
            assert status.is_healthy == expected_healthy, f"Failed for status: {status_value}"

    def test_component_status_metadata_immutability(self):
        """Test that metadata updates don't affect original dict."""
        original_metadata = {"key": "value"}
        status = ComponentStatus("test", metadata=original_metadata.copy())

        # Modify original dict
        original_metadata["new_key"] = "new_value"

        # Status metadata should be unchanged
        assert "new_key" not in status.metadata
        assert status.metadata == {"key": "value"}

    def test_component_status_serialization(self):
        """Test ComponentStatus serialization for backup/restore."""
        status = ComponentStatus(
            component_name="test",
            status="healthy",
            metadata={"version": "1.0", "config": {"timeout": 30}}
        )

        # Simulate serialization
        data = {
            "component_name": status.component_name,
            "status": status.status,
            "last_check": status.last_check,
            "metadata": status.metadata,
        }

        # Should be JSON serializable
        json_str = json.dumps(data)
        restored_data = json.loads(json_str)

        assert restored_data["component_name"] == "test"
        assert restored_data["status"] == "healthy"
        assert restored_data["metadata"]["version"] == "1.0"


class TestOrchestratorInternalMethods:
    """Test internal orchestrator methods."""

    def test_initialize_components_success(self, mock_config, mock_components):
        """Test successful component initialization."""
        orchestrator = Orchestrator(mock_config, mock_components)

        with patch.object(orchestrator, '_initialize_component') as mock_init:
            mock_init.return_value = True

            result = orchestrator._initialize_components()

            assert result is True
            assert mock_init.call_count == len(mock_components)

    def test_initialize_components_partial_failure(self, mock_config, mock_components):
        """Test component initialization with some failures."""
        orchestrator = Orchestrator(mock_config, mock_components)

        with patch.object(orchestrator, '_initialize_component') as mock_init:
            # First component succeeds, second fails
            mock_init.side_effect = [True, False]

            result = orchestrator._initialize_components()

            assert result is False
            assert mock_init.call_count == 2  # Should stop after first failure

    def test_initialize_components_empty_components(self, mock_config):
        """Test component initialization with no components."""
        orchestrator = Orchestrator(mock_config)

        result = orchestrator._initialize_components()

        assert result is True

    def test_initialize_component_with_initialize_method(self, mock_config, mock_components):
        """Test initializing component with initialize method."""
        component = Mock()
        component.initialize.return_value = True
        orchestrator = Orchestrator(mock_config, {"test": component})

        result = orchestrator._initialize_component("test")

        assert result is True
        component.initialize.assert_called_once()

    def test_initialize_component_with_start_method(self, mock_config, mock_components):
        """Test initializing component with start method."""
        component = Mock()
        component.start.return_value = True
        orchestrator = Orchestrator(mock_config, {"test": component})

        result = orchestrator._initialize_component("test")

        assert result is True
        component.start.assert_called_once()

    def test_initialize_component_no_methods(self, mock_config, mock_components):
        """Test initializing component with no initialize/start methods."""
        component = Mock()
        orchestrator = Orchestrator(mock_config, {"test": component})

        result = orchestrator._initialize_component("test")

        assert result is True  # Should return True for components without init methods

    def test_initialize_component_not_found(self, mock_config, mock_components):
        """Test initializing non-existent component."""
        orchestrator = Orchestrator(mock_config, mock_components)

        result = orchestrator._initialize_component("nonexistent")

        assert result is False

    def test_cleanup_components_success(self, mock_config, mock_components):
        """Test successful component cleanup."""
        orchestrator = Orchestrator(mock_config, mock_components)

        with patch.object(orchestrator, 'logger') as mock_logger:
            orchestrator._cleanup_components()

            # Should not log any errors
            mock_logger.error.assert_not_called()

    def test_cleanup_components_with_cleanup_method(self, mock_config, mock_components):
        """Test cleanup with cleanup method."""
        component = Mock()
        component.cleanup.return_value = None
        orchestrator = Orchestrator(mock_config, {"test": component})

        with patch.object(orchestrator, 'logger') as mock_logger:
            orchestrator._cleanup_components()

            component.cleanup.assert_called_once()
            mock_logger.error.assert_not_called()

    def test_cleanup_components_with_stop_method(self, mock_config, mock_components):
        """Test cleanup with stop method."""
        component = Mock()
        component.stop.return_value = None
        orchestrator = Orchestrator(mock_config, {"test": component})

        orchestrator._cleanup_components()
        component.stop.assert_called_once()

    def test_cleanup_components_with_exceptions(self, mock_config, mock_components):
        """Test cleanup with component exceptions."""
        component = Mock()
        component.cleanup.side_effect = Exception("Cleanup failed")
        orchestrator = Orchestrator(mock_config, {"test": component})

        with patch.object(orchestrator, 'logger') as mock_logger:
            orchestrator._cleanup_components()

            mock_logger.error.assert_called_once()
            assert "Cleanup failed" in str(mock_logger.error.call_args)

    def test_start_health_monitoring_placeholder(self, mock_config, mock_components):
        """Test that health monitoring start is a placeholder."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Should not raise an exception
        orchestrator._start_health_monitoring()

    def test_stop_health_monitoring_placeholder(self, mock_config, mock_components):
        """Test that health monitoring stop is a placeholder."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Should not raise an exception
        orchestrator._stop_health_monitoring()

    def test_trigger_event_no_subscribers(self, mock_config, mock_components):
        """Test triggering events with no subscribers."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Should not raise an exception
        orchestrator._trigger_event("test_event", {"data": "test"})

    def test_trigger_event_with_failing_subscriber(self, mock_config, mock_components):
        """Test triggering events with a failing subscriber."""
        orchestrator = Orchestrator(mock_config, mock_components)

        def failing_callback(event_type, data):
            raise Exception("Callback failed")

        def working_callback(event_type, data):
            pass

        orchestrator.subscribe_to_events(failing_callback)
        orchestrator.subscribe_to_events(working_callback)

        with patch.object(orchestrator, 'logger') as mock_logger:
            orchestrator._trigger_event("test_event", {"data": "test"})

            # Should log the error but continue
            mock_logger.error.assert_called_once()
            assert "Callback failed" in str(mock_logger.error.call_args)


class TestOrchestratorOperationEdgeCases:
    """Test orchestrator operation edge cases."""

    def test_execute_operation_in_wrong_state(self, mock_config, mock_components):
        """Test executing operation in wrong orchestrator state."""
        orchestrator = Orchestrator(mock_config, mock_components)

        async def dummy_operation():
            return "result"

        # Test in various non-running states
        for state in [OrchestratorState.INITIALIZING, OrchestratorState.PAUSED, OrchestratorState.STOPPED, OrchestratorState.ERROR]:
            orchestrator.state = state
            result = orchestrator.execute_operation(dummy_operation)
            assert "error" in result
            assert "not running" in result["error"].lower()

    def test_execute_operation_concurrent_limit_exceeded(self, mock_config, mock_components):
        """Test operation execution when concurrent limit is exceeded."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        # Set low concurrent limit
        orchestrator.config.max_concurrent_operations = 1
        orchestrator.active_operations = 1  # Simulate one active operation

        async def dummy_operation():
            return "result"

        result = orchestrator.execute_operation(dummy_operation)

        assert "error" in result
        assert "maximum concurrent operations" in result["error"].lower()

    def test_execute_operation_timeout_handling(self, mock_config, mock_components):
        """Test operation timeout handling."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        async def slow_operation():
            await asyncio.sleep(10)  # Longer than timeout
            return "slow_result"

        # Set short timeout
        result = orchestrator.execute_operation(slow_operation, timeout=0.1)

        assert "error" in result
        assert "timed out" in result["error"].lower()

    def test_execute_operation_exception_handling(self, mock_config, mock_components):
        """Test operation exception handling."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        async def failing_operation():
            raise ValueError("Operation failed")

        result = orchestrator.execute_operation(failing_operation)

        assert "error" in result
        assert "operation failed" in result["error"].lower()

    def test_execute_operation_mixed_sync_async(self, mock_config, mock_components):
        """Test executing both sync and async operations."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        def sync_operation():
            return "sync_result"

        async def async_operation():
            await asyncio.sleep(0.01)  # Small delay to ensure it's async
            return "async_result"

        # Test sync operation
        sync_result = orchestrator.execute_operation(sync_operation)
        assert sync_result == "sync_result"

        # Test async operation
        async_result = orchestrator.execute_operation(async_operation)
        assert async_result == "async_result"

    def test_execute_operation_nested_calls(self, mock_config, mock_components):
        """Test nested operation execution."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        async def outer_operation():
            async def inner_operation():
                return "inner_result"
            return await inner_operation()

        result = orchestrator.execute_operation(outer_operation)
        assert result == "inner_result"

    def test_queue_operation_edge_cases(self, mock_config, mock_components):
        """Test queue operation edge cases."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        # Test queuing invalid operation
        invalid_operation = None
        operation_id = orchestrator.queue_operation(invalid_operation)
        assert operation_id is not None

        # Processing invalid operation should handle gracefully
        result = orchestrator.process_queued_operation(operation_id)
        assert "error" in result or result is None

    def test_cancel_operation_edge_cases(self, mock_config, mock_components):
        """Test cancel operation edge cases."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Test canceling non-existent operation
        result = orchestrator.cancel_operation("nonexistent_id")
        assert result is False

        # Test canceling with empty queue
        result = orchestrator.cancel_operation("")
        assert result is False

    def test_process_queued_operation_invalid_id(self, mock_config, mock_components):
        """Test processing queued operation with invalid ID."""
        orchestrator = Orchestrator(mock_config, mock_components)

        result = orchestrator.process_queued_operation("invalid_id")
        assert "error" in result
        assert "not found" in result["error"].lower()


class TestOrchestratorStateTransitions:
    """Test orchestrator state transitions and edge cases."""

    def test_state_transition_validation(self, mock_config, mock_components):
        """Test state transition validation."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Test all valid transitions
        valid_transitions = [
            (OrchestratorState.INITIALIZING, OrchestratorState.RUNNING),
            (OrchestratorState.INITIALIZING, OrchestratorState.ERROR),
            (OrchestratorState.RUNNING, OrchestratorState.PAUSED),
            (OrchestratorState.RUNNING, OrchestratorState.STOPPED),
            (OrchestratorState.RUNNING, OrchestratorState.ERROR),
            (OrchestratorState.PAUSED, OrchestratorState.RUNNING),
            (OrchestratorState.PAUSED, OrchestratorState.STOPPED),
            (OrchestratorState.PAUSED, OrchestratorState.ERROR),
            (OrchestratorState.STOPPED, OrchestratorState.INITIALIZING),
            (OrchestratorState.STOPPED, OrchestratorState.ERROR),
            (OrchestratorState.ERROR, OrchestratorState.INITIALIZING),
            (OrchestratorState.ERROR, OrchestratorState.STOPPED),
        ]

        for from_state, to_state in valid_transitions:
            assert OrchestratorState.can_transition(from_state, to_state)

    def test_state_transition_invalid(self, mock_config, mock_components):
        """Test invalid state transitions."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Test invalid transitions
        invalid_transitions = [
            (OrchestratorState.RUNNING, OrchestratorState.INITIALIZING),
            (OrchestratorState.PAUSED, OrchestratorState.INITIALIZING),
            (OrchestratorState.STOPPED, OrchestratorState.RUNNING),
            (OrchestratorState.STOPPED, OrchestratorState.PAUSED),
            (OrchestratorState.ERROR, OrchestratorState.RUNNING),
            (OrchestratorState.ERROR, OrchestratorState.PAUSED),
        ]

        for from_state, to_state in invalid_transitions:
            assert not OrchestratorState.can_transition(from_state, to_state)

    def test_start_invalid_state(self, mock_config, mock_components):
        """Test starting orchestrator in invalid states."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Set to invalid starting state
        orchestrator.state = OrchestratorState.RUNNING

        with patch.object(orchestrator, 'logger') as mock_logger:
            result = orchestrator.start()

            assert result is False
            mock_logger.warning.assert_called_once()

    def test_stop_invalid_state(self, mock_config, mock_components):
        """Test stopping orchestrator in invalid states."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Test stopping in states that don't allow stopping
        for state in [OrchestratorState.INITIALIZING, OrchestratorState.ERROR]:
            orchestrator.state = state
            result = orchestrator.stop()
            assert result is False

    def test_pause_invalid_state(self, mock_config, mock_components):
        """Test pausing orchestrator in invalid states."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Test pausing in states that don't allow pausing
        for state in [OrchestratorState.INITIALIZING, OrchestratorState.STOPPED, OrchestratorState.ERROR]:
            orchestrator.state = state
            result = orchestrator.pause()
            assert result is False

    def test_resume_invalid_state(self, mock_config, mock_components):
        """Test resuming orchestrator in invalid states."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Test resuming in states that don't allow resuming
        for state in [OrchestratorState.INITIALIZING, OrchestratorState.RUNNING, OrchestratorState.STOPPED, OrchestratorState.ERROR]:
            orchestrator.state = state
            result = orchestrator.resume()
            assert result is False


class TestOrchestratorBackupRestore:
    """Test orchestrator backup and restore functionality."""

    def test_backup_state_disabled(self, mock_config, mock_components):
        """Test backup when backup is disabled."""
        mock_config.backup_enabled = False
        orchestrator = Orchestrator(mock_config, mock_components)

        result = orchestrator.backup_state("/tmp/test_backup.json")
        assert result is False

    def test_backup_state_success(self, mock_config, mock_components, tmp_path):
        """Test successful state backup."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING
        orchestrator.active_operations = 5

        backup_file = tmp_path / "test_backup.json"

        result = orchestrator.backup_state(str(backup_file))

        assert result is True
        assert backup_file.exists()

        # Verify backup contents
        with open(backup_file) as f:
            backup_data = json.load(f)

        assert backup_data["state"] == "running"
        assert backup_data["active_operations"] == 5
        assert backup_data["config"]["max_concurrent_operations"] == mock_config.max_concurrent_operations

    def test_backup_state_file_error(self, mock_config, mock_components):
        """Test backup with file system error."""
        orchestrator = Orchestrator(mock_config, mock_components)

        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            with patch.object(orchestrator, 'logger') as mock_logger:
                result = orchestrator.backup_state("/root/test_backup.json")

                assert result is False
                mock_logger.error.assert_called_once()

    def test_restore_state_success(self, mock_config, mock_components, tmp_path):
        """Test successful state restore."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.STOPPED

        # Create backup file
        backup_data = {
            "state": "running",
            "config": {"max_concurrent_operations": 20},
            "active_operations": 3,
            "timestamp": time.time()
        }

        backup_file = tmp_path / "test_backup.json"
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f)

        result = orchestrator.restore_state(str(backup_file))

        assert result is True
        assert orchestrator.state == OrchestratorState.RUNNING

    def test_restore_state_file_not_found(self, mock_config, mock_components):
        """Test restore with non-existent file."""
        orchestrator = Orchestrator(mock_config, mock_components)

        with patch.object(orchestrator, 'logger') as mock_logger:
            result = orchestrator.restore_state("/nonexistent/backup.json")

            assert result is False
            mock_logger.error.assert_called_once()

    def test_restore_state_invalid_json(self, mock_config, mock_components, tmp_path):
        """Test restore with invalid JSON."""
        orchestrator = Orchestrator(mock_config, mock_components)

        backup_file = tmp_path / "invalid_backup.json"
        with open(backup_file, 'w') as f:
            f.write("invalid json content {")

        with patch.object(orchestrator, 'logger') as mock_logger:
            result = orchestrator.restore_state(str(backup_file))

            assert result is False
            mock_logger.error.assert_called_once()

    def test_restore_state_invalid_state_value(self, mock_config, mock_components, tmp_path):
        """Test restore with invalid state value."""
        orchestrator = Orchestrator(mock_config, mock_components)

        backup_data = {
            "state": "invalid_state",
            "config": {"max_concurrent_operations": 20},
            "timestamp": time.time()
        }

        backup_file = tmp_path / "test_backup.json"
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f)

        result = orchestrator.restore_state(str(backup_file))

        assert result is True
        # State should remain unchanged due to invalid state value
        assert orchestrator.state == OrchestratorState.INITIALIZING


class TestInputAdapterClasses:
    """Test InputAdapter and related classes."""

    def test_input_adapter_base_class(self):
        """Test InputAdapter base class."""
        adapter = InputAdapter()

        assert adapter.name == "base"
        assert not adapter._started

        adapter.start()
        assert adapter._started

        adapter.stop()
        assert not adapter._started

    def test_text_input_adapter(self):
        """Test TextInputAdapter."""
        commands_received = []

        def mock_command_handler(command):
            commands_received.append(command)

        adapter = TextInputAdapter(mock_command_handler)

        assert adapter.name == "base"  # Inherits from base
        assert not adapter._started

        # Test feeding commands when not started
        adapter.feed("test command")
        assert len(commands_received) == 0

        # Start adapter
        adapter.start()

        # Test feeding commands when started
        adapter.feed("test command")
        assert len(commands_received) == 1
        assert commands_received[0] == "test command"

    def test_dummy_adapter(self):
        """Test DummyAdapter."""
        adapter = DummyAdapter("test_adapter")

        assert adapter.name == "test_adapter"
        assert not adapter._started

        adapter.start()
        assert adapter._started

        adapter.stop()
        assert not adapter._started

    def test_open_wake_word_adapter_initialization(self):
        """Test OpenWakeWordAdapter initialization."""
        def mock_wake_handler(wake_word, confidence):
            pass

        config = Mock()
        config.wake_words = ["test_wake"]
        config.wake_word_threshold = 0.8

        adapter = OpenWakeWordAdapter(mock_wake_handler, config)

        assert not adapter._started
        assert adapter._detector is None

    def test_open_wake_word_adapter_voice_unavailable(self):
        """Test OpenWakeWordAdapter when voice is unavailable."""
        def mock_wake_handler(wake_word, confidence):
            pass

        with patch('chatty_commander.app.orchestrator.VOICE_AVAILABLE', False):
            adapter = OpenWakeWordAdapter(mock_wake_handler)

            with pytest.raises(ImportError):
                adapter.start()

    def test_open_wake_word_adapter_start_stop(self):
        """Test OpenWakeWordAdapter start/stop functionality."""
        def mock_wake_handler(wake_word, confidence):
            pass

        config = Mock()
        config.wake_words = ["hey_jarvis"]
        config.wake_word_threshold = 0.5

        with patch('chatty_commander.app.orchestrator.VOICE_AVAILABLE', True):
            with patch('chatty_commander.app.orchestrator.WakeWordDetector') as mock_detector_class:
                mock_detector = Mock()
                mock_detector_class.return_value = mock_detector

                adapter = OpenWakeWordAdapter(mock_wake_handler, config)

                # Start adapter
                adapter.start()
                assert adapter._started
                mock_detector.start_listening.assert_called_once()

                # Stop adapter
                adapter.stop()
                assert not adapter._started
                mock_detector.stop_listening.assert_called_once()

    def test_open_wake_word_adapter_fallback_to_mock(self):
        """Test OpenWakeWordAdapter fallback to mock detector."""
        def mock_wake_handler(wake_word, confidence):
            pass

        config = Mock()
        config.wake_words = ["hey_jarvis"]
        config.wake_word_threshold = 0.5

        with patch('chatty_commander.app.orchestrator.VOICE_AVAILABLE', True):
            with patch('chatty_commander.app.orchestrator.WakeWordDetector', side_effect=Exception("No audio")):
                with patch('chatty_commander.app.orchestrator.MockWakeWordDetector') as mock_detector_class:
                    mock_detector = Mock()
                    mock_detector_class.return_value = mock_detector

                    adapter = OpenWakeWordAdapter(mock_wake_handler, config)

                    adapter.start()
                    assert adapter._started
                    assert isinstance(adapter._detector, Mock)  # Should be mock detector


class TestModeOrchestrator:
    """Test ModeOrchestrator functionality."""

    def test_mode_orchestrator_initialization(self):
        """Test ModeOrchestrator initialization."""
        config = Mock()
        command_sink = Mock()
        advisor_sink = Mock()

        orchestrator = ModeOrchestrator(
            config=config,
            command_sink=command_sink,
            advisor_sink=advisor_sink
        )

        assert orchestrator.config == config
        assert orchestrator.command_sink == command_sink
        assert orchestrator.advisor_sink == advisor_sink
        assert orchestrator.flags.enable_text is False  # Default
        assert len(orchestrator.adapters) == 0

    def test_select_adapters_text_only(self):
        """Test adapter selection with text only."""
        config = Mock()
        command_sink = Mock()
        command_sink.execute_command.return_value = "command_result"

        orchestrator = ModeOrchestrator(
            config=config,
            command_sink=command_sink,
            flags=OrchestratorFlags(enable_text=True)
        )

        selected_adapters = orchestrator.select_adapters()

        assert len(selected_adapters) == 1
        assert selected_adapters[0].name == "base"  # TextInputAdapter inherits from base
        assert len(orchestrator.adapters) == 1

    def test_select_adapters_all_enabled(self):
        """Test adapter selection with all flags enabled."""
        config = Mock()
        command_sink = Mock()

        orchestrator = ModeOrchestrator(
            config=config,
            command_sink=command_sink,
            flags=OrchestratorFlags(
                enable_text=True,
                enable_gui=True,
                enable_web=True,
                enable_openwakeword=True,
                enable_computer_vision=True,
                enable_discord_bridge=True
            )
        )

        with patch('chatty_commander.app.orchestrator.InputAdapter.registry', {
            "gui": lambda: DummyAdapter("gui"),
            "web": lambda: DummyAdapter("web"),
            "openwakeword": lambda config=None, on_wake_word=None: DummyAdapter("openwakeword"),
            "computer_vision": lambda: DummyAdapter("computer_vision"),
            "discord_bridge": lambda: DummyAdapter("discord_bridge"),
        }):
            selected_adapters = orchestrator.select_adapters()

            assert len(selected_adapters) == 6  # All adapters selected

    def test_select_adapters_with_advisor_config(self):
        """Test adapter selection with advisor configuration."""
        config = Mock()
        config.advisors = {"enabled": True}
        command_sink = Mock()

        orchestrator = ModeOrchestrator(
            config=config,
            command_sink=command_sink,
            flags=OrchestratorFlags(enable_discord_bridge=True)
        )

        with patch('chatty_commander.app.orchestrator.InputAdapter.registry', {
            "discord_bridge": lambda: DummyAdapter("discord_bridge"),
        }):
            selected_adapters = orchestrator.select_adapters()

            assert len(selected_adapters) == 2  # Text + Discord bridge
            assert "discord_bridge" in [a.name for a in selected_adapters]

    def test_start_stop_orchestrator(self):
        """Test starting and stopping mode orchestrator."""
        config = Mock()
        command_sink = Mock()

        orchestrator = ModeOrchestrator(
            config=config,
            command_sink=command_sink,
            flags=OrchestratorFlags(enable_text=True)
        )

        # Start should work
        started_adapters = orchestrator.start()
        assert len(started_adapters) == 1

        # Stop should work
        orchestrator.stop()
        # No assertions needed, just that it doesn't raise

    def test_dispatch_command(self):
        """Test command dispatching."""
        config = Mock()
        command_sink = Mock()
        command_sink.execute_command.return_value = "success"

        orchestrator = ModeOrchestrator(
            config=config,
            command_sink=command_sink
        )

        result = orchestrator._dispatch_command("test_command")

        assert result == "success"
        command_sink.execute_command.assert_called_once_with("test_command")

    def test_handle_wake_word(self):
        """Test wake word handling."""
        config = Mock()
        command_sink = Mock()
        command_sink.execute_command.side_effect = ["wake_result", "generic_result"]

        orchestrator = ModeOrchestrator(
            config=config,
            command_sink=command_sink
        )

        # Test specific wake word command
        orchestrator._handle_wake_word("jarvis", 0.95)

        # Should try specific wake word command first, then generic
        assert command_sink.execute_command.call_count == 2
        command_sink.execute_command.assert_any_call("wake_word_jarvis")
        command_sink.execute_command.assert_any_call("wake")

    def test_handle_wake_word_no_commands(self):
        """Test wake word handling when no commands exist."""
        config = Mock()
        command_sink = Mock()
        command_sink.execute_command.side_effect = Exception("Command not found")

        orchestrator = ModeOrchestrator(
            config=config,
            command_sink=command_sink
        )

        # Should not raise exception
        orchestrator._handle_wake_word("jarvis", 0.95)

        # Should try both specific and generic commands
        assert command_sink.execute_command.call_count == 2


class TestOrchestratorStressTests:
    """Stress tests for orchestrator."""

    def test_concurrent_operation_stress(self, mock_config, mock_components):
        """Test orchestrator under concurrent operation stress."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        results = []
        errors = []

        async def stress_operation(operation_id):
            await asyncio.sleep(0.01)  # Small delay to simulate work
            return f"result_{operation_id}"

        async def run_stress_test():
            tasks = []
            for i in range(100):  # 100 concurrent operations
                task = orchestrator.execute_operation(
                    lambda oid=i: stress_operation(oid)
                )
                tasks.append(task)

            # Wait for all to complete
            for task in tasks:
                try:
                    result = task
                    results.append(result)
                except Exception as e:
                    errors.append(e)

        # Run stress test
        asyncio.run(run_stress_test())

        assert len(results) == 100
        assert len(errors) == 0
        assert all("result_" in result for result in results)

    def test_queue_operation_stress(self, mock_config, mock_components):
        """Test queue operation stress."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        # Queue many operations
        operation_ids = []
        for i in range(50):
            op_id = orchestrator.queue_operation(lambda: f"queued_result_{i}")
            operation_ids.append(op_id)

        assert len(orchestrator.operation_queue) == 50

        # Process all queued operations
        results = []
        for op_id in operation_ids:
            result = orchestrator.process_queued_operation(op_id)
            results.append(result)

        assert len(results) == 50
        assert len(orchestrator.operation_queue) == 0
        assert all("queued_result_" in result for result in results)

    def test_memory_usage_simulation(self, mock_config, mock_components):
        """Test orchestrator memory usage under load."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        # Simulate many operations to build up operation history
        async def memory_operation():
            return "memory_test"

        for i in range(1000):
            result = orchestrator.execute_operation(memory_operation)
            assert result == "memory_test"

        # Check that operation history is maintained
        assert len(orchestrator.operation_history) == 1000

        # Get statistics should still work
        stats = orchestrator.get_operation_statistics()
        assert stats["total_operations"] == 1000
        assert stats["success_rate"] == 1.0

    def test_thread_safety_stress(self, mock_config, mock_components):
        """Test orchestrator thread safety under stress."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        results = []
        errors = []

        def execute_in_thread(thread_id):
            try:
                async def thread_operation():
                    await asyncio.sleep(0.01)
                    return f"thread_{thread_id}"

                result = orchestrator.execute_operation(thread_operation)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Execute operations from multiple threads
        threads = []
        for i in range(20):
            thread = threading.Thread(target=execute_in_thread, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(results) == 20
        assert len(errors) == 0
        assert all("thread_" in result for result in results)

    def test_event_system_stress(self, mock_config, mock_components):
        """Test event system under stress."""
        orchestrator = Orchestrator(mock_config, mock_components)

        event_calls = []

        def event_handler(event_type, data):
            event_calls.append((event_type, data))

        # Subscribe multiple handlers
        for i in range(10):
            orchestrator.subscribe_to_events(event_handler)

        # Trigger many events
        for i in range(100):
            orchestrator._trigger_event(f"stress_event_{i}", {"index": i})

        # Should have 100 events * 10 handlers = 1000 total calls
        assert len(event_calls) == 1000

        # Verify all events were received by all handlers
        for i in range(100):
            event_count = sum(1 for event_type, _ in event_calls if event_type == f"stress_event_{i}")
            assert event_count == 10


class TestOrchestratorErrorRecovery:
    """Test orchestrator error recovery scenarios."""

    def test_component_initialization_failure_recovery(self, mock_config, mock_components):
        """Test recovery from component initialization failure."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Make one component fail initialization
        mock_components["failing_component"] = Mock()
        mock_components["failing_component"].initialize.side_effect = Exception("Init failed")

        with patch.object(orchestrator, '_initialize_component') as mock_init:
            mock_init.side_effect = [True, Exception("Init failed"), True]

            result = orchestrator._initialize_components()

            assert result is False
            assert mock_init.call_count == 2  # Should stop after first failure

    def test_operation_execution_failure_recovery(self, mock_config, mock_components):
        """Test recovery from operation execution failure."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        # Execute failing operation
        async def failing_operation():
            raise RuntimeError("Operation crashed")

        result = orchestrator.execute_operation(failing_operation)

        assert "error" in result
        assert "operation crashed" in result["error"].lower()

        # Should still be able to execute subsequent operations
        async def working_operation():
            return "recovery_success"

        result = orchestrator.execute_operation(working_operation)
        assert result == "recovery_success"

    def test_event_handler_failure_recovery(self, mock_config, mock_components):
        """Test recovery from event handler failure."""
        orchestrator = Orchestrator(mock_config, mock_components)

        def failing_handler(event_type, data):
            raise RuntimeError("Handler crashed")

        def working_handler(event_type, data):
            pass

        orchestrator.subscribe_to_events(failing_handler)
        orchestrator.subscribe_to_events(working_handler)

        # Should not raise exception
        orchestrator._trigger_event("test_event", {"data": "test"})

    def test_state_corruption_recovery(self, mock_config, mock_components):
        """Test recovery from state corruption."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        # Simulate state corruption
        orchestrator.state = "invalid_state"

        # Operations should handle invalid state gracefully
        async def test_operation():
            return "test"

        result = orchestrator.execute_operation(test_operation)
        assert "error" in result
        assert "not running" in result["error"].lower()

    def test_queue_corruption_recovery(self, mock_config, mock_components):
        """Test recovery from queue corruption."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        # Corrupt the queue
        orchestrator.operation_queue = "not_a_list"

        async def test_operation():
            return "test"

        # Should handle corrupted queue gracefully
        result = orchestrator.execute_operation(test_operation)
        assert result == "test"

        # Queue operations should also handle corruption
        operation_id = orchestrator.queue_operation(test_operation)
        assert operation_id is not None  # Should create new queue

    def test_component_dependency_cycle_recovery(self, mock_config, mock_components):
        """Test recovery from component dependency cycles."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Create circular dependency
        orchestrator.set_component_dependencies({
            "comp_a": ["comp_b"],
            "comp_b": ["comp_a"],  # Circular dependency
        })

        # Should handle gracefully without infinite loops
        dependencies = orchestrator.get_component_dependencies("comp_a")
        assert dependencies == ["comp_b"]

    def test_backup_restore_corruption_recovery(self, mock_config, mock_components, tmp_path):
        """Test recovery from backup corruption."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Create corrupted backup file
        backup_file = tmp_path / "corrupted_backup.json"
        with open(backup_file, 'w') as f:
            f.write("corrupted json content")

        # Should handle corruption gracefully
        result = orchestrator.restore_state(str(backup_file))
        assert result is False

        # Should still be functional
        assert orchestrator.state == OrchestratorState.INITIALIZING

    def test_metrics_corruption_recovery(self, mock_config, mock_components):
        """Test recovery from metrics corruption."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        # Corrupt operation history
        orchestrator.operation_history = "not_a_list"

        # Should handle corruption gracefully
        stats = orchestrator.get_operation_statistics()
        assert stats["total_operations"] == 0

        # Should still be able to execute operations
        async def test_operation():
            return "test"

        result = orchestrator.execute_operation(test_operation)
        assert result == "test"


class TestOrchestratorIntegrationScenarios:
    """Integration tests for orchestrator scenarios."""

    def test_full_orchestrator_lifecycle(self, mock_config, mock_components):
        """Test complete orchestrator lifecycle."""
        orchestrator = Orchestrator(mock_config, mock_components)

        # Start orchestrator
        result = orchestrator.start()
        assert result is True
        assert orchestrator.state == OrchestratorState.RUNNING

        # Execute some operations
        async def test_operation():
            return "operation_result"

        results = []
        for i in range(5):
            result = orchestrator.execute_operation(test_operation)
            results.append(result)

        assert len(results) == 5
        assert all(result == "operation_result" for result in results)

        # Check statistics
        stats = orchestrator.get_operation_statistics()
        assert stats["total_operations"] == 5
        assert stats["success_rate"] == 1.0

        # Queue some operations
        operation_ids = []
        for i in range(3):
            op_id = orchestrator.queue_operation(test_operation)
            operation_ids.append(op_id)

        assert len(orchestrator.operation_queue) == 3

        # Process queued operations
        queued_results = []
        for op_id in operation_ids:
            result = orchestrator.process_queued_operation(op_id)
            queued_results.append(result)

        assert len(queued_results) == 3
        assert all(result == "operation_result" for result in queued_results)

        # Test pause/resume
        result = orchestrator.pause()
        assert result is True
        assert orchestrator.state == OrchestratorState.PAUSED

        result = orchestrator.resume()
        assert result is True
        assert orchestrator.state == OrchestratorState.RUNNING

        # Test graceful shutdown
        result = orchestrator.graceful_shutdown(timeout=1)
        assert result is True
        assert orchestrator.state == OrchestratorState.STOPPED

    def test_orchestrator_with_failing_components(self, mock_config):
        """Test orchestrator with some failing components."""
        # Create components with different health states
        healthy_component = Mock()
        healthy_component.health_check.return_value = True
        healthy_component.initialize.return_value = True

        failing_component = Mock()
        failing_component.health_check.return_value = False
        failing_component.initialize.side_effect = Exception("Init failed")

        error_component = Mock()
        error_component.health_check.side_effect = Exception("Health check failed")
        error_component.initialize.return_value = True

        components = {
            "healthy": healthy_component,
            "failing": failing_component,
            "error": error_component
        }

        orchestrator = Orchestrator(mock_config, components)

        # Start should handle component failures
        result = orchestrator.start()
        assert result is False  # Should fail due to failing component
        assert orchestrator.state == OrchestratorState.ERROR

        # Check health status
        health_status = orchestrator.health_check()
        assert health_status["overall"] == "degraded"
        assert health_status["components"]["healthy"]["healthy"] is True
        assert health_status["components"]["failing"]["healthy"] is False
        assert "error" in health_status["components"]["error"]["status"]

    def test_orchestrator_event_driven_operations(self, mock_config, mock_components):
        """Test orchestrator with event-driven operations."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        event_log = []

        def event_logger(event_type, data):
            event_log.append((event_type, data))

        orchestrator.subscribe_to_events(event_logger)

        # Perform various operations that trigger events
        orchestrator.start()  # Should not change state but might trigger events

        async def event_operation():
            return "event_result"

        orchestrator.execute_operation(event_operation)
        orchestrator.pause()
        orchestrator.resume()

        # Check that events were triggered
        assert len(event_log) > 0

        # Should have events for pause/resume
        event_types = [event_type for event_type, _ in event_log]
        assert "orchestrator_paused" in event_types
        assert "orchestrator_resumed" in event_types

    def test_orchestrator_backup_restore_integration(self, mock_config, mock_components, tmp_path):
        """Test backup/restore integration."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        # Execute some operations to create history
        async def backup_operation():
            return "backup_test"

        for i in range(10):
            orchestrator.execute_operation(backup_operation)

        # Create backup
        backup_file = tmp_path / "integration_backup.json"
        result = orchestrator.backup_state(str(backup_file))
        assert result is True
        assert backup_file.exists()

        # Change state
        orchestrator.state = OrchestratorState.PAUSED

        # Restore from backup
        result = orchestrator.restore_state(str(backup_file))
        assert result is True
        assert orchestrator.state == OrchestratorState.RUNNING

        # Verify backup data
        with open(backup_file) as f:
            backup_data = json.load(f)

        assert backup_data["state"] == "running"
        assert backup_data["active_operations"] == 0  # Should be 0 after operations complete

    def test_orchestrator_concurrent_stress_integration(self, mock_config, mock_components):
        """Test orchestrator under concurrent stress with integration."""
        orchestrator = Orchestrator(mock_config, mock_components)
        orchestrator.state = OrchestratorState.RUNNING

        async def concurrent_operation(delay):
            await asyncio.sleep(delay)
            return f"concurrent_{delay}"

        async def run_concurrent_test():
            # Execute many concurrent operations
            tasks = []
            for i in range(50):
                delay = i * 0.001  # Increasing delays
                task = orchestrator.execute_operation(
                    lambda d=delay: concurrent_operation(d)
                )
                tasks.append(task)

            # Collect results
            results = []
            for task in tasks:
                try:
                    result = task
                    results.append(result)
                except Exception as e:
                    results.append(f"error: {e}")

            return results

        results = asyncio.run(run_concurrent_test())

        assert len(results) == 50
        assert all("concurrent_" in result or "error" in result for result in results)

        # Check statistics
        stats = orchestrator.get_operation_statistics()
        assert stats["total_operations"] == 50
        assert stats["success_rate"] >= 0.9  # Should have high success rate
