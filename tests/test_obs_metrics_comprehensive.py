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

"""Comprehensive tests for obs/metrics.py to increase coverage."""


from chatty_commander.obs.metrics import Counter, Gauge, HistogramBuckets, MetricsRegistry


class TestCounter:
    def test_counter_negative_amount(self):
        """Test that negative amounts are converted to 0"""
        counter = Counter("test_counter", "Test counter")
        counter.inc(-5)
        assert counter.get() == 0

    def test_counter_with_labels(self):
        """Test counter with labels"""
        counter = Counter("test_counter", "Test counter")
        counter.inc(1, {"method": "GET"})
        counter.inc(2, {"method": "POST"})

        assert counter.get({"method": "GET"}) == 1
        assert counter.get({"method": "POST"}) == 2
        assert counter.get({"method": "DELETE"}) == 0

    def test_counter_samples(self):
        """Test counter samples method"""
        counter = Counter("test_counter", "Test counter")
        counter.inc(1, {"method": "GET"})
        counter.inc(2, {"method": "POST"})

        samples = counter.samples()
        assert len(samples) == 2
        # Check that samples contain the expected data
        sample_dict = {
            tuple(sorted(labels.items())): value for labels, value in samples
        }
        assert sample_dict[(("method", "GET"),)] == 1
        assert sample_dict[(("method", "POST"),)] == 2


class TestGauge:
    def test_gauge_set_and_get(self):
        """Test gauge set and get operations"""
        gauge = Gauge("test_gauge", "Test gauge")
        gauge.set(42.5)
        assert gauge.get() == 42.5

    def test_gauge_with_labels(self):
        """Test gauge with labels"""
        gauge = Gauge("test_gauge", "Test gauge")
        gauge.set(10.0, {"region": "us-east-1"})
        gauge.set(20.0, {"region": "us-west-2"})

        assert gauge.get({"region": "us-east-1"}) == 10.0
        assert gauge.get({"region": "us-west-2"}) == 20.0
        assert gauge.get({"region": "eu-west-1"}) == 0.0

    def test_gauge_samples(self):
        """Test gauge samples method"""
        gauge = Gauge("test_gauge", "Test gauge")
        gauge.set(10.0, {"region": "us-east-1"})
        gauge.set(20.0, {"region": "us-west-2"})

        samples = gauge.samples()
        assert len(samples) == 2
        # Check that samples contain the expected data
        sample_dict = {
            tuple(sorted(labels.items())): value for labels, value in samples
        }
        assert sample_dict[(("region", "us-east-1"),)] == 10.0
        assert sample_dict[(("region", "us-west-2"),)] == 20.0


class TestMetricsRegistry:
    def test_registry_counter(self):
        """Test registry counter creation and retrieval"""
        registry = MetricsRegistry()
        counter = registry.counter("test_counter", "Test counter")

        # Should return the same instance on subsequent calls
        counter2 = registry.counter("test_counter", "Test counter")
        assert counter is counter2

    def test_registry_gauge(self):
        """Test registry gauge creation and retrieval"""
        registry = MetricsRegistry()
        gauge = registry.gauge("test_gauge", "Test gauge")

        # Should return the same instance on subsequent calls
        gauge2 = registry.gauge("test_gauge", "Test gauge")
        assert gauge is gauge2

    def test_registry_histogram(self):
        """Test registry histogram creation and retrieval"""
        registry = MetricsRegistry()
        histogram = registry.histogram("test_histogram", "Test histogram")

        # Should return the same instance on subsequent calls
        histogram2 = registry.histogram("test_histogram", "Test histogram")
        assert histogram is histogram2

    def test_registry_to_json(self):
        """Test registry JSON export"""
        registry = MetricsRegistry()
        counter = registry.counter("test_counter", "Test counter")
        gauge = registry.gauge("test_gauge", "Test gauge")
        histogram = registry.histogram("test_histogram", "Test histogram")

        counter.inc(5)
        gauge.set(42.0)
        histogram.observe(1.5)

        json_data = registry.to_json()
        assert "counters" in json_data
        assert "gauges" in json_data
        assert "histograms" in json_data

        assert "test_counter" in json_data["counters"]
        assert "test_gauge" in json_data["gauges"]
        assert "test_histogram" in json_data["histograms"]


class TestMetricKeyGeneration:
    def test_key_generation_empty_labels(self):
        """Test key generation with empty labels"""
        counter = Counter("test", "test")
        key1 = counter._key(None)
        key2 = counter._key({})
        assert key1 == ()
        assert key2 == ()

    def test_key_generation_sorted_labels(self):
        """Test that keys are generated in sorted order"""
        counter = Counter("test", "test")
        key1 = counter._key({"b": "2", "a": "1"})
        key2 = counter._key({"a": "1", "b": "2"})
        assert key1 == key2
        assert key1 == (("a", "1"), ("b", "2"))

    def test_key_generation_string_conversion(self):
        """Test that label values are converted to strings"""
        counter = Counter("test", "test")
        key = counter._key({"num": 123, "bool": True})
        assert key == (("bool", "True"), ("num", "123"))


class TestHistogramBuckets:
    def test_bucket_clamp_and_snapshot(self):
        """Test histogram buckets clamp values and snapshot structure."""
        buckets = HistogramBuckets([0.1, 0.5, 1.0])
        assert buckets.clamp(-1.0) == 0.0
        assert buckets.clamp(0.3) == 0.3

        registry = MetricsRegistry()
        histogram = registry.histogram("bucket_test", "Bucket test", buckets=buckets)
        histogram.observe(5.0)

        snapshot = histogram.snapshot()
        assert snapshot["buckets"] == [0.1, 0.5, 1.0]
        assert snapshot["series"]
        assert snapshot["series"][0]["counts"][-1] == 1
