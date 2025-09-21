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
Comprehensive tests for advisors recurring tasks module.

Tests scheduled task management, execution, persistence, and monitoring.
"""

import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.chatty_commander.advisors.recurring import (
    RecurringTask,
    TaskSchedule,
    RecurringTaskManager,
    TaskResult,
    TaskStatus,
    ScheduleType,
)


class TestTaskStatus:
    """Test TaskStatus enum."""

    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_task_status_transitions(self):
        """Test valid TaskStatus transitions."""
        assert TaskStatus.can_transition(TaskStatus.PENDING, TaskStatus.RUNNING) is True
        assert TaskStatus.can_transition(TaskStatus.RUNNING, TaskStatus.COMPLETED) is True
        assert TaskStatus.can_transition(TaskStatus.RUNNING, TaskStatus.FAILED) is True

        # Invalid transitions
        assert TaskStatus.can_transition(TaskStatus.COMPLETED, TaskStatus.RUNNING) is False
        assert TaskStatus.can_transition(TaskStatus.FAILED, TaskStatus.PENDING) is False


class TestScheduleType:
    """Test ScheduleType enum."""

    def test_schedule_type_values(self):
        """Test ScheduleType enum values."""
        assert ScheduleType.INTERVAL.value == "interval"
        assert ScheduleType.CRON.value == "cron"
        assert ScheduleType.FIXED_TIME.value == "fixed_time"
        assert ScheduleType.ON_DEMAND.value == "on_demand"

    def test_schedule_type_validation(self):
        """Test ScheduleType validation."""
        assert ScheduleType.is_valid("interval") is True
        assert ScheduleType.is_valid("cron") is True
        assert ScheduleType.is_valid("fixed_time") is True
        assert ScheduleType.is_valid("on_demand") is True
        assert ScheduleType.is_valid("invalid") is False


class TestTaskResult:
    """Test TaskResult class."""

    def test_task_result_creation(self):
        """Test creating a TaskResult instance."""
        result = TaskResult(
            task_id="task123",
            status=TaskStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            result_data={"output": "success"},
            execution_time=1.5,
            metadata={"attempt": 1}
        )

        assert result.task_id == "task123"
        assert result.status == TaskStatus.COMPLETED
        assert result.result_data == {"output": "success"}
        assert result.execution_time == 1.5
        assert result.metadata == {"attempt": 1}

    def test_task_result_defaults(self):
        """Test TaskResult with default values."""
        result = TaskResult(task_id="task456")

        assert result.task_id == "task456"
        assert result.status == TaskStatus.PENDING
        assert result.start_time is not None
        assert result.end_time is None
        assert result.result_data is None
        assert result.execution_time == 0.0
        assert result.metadata == {}

    def test_task_result_is_success(self):
        """Test TaskResult success checking."""
        success_result = TaskResult(
            task_id="task1",
            status=TaskStatus.COMPLETED
        )
        assert success_result.is_success is True

        failed_result = TaskResult(
            task_id="task2",
            status=TaskStatus.FAILED
        )
        assert failed_result.is_success is False

    def test_task_result_to_dict(self):
        """Test converting TaskResult to dictionary."""
        result = TaskResult(
            task_id="task123",
            status=TaskStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            result_data="test output",
            execution_time=2.0
        )

        result_dict = result.to_dict()

        assert result_dict["task_id"] == "task123"
        assert result_dict["status"] == "completed"
        assert result_dict["result_data"] == "test output"
        assert result_dict["execution_time"] == 2.0


class TestTaskSchedule:
    """Test TaskSchedule class."""

    def test_task_schedule_creation_interval(self):
        """Test creating interval-based task schedule."""
        schedule = TaskSchedule(
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=300,  # 5 minutes
            max_occurrences=10
        )

        assert schedule.schedule_type == ScheduleType.INTERVAL
        assert schedule.interval_seconds == 300
        assert schedule.max_occurrences == 10

    def test_task_schedule_creation_cron(self):
        """Test creating cron-based task schedule."""
        schedule = TaskSchedule(
            schedule_type=ScheduleType.CRON,
            cron_expression="0 */2 * * *",  # Every 2 hours
            timezone="UTC"
        )

        assert schedule.schedule_type == ScheduleType.CRON
        assert schedule.cron_expression == "0 */2 * * *"
        assert schedule.timezone == "UTC"

    def test_task_schedule_creation_fixed_time(self):
        """Test creating fixed time task schedule."""
        schedule = TaskSchedule(
            schedule_type=ScheduleType.FIXED_TIME,
            fixed_times=["09:00", "14:00", "18:00"],
            days_of_week=[1, 2, 3, 4, 5]  # Monday to Friday
        )

        assert schedule.schedule_type == ScheduleType.FIXED_TIME
        assert schedule.fixed_times == ["09:00", "14:00", "18:00"]
        assert schedule.days_of_week == [1, 2, 3, 4, 5]

    def test_task_schedule_validation(self):
        """Test TaskSchedule validation."""
        # Valid interval schedule
        valid_schedule = TaskSchedule(
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=60
        )
        assert valid_schedule.validate() is True

        # Invalid schedule (negative interval)
        invalid_schedule = TaskSchedule(
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=-10
        )
        assert invalid_schedule.validate() is False

    def test_task_schedule_next_run_interval(self):
        """Test calculating next run time for interval schedule."""
        schedule = TaskSchedule(
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=3600  # 1 hour
        )

        now = datetime.now()
        next_run = schedule.get_next_run_time(now)

        assert next_run is not None
        assert (next_run - now).total_seconds() >= 3600

    def test_task_schedule_next_run_fixed_time(self):
        """Test calculating next run time for fixed time schedule."""
        schedule = TaskSchedule(
            schedule_type=ScheduleType.FIXED_TIME,
            fixed_times=["14:30", "16:45"]
        )

        now = datetime.now()
        next_run = schedule.get_next_run_time(now)

        assert next_run is not None
        # Should be at one of the fixed times


class TestRecurringTask:
    """Test RecurringTask class."""

    def test_recurring_task_creation(self):
        """Test creating a RecurringTask instance."""
        async def sample_task():
            return "task completed"

        schedule = TaskSchedule(
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=300
        )

        task = RecurringTask(
            task_id="test_task",
            name="Test Task",
            task_function=sample_task,
            schedule=schedule,
            enabled=True,
            max_retries=3,
            metadata={"priority": "high"}
        )

        assert task.task_id == "test_task"
        assert task.name == "Test Task"
        assert task.task_function == sample_task
        assert task.schedule == schedule
        assert task.enabled is True
        assert task.max_retries == 3
        assert task.metadata == {"priority": "high"}

    def test_recurring_task_execution(self):
        """Test executing a recurring task."""
        async def sample_task():
            return {"result": "success"}

        schedule = TaskSchedule(
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=300
        )

        task = RecurringTask(
            task_id="test_task",
            name="Test Task",
            task_function=sample_task,
            schedule=schedule
        )

        # Execute task
        result = task.execute()

        assert result is not None
        assert result.status == TaskStatus.COMPLETED
        assert result.result_data == {"result": "success"}

    def test_recurring_task_execution_with_retry(self):
        """Test task execution with retry on failure."""
        call_count = 0

        async def failing_task():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "eventual success"

        schedule = TaskSchedule(
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=300
        )

        task = RecurringTask(
            task_id="retry_task",
            name="Retry Task",
            task_function=failing_task,
            schedule=schedule,
            max_retries=3
        )

        # Execute task (should retry and eventually succeed)
        result = task.execute()

        assert result.status == TaskStatus.COMPLETED
        assert result.result_data == "eventual success"
        assert call_count == 2  # Should have been called twice

    def test_recurring_task_execution_failure(self):
        """Test task execution that fails permanently."""
        async def failing_task():
            raise Exception("Permanent failure")

        schedule = TaskSchedule(
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=300
        )

        task = RecurringTask(
            task_id="fail_task",
            name="Failing Task",
            task_function=failing_task,
            schedule=schedule,
            max_retries=1
        )

        # Execute task
        result = task.execute()

        assert result.status == TaskStatus.FAILED
        assert "Permanent failure" in str(result.result_data)

    def test_recurring_task_enable_disable(self):
        """Test enabling and disabling tasks."""
        async def sample_task():
            return "task result"

        schedule = TaskSchedule(
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=300
        )

        task = RecurringTask(
            task_id="toggle_task",
            name="Toggle Task",
            task_function=sample_task,
            schedule=schedule,
            enabled=False  # Start disabled
        )

        # Task should not execute when disabled
        result = task.execute()
        assert result is None

        # Enable task
        task.enable()
        assert task.enabled is True

        # Task should execute when enabled
        result = task.execute()
        assert result is not None
        assert result.status == TaskStatus.COMPLETED

        # Disable task
        task.disable()
        assert task.enabled is False

    def test_recurring_task_should_run(self):
        """Test checking if task should run."""
        schedule = TaskSchedule(
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=300
        )

        task = RecurringTask(
            task_id="schedule_task",
            name="Schedule Task",
            task_function=async def(): return "result",
            schedule=schedule,
            enabled=True
        )

        # Should run when enabled and scheduled
        assert task.should_run(datetime.now()) is True

        # Should not run when disabled
        task.disable()
        assert task.should_run(datetime.now()) is False


class TestRecurringTaskManager:
    """Comprehensive tests for RecurringTaskManager class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing."""
        return {
            "max_concurrent_tasks": 5,
            "default_task_timeout": 300,
            "enable_persistence": True,
            "task_history_limit": 1000,
            "health_check_interval": 60
        }

    @pytest.fixture
    def sample_tasks(self):
        """Create sample recurring tasks."""
        async def task1():
            return "Task 1 result"

        async def task2():
            return "Task 2 result"

        async def task3():
            raise Exception("Task 3 failed")

        schedule1 = TaskSchedule(
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=300
        )

        schedule2 = TaskSchedule(
            schedule_type=ScheduleType.FIXED_TIME,
            fixed_times=["10:00", "14:00"]
        )

        schedule3 = TaskSchedule(
            schedule_type=ScheduleType.CRON,
            cron_expression="0 */4 * * *"
        )

        return [
            RecurringTask(
                task_id="task1",
                name="First Task",
                task_function=task1,
                schedule=schedule1,
                enabled=True,
                max_retries=2
            ),
            RecurringTask(
                task_id="task2",
                name="Second Task",
                task_function=task2,
                schedule=schedule2,
                enabled=True,
                priority=5
            ),
            RecurringTask(
                task_id="task3",
                name="Failing Task",
                task_function=task3,
                schedule=schedule3,
                enabled=True,
                max_retries=1
            )
        ]

    def test_recurring_task_manager_initialization(self, mock_config):
        """Test RecurringTaskManager initialization."""
        manager = RecurringTaskManager(mock_config)

        assert manager.config == mock_config
        assert manager.tasks == {}
        assert manager.task_results == {}
        assert manager.is_running is False
        assert manager.background_tasks == set()

    def test_add_task(self, mock_config, sample_tasks):
        """Test adding tasks to manager."""
        manager = RecurringTaskManager(mock_config)

        # Add tasks
        for task in sample_tasks:
            result = manager.add_task(task)
            assert result is True

        assert len(manager.tasks) == 3
        assert "task1" in manager.tasks
        assert "task2" in manager.tasks
        assert "task3" in manager.tasks

    def test_add_duplicate_task(self, mock_config, sample_tasks):
        """Test adding duplicate task."""
        manager = RecurringTaskManager(mock_config)

        # Add task
        manager.add_task(sample_tasks[0])

        # Try to add same task again
        result = manager.add_task(sample_tasks[0])

        assert result is False  # Should fail

    def test_get_task(self, mock_config, sample_tasks):
        """Test getting task from manager."""
        manager = RecurringTaskManager(mock_config)

        # Add task
        manager.add_task(sample_tasks[0])

        # Get task
        task = manager.get_task("task1")

        assert task is not None
        assert task.task_id == "task1"
        assert task.name == "First Task"

    def test_get_nonexistent_task(self, mock_config):
        """Test getting nonexistent task."""
        manager = RecurringTaskManager(mock_config)

        task = manager.get_task("nonexistent")

        assert task is None

    def test_remove_task(self, mock_config, sample_tasks):
        """Test removing task from manager."""
        manager = RecurringTaskManager(mock_config)

        # Add task
        manager.add_task(sample_tasks[0])

        assert len(manager.tasks) == 1

        # Remove task
        result = manager.remove_task("task1")

        assert result is True
        assert len(manager.tasks) == 0

    def test_remove_nonexistent_task(self, mock_config):
        """Test removing nonexistent task."""
        manager = RecurringTaskManager(mock_config)

        result = manager.remove_task("nonexistent")

        assert result is False

    def test_list_tasks(self, mock_config, sample_tasks):
        """Test listing all tasks."""
        manager = RecurringTaskManager(mock_config)

        # Add tasks
        for task in sample_tasks:
            manager.add_task(task)

        tasks = manager.list_tasks()

        assert len(tasks) == 3
        assert all(isinstance(task, RecurringTask) for task in tasks)

    def test_list_tasks_with_filters(self, mock_config, sample_tasks):
        """Test listing tasks with filters."""
        manager = RecurringTaskManager(mock_config)

        # Add tasks
        for task in sample_tasks:
            manager.add_task(task)

        # Filter by enabled status
        enabled_tasks = manager.list_tasks(enabled_only=True)
        assert len(enabled_tasks) == 3

        # Filter by schedule type
        interval_tasks = manager.list_tasks(schedule_type=ScheduleType.INTERVAL)
        assert len(interval_tasks) == 1
        assert interval_tasks[0].task_id == "task1"

    def test_enable_disable_task(self, mock_config, sample_tasks):
        """Test enabling and disabling tasks."""
        manager = RecurringTaskManager(mock_config)

        # Add task
        manager.add_task(sample_tasks[0])

        # Disable task
        result = manager.disable_task("task1")
        assert result is True

        task = manager.get_task("task1")
        assert task.enabled is False

        # Enable task
        result = manager.enable_task("task1")
        assert result is True

        task = manager.get_task("task1")
        assert task.enabled is True

    def test_execute_task(self, mock_config, sample_tasks):
        """Test executing individual task."""
        manager = RecurringTaskManager(mock_config)

        # Add task
        manager.add_task(sample_tasks[0])

        # Execute task
        result = manager.execute_task("task1")

        assert result is not None
        assert result.task_id == "task1"
        assert result.status == TaskStatus.COMPLETED
        assert result.result_data == "Task 1 result"

    def test_execute_nonexistent_task(self, mock_config):
        """Test executing nonexistent task."""
        manager = RecurringTaskManager(mock_config)

        result = manager.execute_task("nonexistent")

        assert result is None

    def test_execute_disabled_task(self, mock_config, sample_tasks):
        """Test executing disabled task."""
        manager = RecurringTaskManager(mock_config)

        # Add and disable task
        manager.add_task(sample_tasks[0])
        manager.disable_task("task1")

        # Try to execute disabled task
        result = manager.execute_task("task1")

        assert result is None

    def test_start_stop_manager(self, mock_config, sample_tasks):
        """Test starting and stopping the task manager."""
        manager = RecurringTaskManager(mock_config)

        # Add tasks
        for task in sample_tasks:
            manager.add_task(task)

        # Start manager
        result = manager.start()
        assert result is True
        assert manager.is_running is True

        # Stop manager
        result = manager.stop()
        assert result is True
        assert manager.is_running is False

    def test_get_manager_status(self, mock_config, sample_tasks):
        """Test getting manager status."""
        manager = RecurringTaskManager(mock_config)

        # Add tasks
        for task in sample_tasks:
            manager.add_task(task)

        status = manager.get_status()

        assert "total_tasks" in status
        assert "active_tasks" in status
        assert "running" in status
        assert "task_results" in status
        assert status["total_tasks"] == 3
        assert status["active_tasks"] == 3
        assert status["running"] is False

    def test_get_task_results(self, mock_config, sample_tasks):
        """Test getting task execution results."""
        manager = RecurringTaskManager(mock_config)

        # Add and execute task
        manager.add_task(sample_tasks[0])
        manager.execute_task("task1")

        results = manager.get_task_results("task1")

        assert len(results) == 1
        assert results[0].task_id == "task1"
        assert results[0].status == TaskStatus.COMPLETED

    def test_get_all_task_results(self, mock_config, sample_tasks):
        """Test getting all task execution results."""
        manager = RecurringTaskManager(mock_config)

        # Add and execute tasks
        for task in sample_tasks:
            manager.add_task(task)
            manager.execute_task(task.task_id)

        all_results = manager.get_all_task_results()

        assert len(all_results) == 3  # All tasks executed
        assert all(len(results) == 1 for results in all_results.values())

    def test_clear_task_results(self, mock_config, sample_tasks):
        """Test clearing task execution results."""
        manager = RecurringTaskManager(mock_config)

        # Add and execute task
        manager.add_task(sample_tasks[0])
        manager.execute_task("task1")

        assert len(manager.task_results) == 1

        # Clear results
        manager.clear_task_results("task1")

        assert len(manager.task_results) == 0

    def test_get_task_statistics(self, mock_config, sample_tasks):
        """Test getting task statistics."""
        manager = RecurringTaskManager(mock_config)

        # Add and execute tasks with mixed results
        manager.add_task(sample_tasks[0])  # Should succeed
        manager.add_task(sample_tasks[2])  # Should fail
        manager.execute_task("task1")
        manager.execute_task("task3")

        stats = manager.get_statistics()

        assert "total_tasks" in stats
        assert "success_rate" in stats
        assert "average_execution_time" in stats
        assert "most_active_tasks" in stats
        assert stats["total_tasks"] == 2
        assert stats["success_rate"] == 0.5  # 1 success, 1 failure

    def test_task_priority_execution(self, mock_config):
        """Test task execution with priority ordering."""
        manager = RecurringTaskManager(mock_config)

        async def task_func(task_id):
            return f"result_{task_id}"

        # Create tasks with different priorities
        high_priority_task = RecurringTask(
            task_id="high_pri",
            name="High Priority",
            task_function=lambda: task_func("high"),
            schedule=TaskSchedule(schedule_type=ScheduleType.ON_DEMAND),
            enabled=True,
            priority=10
        )

        low_priority_task = RecurringTask(
            task_id="low_pri",
            name="Low Priority",
            task_function=lambda: task_func("low"),
            schedule=TaskSchedule(schedule_type=ScheduleType.ON_DEMAND),
            enabled=True,
            priority=1
        )

        # Add tasks
        manager.add_task(high_priority_task)
        manager.add_task(low_priority_task)

        # Execute tasks in priority order
        results = []
        for task_id in ["high_pri", "low_pri"]:
            result = manager.execute_task(task_id)
            results.append(result)

        assert len(results) == 2
        assert results[0].task_id == "high_pri"
        assert results[1].task_id == "low_pri"

    def test_concurrent_task_execution(self, mock_config):
        """Test concurrent task execution."""
        manager = RecurringTaskManager(mock_config)

        async def slow_task(delay):
            await asyncio.sleep(delay)
            return f"completed_after_{delay}s"

        # Create tasks with different execution times
        tasks = []
        for i, delay in enumerate([0.1, 0.2, 0.3]):
            task = RecurringTask(
                task_id=f"concurrent_task_{i}",
                name=f"Concurrent Task {i}",
                task_function=lambda d=delay: slow_task(d),
                schedule=TaskSchedule(schedule_type=ScheduleType.ON_DEMAND),
                enabled=True
            )
            tasks.append(task)

        # Add and execute tasks
        for task in tasks:
            manager.add_task(task)

        # Execute all tasks concurrently
        start_time = time.time()
        results = []

        for task in tasks:
            result = manager.execute_task(task.task_id)
            results.append(result)

        execution_time = time.time() - start_time

        assert len(results) == 3
        assert all(result.status == TaskStatus.COMPLETED for result in results)
        assert execution_time < 0.5  # Should run concurrently

    def test_task_persistence(self, mock_config, sample_tasks, tmp_path):
        """Test task persistence to disk."""
        persist_path = tmp_path / "recurring_tasks.json"
        persist_config = mock_config.copy()
        persist_config["persistence_file"] = str(persist_path)

        manager = RecurringTaskManager(persist_config)

        # Add tasks
        for task in sample_tasks:
            manager.add_task(task)

        # Save tasks
        manager.save_tasks()

        # Verify file was created
        assert persist_path.exists()

        # Create new manager and load tasks
        new_manager = RecurringTaskManager(persist_config)
        new_manager.load_tasks()

        # Verify tasks were loaded
        assert len(new_manager.tasks) == 3

        # Verify task properties were preserved
        loaded_task = new_manager.get_task("task1")
        assert loaded_task is not None
        assert loaded_task.name == "First Task"
        assert loaded_task.enabled is True

    def test_error_handling_invalid_task_operations(self, mock_config):
        """Test error handling for invalid task operations."""
        manager = RecurringTaskManager(mock_config)

        # Try to get results for task that never executed
        results = manager.get_task_results("never_executed")
        assert results == []

        # Try to execute task with None function
        invalid_task = RecurringTask(
            task_id="invalid",
            name="Invalid Task",
            task_function=None,
            schedule=TaskSchedule(schedule_type=ScheduleType.ON_DEMAND)
        )
        manager.add_task(invalid_task)

        # Should handle gracefully
        result = manager.execute_task("invalid")
        assert result is not None
        assert result.status == TaskStatus.FAILED

    def test_task_health_monitoring(self, mock_config, sample_tasks):
        """Test task health monitoring."""
        manager = RecurringTaskManager(mock_config)

        # Add tasks
        for task in sample_tasks:
            manager.add_task(task)

        # Get health status
        health_status = manager.get_health_status()

        assert "overall" in health_status
        assert "task_health" in health_status
        assert "system_load" in health_status
        assert len(health_status["task_health"]) == 3

        # All tasks should be healthy initially
        assert all(task_health["healthy"] for task_health in health_status["task_health"].values())

    def test_task_cleanup_old_results(self, mock_config, sample_tasks):
        """Test cleanup of old task results."""
        manager = RecurringTaskManager(mock_config)

        # Add and execute task multiple times
        manager.add_task(sample_tasks[0])

        for _ in range(10):
            manager.execute_task("task1")

        # Should have 10 results
        assert len(manager.task_results["task1"]) == 10

        # Cleanup old results (keep only last 5)
        manager.cleanup_old_results("task1", keep_last=5)

        # Should now have only 5 results
        assert len(manager.task_results["task1"]) == 5

    def test_batch_task_operations(self, mock_config, sample_tasks):
        """Test batch task operations."""
        manager = RecurringTaskManager(mock_config)

        # Add tasks
        for task in sample_tasks:
            manager.add_task(task)

        # Execute batch of tasks
        task_ids = ["task1", "task2"]
        results = manager.execute_batch_tasks(task_ids)

        assert len(results) == 2
        assert all(result.status == TaskStatus.COMPLETED for result in results)

    def test_task_search_functionality(self, mock_config, sample_tasks):
        """Test task search functionality."""
        manager = RecurringTaskManager(mock_config)

        # Add tasks
        for task in sample_tasks:
            manager.add_task(task)

        # Search by name
        search_results = manager.search_tasks("First")
        assert len(search_results) == 1
        assert search_results[0].task_id == "task1"

        # Search by schedule type
        interval_tasks = manager.search_tasks(schedule_type=ScheduleType.INTERVAL)
        assert len(interval_tasks) == 1
        assert interval_tasks[0].task_id == "task1"

    def test_task_metrics_collection(self, mock_config, sample_tasks):
        """Test task metrics collection."""
        manager = RecurringTaskManager(mock_config)

        # Add and execute tasks
        manager.add_task(sample_tasks[0])  # Success
        manager.add_task(sample_tasks[2])  # Failure
        manager.execute_task("task1")
        manager.execute_task("task3")

        # Get metrics
        metrics = manager.get_metrics()

        assert "total_executions" in metrics
        assert "successful_executions" in metrics
        assert "failed_executions" in metrics
        assert "average_execution_time" in metrics
        assert metrics["total_executions"] == 2
        assert metrics["successful_executions"] == 1
        assert metrics["failed_executions"] == 1
