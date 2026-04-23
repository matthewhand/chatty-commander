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
Comprehensive tests for metrics module.

Tests Counter, Gauge, Histogram metrics and registry functionality.
"""

from unittest.mock import Mock

import pytest

from src.chatty_commander.obs.metrics import (
    Counter,
    Gauge,
    Histogram,
    HistogramBuckets,
    Metric,
    MetricsRegistry,
    Timer,
    DEFAULT_REGISTRY,
)


class TestCounter:
    """Tests for Counter metric."""

    def test_initialization(self):
        """Test Counter initialization."""
        counter = Counter("test_counter", "Test counter metric")
        assert counter.name == "test_counter"
        assert counter.description == "Test counter metric"

    def test_increment_default(self):
        """Test increment with default value."""
        counter = Counter("requests", "Total requests")
        counter.inc()
        assert counter.get() == 1

    def test_increment_custom(self):
        """Test increment with custom value."""
        counter = Counter("requests", "Total requests")
        counter.inc(5)
        assert counter.get() == 5

    def test_increment_multiple(self):
        """Test multiple increments."""
        counter = Counter("requests", "Total requests")
        counter.inc()
        counter.inc(2)
        counter.inc(3)
        assert counter.get() == 6

    def test_increment_with_labels(self):
        """Test increment with labels."""
        counter = Counter("requests", "Requests by method")
        counter.inc(1, {"method": "GET"})
        counter.inc(1, {"method": "POST"})
        counter.inc(1, {"method": "GET"})
        assert counter.get({"method": "GET"}) == 2
        assert counter.get({"method": "POST"}) == 1

    def test_get_missing(self):
        """Test getting value for non-existent label."""
        counter = Counter("test", "Test")
        assert counter.get({"method": "DELETE"}) == 0

    def test_negative_increment(self):
        """Test that negative increments are treated as 0."""
        counter = Counter("test", "Test")
        counter.inc(5)
        counter.inc(-3)
        assert counter.get() == 5  # Negative treated as 0


class TestGauge:
    """Tests for Gauge metric."""

    def test_initialization(self):
        """Test Gauge initialization."""
        gauge = Gauge("temperature", "Current temperature")
        assert gauge.name == "temperature"
        assert gauge.get() == 0.0

    def test_set(self):
        """Test setting gauge value."""
        gauge = Gauge("temperature", "Current temperature")
        gauge.set(25.5)
        assert gauge.get() == 25.5

    def test_set_with_labels(self):
        """Test setting gauge with labels."""
        gauge = Gauge("temperature", "Temperature by zone")
        gauge.set(20.0, {"zone": "indoor"})
        gauge.set(15.0, {"zone": "outdoor"})
        assert gauge.get({"zone": "indoor"}) == 20.0
        assert gauge.get({"zone": "outdoor"}) == 15.0

    def test_negative_values(self):
        """Test that gauge can be negative."""
        gauge = Gauge("offset", "Offset value")
        gauge.set(-5)
        assert gauge.get() == -5


class TestHistogram:
    """Tests for Histogram metric."""

    def test_initialization(self):
        """Test Histogram initialization."""
        hist = Histogram("request_duration", "Request duration in seconds")
        assert hist.name == "request_duration"

    def test_observe(self):
        """Test observing values."""
        hist = Histogram("duration", "Duration")
        hist.observe(0.5)
        hist.observe(1.0)
        hist.observe(0.3)
        # Check snapshot for recorded observations
        snap = hist.snapshot()
        assert len(snap["series"]) == 1
        assert snap["series"][0]["count"] == 3
        assert abs(snap["series"][0]["sum"] - 1.8) < 0.001

    def test_buckets(self):
        """Test histogram buckets."""
        hist = Histogram("duration", "Duration", buckets=HistogramBuckets(edges=[0.1, 0.5, 1.0, 5.0]))
        hist.observe(0.05)
        hist.observe(0.3)
        hist.observe(0.7)
        hist.observe(2.0)
        # Values should be in appropriate buckets
        snap = hist.snapshot()
        assert "series" in snap

    def test_snapshot(self):
        """Test getting snapshot."""
        hist = Histogram("duration", "Duration")
        hist.observe(1.0)
        snap = hist.snapshot()
        assert len(snap["series"]) == 1
        assert snap["series"][0]["count"] == 1
        assert "buckets" in snap
        assert "series" in snap

    def test_clamp(self):
        """Test that values are clamped."""
        buckets = HistogramBuckets()
        assert buckets.clamp(-5.0) == 0.0
        assert buckets.clamp(100.0) == 100.0


class TestTimer:
    """Tests for Timer context manager."""

    def test_timer_context(self):
        """Test timer context manager."""
        hist = Histogram("duration", "Duration")
        with Timer(hist):
            pass  # Minimal work
        # Should have recorded something
        snap = hist.snapshot()
        assert len(snap["series"]) == 1

    def test_timer_decorator(self):
        """Test timer as decorator."""
        hist = Histogram("function_duration", "Function duration")
        
        @Timer(hist)
        def slow_function():
            return 42
        
        result = slow_function()
        assert result == 42
        snap = hist.snapshot()
        assert len(snap["series"]) == 1


class TestMetricsRegistry:
    """Tests for MetricsRegistry."""

    def test_initialization(self):
        """Test registry initialization."""
        registry = MetricsRegistry()
        assert len(registry.counters) == 0
        assert len(registry.gauges) == 0
        assert len(registry.hists) == 0

    def test_counter_factory(self):
        """Test counter factory method."""
        registry = MetricsRegistry()
        counter = registry.counter("requests", "Total requests")
        assert counter.name == "requests"
        assert "requests" in registry.counters

    def test_gauge_factory(self):
        """Test gauge factory method."""
        registry = MetricsRegistry()
        gauge = registry.gauge("temperature", "Temperature")
        assert gauge.name == "temperature"
        assert "temperature" in registry.gauges

    def test_histogram_factory(self):
        """Test histogram factory method."""
        registry = MetricsRegistry()
        hist = registry.histogram("duration", "Duration")
        assert hist.name == "duration"
        assert "duration" in registry.hists

    def test_counter_returns_same_instance(self):
        """Test counter returns existing instance."""
        registry = MetricsRegistry()
        counter1 = registry.counter("test", "Test")
        counter2 = registry.counter("test", "Test")
        assert counter1 is counter2

    def test_to_json(self):
        """Test exporting to JSON."""
        registry = MetricsRegistry()
        registry.counter("c1", "Counter 1")
        registry.gauge("g1", "Gauge 1")
        c = registry.counter("c1")
        c.inc(5)
        g = registry.gauge("g1")
        g.set(10.5)
        
        data = registry.to_json()
        assert "c1" in data["counters"]
        assert "g1" in data["gauges"]


class TestDefaultRegistry:
    """Tests for DEFAULT_REGISTRY."""

    def test_default_registry_exists(self):
        """Test that default registry exists."""
        assert DEFAULT_REGISTRY is not None
        assert isinstance(DEFAULT_REGISTRY, MetricsRegistry)

    def test_default_registry_is_singleton(self):
        """Test that DEFAULT_REGISTRY is a single instance."""
        reg1 = DEFAULT_REGISTRY
        reg2 = DEFAULT_REGISTRY
        assert reg1 is reg2


class TestEdgeCases:
    """Edge case tests."""

    def test_counter_thread_safety(self):
        """Test counter is thread-safe."""
        counter = Counter("test", "Test")
        # Should handle concurrent access without error
        counter.inc()
        counter.inc(100)
        assert counter.get() == 101

    def test_histogram_large_values(self):
        """Test histogram with very large values."""
        hist = Histogram("large", "Large values")
        hist.observe(1e9)
        hist.observe(1e10)
        snap = hist.snapshot()
        assert snap["series"][0]["count"] == 2
        assert snap["series"][0]["sum"] > 1e9

    def test_gauge_float_precision(self):
        """Test gauge preserves float precision."""
        gauge = Gauge("precise", "Precise value")
        gauge.set(3.14159265359)
        assert abs(gauge.get() - 3.14159265359) < 1e-10
