#!/usr/bin/env python3
"""
Performance benchmarking tests for ChattyCommander.
Measures response times, memory usage, and throughput under various conditions.
"""

import asyncio
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock, Mock, patch

import psutil
import pytest
from config import Config
from fastapi.testclient import TestClient
from model_manager import ModelManager
from state_manager import StateManager
from web_mode import WebModeServer

from chatty_commander.app.command_executor import CommandExecutor


class PerformanceMonitor:
    """Monitor system performance during tests."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.process = psutil.Process()

    def start(self):
        """Start performance monitoring."""
        self.start_time = time.perf_counter()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB

    def stop(self):
        """Stop performance monitoring."""
        self.end_time = time.perf_counter()
        self.end_memory = self.process.memory_info().rss / 1024 / 1024  # MB

    @property
    def duration(self):
        """Get execution duration in seconds."""
        return self.end_time - self.start_time if self.end_time else None

    @property
    def memory_delta(self):
        """Get memory usage change in MB."""
        return self.end_memory - self.start_memory if self.end_memory else None


class TestPerformanceBenchmarks:
    """Performance benchmark test suite."""

    @pytest.fixture
    def mock_managers(self):
        """Create lightweight mock managers for performance testing."""
        config = Mock(spec=Config)
        config.config = {"performance_test": True}

        state_manager = Mock(spec=StateManager)
        state_manager.current_state = "idle"
        state_manager.get_active_models.return_value = ["fast_model"]
        state_manager.add_state_change_callback = Mock()
        state_manager.change_state = Mock()

        model_manager = Mock(spec=ModelManager)
        command_executor = Mock(spec=CommandExecutor)

        return config, state_manager, model_manager, command_executor

    @pytest.fixture
    def web_server(self, mock_managers):
        """Create WebModeServer for performance testing."""
        with patch('chatty_commander.advisors.providers.build_provider_safe') as mock_build_provider:
            mock_provider = MagicMock()
            mock_provider.model = "test-model"
            mock_provider.api_mode = "completion"
            mock_build_provider.return_value = mock_provider
            config, state_manager, model_manager, command_executor = mock_managers
            return WebModeServer(
                config_manager=config,
                state_manager=state_manager,
                model_manager=model_manager,
                command_executor=command_executor,
                no_auth=True,
            )

    @pytest.fixture
    def test_client(self, web_server):
        """Create test client for API performance testing."""
        return TestClient(web_server.app)

    def test_api_response_time_benchmark(self, test_client):
        """Benchmark API response times for various endpoints."""
        endpoints = ["/api/v1/status", "/api/v1/config", "/api/v1/state"]

        results = {}

        for endpoint in endpoints:
            response_times = []

            # Warm up
            for _ in range(5):
                test_client.get(endpoint)

            # Measure response times
            for _ in range(50):
                start_time = time.perf_counter()
                response = test_client.get(endpoint)
                end_time = time.perf_counter()

                assert response.status_code == 200
                response_times.append((end_time - start_time) * 1000)  # Convert to ms

            results[endpoint] = {
                'mean': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'min': min(response_times),
                'max': max(response_times),
                'stdev': statistics.stdev(response_times) if len(response_times) > 1 else 0,
            }

        # Assert performance requirements
        for endpoint, stats in results.items():
            print(f"\n{endpoint} performance:")
            print(f"  Mean: {stats['mean']:.2f}ms")
            print(f"  Median: {stats['median']:.2f}ms")
            print(f"  Min: {stats['min']:.2f}ms")
            print(f"  Max: {stats['max']:.2f}ms")
            print(f"  StdDev: {stats['stdev']:.2f}ms")

            # Performance assertions (adjust thresholds as needed)
            assert (
                stats['mean'] < 100
            ), f"{endpoint} mean response time too high: {stats['mean']:.2f}ms"
            assert (
                stats['median'] < 50
            ), f"{endpoint} median response time too high: {stats['median']:.2f}ms"

    def test_concurrent_request_throughput(self, test_client):
        """Test API throughput under concurrent load."""
        num_threads = 10
        requests_per_thread = 20
        endpoint = "/api/v1/status"

        def make_requests(thread_id):
            """Make multiple requests from a single thread."""
            thread_times = []
            for i in range(
                requests_per_thread
            ):  # noqa: B007 - loop index not used; measuring throughput only
                start_time = time.perf_counter()
                response = test_client.get(endpoint)
                end_time = time.perf_counter()

                assert response.status_code == 200
                thread_times.append(end_time - start_time)

            return thread_id, thread_times

        monitor = PerformanceMonitor()
        monitor.start()

        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_requests, i) for i in range(num_threads)]

            all_times = []
            for future in as_completed(futures):
                thread_id, times = future.result()
                all_times.extend(times)

        monitor.stop()

        # Calculate throughput metrics
        total_requests = num_threads * requests_per_thread
        total_time = monitor.duration
        throughput = total_requests / total_time

        avg_response_time = statistics.mean(all_times) * 1000  # Convert to ms

        print("\nConcurrent load test results:")
        print(f"  Total requests: {total_requests}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Throughput: {throughput:.2f} req/s")
        print(f"  Average response time: {avg_response_time:.2f}ms")
        print(f"  Memory delta: {monitor.memory_delta:.2f}MB")

        # Performance assertions
        assert throughput > 50, f"Throughput too low: {throughput:.2f} req/s"
        assert avg_response_time < 200, f"Average response time too high: {avg_response_time:.2f}ms"
        assert monitor.memory_delta < 50, f"Memory usage too high: {monitor.memory_delta:.2f}MB"

    def test_memory_usage_stability(self, test_client):
        """Test memory usage stability over extended operation."""
        endpoint = "/api/v1/status"
        num_iterations = 100

        memory_samples = []
        process = psutil.Process()

        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024

        for i in range(num_iterations):
            response = test_client.get(endpoint)
            assert response.status_code == 200

            # Sample memory every 10 iterations
            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)

        # Analyze memory usage
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - baseline_memory
        max_memory = max(memory_samples)
        memory_variance = statistics.variance(memory_samples) if len(memory_samples) > 1 else 0

        print("\nMemory stability test results:")
        print(f"  Baseline memory: {baseline_memory:.2f}MB")
        print(f"  Final memory: {final_memory:.2f}MB")
        print(f"  Memory growth: {memory_growth:.2f}MB")
        print(f"  Max memory: {max_memory:.2f}MB")
        print(f"  Memory variance: {memory_variance:.2f}")

        # Memory stability assertions
        assert memory_growth < 10, f"Memory growth too high: {memory_growth:.2f}MB"
        assert memory_variance < 5, f"Memory usage too unstable: {memory_variance:.2f}"

    def test_state_change_performance(self, test_client, mock_managers):
        """Benchmark state change operations."""
        _, state_manager, _, _ = mock_managers

        states = ["idle", "chatty", "computer"]
        num_changes = 50

        response_times = []

        for i in range(num_changes):
            target_state = states[i % len(states)]

            start_time = time.perf_counter()
            response = test_client.post("/api/v1/state", json={"state": target_state})
            end_time = time.perf_counter()

            assert response.status_code == 200
            response_times.append((end_time - start_time) * 1000)

        # Calculate statistics
        mean_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        max_time = max(response_times)

        print("\nState change performance:")
        print(f"  Mean time: {mean_time:.2f}ms")
        print(f"  Median time: {median_time:.2f}ms")
        print(f"  Max time: {max_time:.2f}ms")

        # Performance assertions
        assert mean_time < 50, f"State change mean time too high: {mean_time:.2f}ms"
        assert max_time < 200, f"State change max time too high: {max_time:.2f}ms"

        # Verify all state changes were called
        assert state_manager.change_state.call_count == num_changes

    def test_websocket_message_broadcast_performance(self, web_server):
        """Test WebSocket message broadcasting performance."""
        from unittest.mock import AsyncMock

        from web_mode import WebSocketMessage

        # Create mock WebSocket connections
        num_connections = 50
        mock_connections = []

        for i in range(
            num_connections
        ):  # noqa: B007 - loop index not used; creating mock connections
            mock_ws = AsyncMock()
            mock_connections.append(mock_ws)
            web_server.active_connections.add(mock_ws)

        # Test message broadcasting
        message = WebSocketMessage(type="performance_test", data={"iteration": 1})

        # Measure broadcast performance with event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            start_time = time.perf_counter()
            loop.run_until_complete(web_server._broadcast_message(message))
            end_time = time.perf_counter()

            broadcast_time = (end_time - start_time) * 1000  # Convert to ms

            print("\nWebSocket broadcast performance:")
            print(f"  Connections: {num_connections}")
            print(f"  Broadcast time: {broadcast_time:.2f}ms")
            print(f"  Time per connection: {broadcast_time/num_connections:.2f}ms")

            # Verify all connections received the message
            for mock_ws in mock_connections:
                mock_ws.send_text.assert_called_once()

            # Performance assertions
            assert broadcast_time < 100, f"Broadcast time too high: {broadcast_time:.2f}ms"
            assert (
                broadcast_time / num_connections < 2
            ), f"Per-connection time too high: {broadcast_time/num_connections:.2f}ms"
        finally:
            loop.close()

    def test_config_update_performance(self, test_client, mock_managers):
        """Test configuration update performance."""
        config, _, _, _ = mock_managers
        config.save_config = Mock()

        # Test various config sizes
        config_sizes = [
            {"small": "value"},
            {f"key_{i}": f"value_{i}" for i in range(10)},
            {f"large_key_{i}": f"large_value_{i}" * 10 for i in range(50)},
        ]

        for i, config_data in enumerate(config_sizes):
            response_times = []

            for _ in range(10):
                start_time = time.perf_counter()
                response = test_client.put("/api/v1/config", json=config_data)
                end_time = time.perf_counter()

                assert response.status_code == 200
                response_times.append((end_time - start_time) * 1000)

            mean_time = statistics.mean(response_times)
            print(f"\nConfig update performance (size {i+1}):")
            print(f"  Config keys: {len(config_data)}")
            print(f"  Mean time: {mean_time:.2f}ms")

            # Performance assertion
            assert mean_time < 100, f"Config update time too high: {mean_time:.2f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to show print statements
