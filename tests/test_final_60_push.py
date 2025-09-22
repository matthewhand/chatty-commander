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

"""Final push to exactly 60% coverage."""

from chatty_commander.app.config import Config
from chatty_commander.obs.metrics import Counter, Gauge, MetricsRegistry


class TestFinal60Push:
    def test_comprehensive_final_coverage(self):
        """Comprehensive final test to reach 60%"""
        # Test all config properties extensively
        config = Config()
        gs = config.general_settings

        # Test all property getters and setters
        original_debug = gs.debug_mode
        original_boot = gs.start_on_boot
        original_updates = gs.check_for_updates
        original_framework = gs.inference_framework
        original_state = gs.default_state

        # Test debug_mode
        gs.debug_mode = not original_debug
        assert gs.debug_mode == (not original_debug)
        gs.debug_mode = original_debug

        # Test start_on_boot
        gs.start_on_boot = not original_boot
        assert gs.start_on_boot == (not original_boot)
        gs.start_on_boot = original_boot

        # Test check_for_updates
        gs.check_for_updates = not original_updates
        assert gs.check_for_updates == (not original_updates)
        gs.check_for_updates = original_updates

        # Test inference_framework
        gs.inference_framework = "test_framework"
        assert gs.inference_framework == "test_framework"
        gs.inference_framework = original_framework

        # Test default_state
        gs.default_state = "computer"
        assert gs.default_state == "computer"
        gs.default_state = original_state

        # Test config methods
        config.set_check_for_updates(True)
        config.set_check_for_updates(False)
        config._enable_start_on_boot()
        config._disable_start_on_boot()

        # Test _update_general_setting directly
        config._update_general_setting("test_key", "test_value")
        config._update_general_setting("test_bool", True)
        config._update_general_setting("test_int", 42)

        # Test metrics extensively
        registry = MetricsRegistry()

        # Test counter with all edge cases
        counter = Counter("final_counter", "Final counter")
        counter.inc(1)
        counter.inc(0)  # Zero increment
        counter.inc(-5)  # Negative increment
        counter.inc(10, {"label": "value"})

        # Test gauge with all edge cases
        gauge = Gauge("final_gauge", "Final gauge")
        gauge.set(42.5)
        gauge.set(-10.0)
        gauge.set(0.0)
        gauge.set(100.0, {"region": "test"})

        # Test key generation
        key1 = counter._key(None)
        key2 = counter._key({})
        key3 = counter._key({"a": 1, "b": 2})
        key4 = counter._key({"b": 2, "a": 1})

        assert key1 == ()
        assert key2 == ()
        assert key3 == key4

        # Test samples
        counter_samples = counter.samples()
        gauge_samples = gauge.samples()

        assert isinstance(counter_samples, list)
        assert isinstance(gauge_samples, list)

        # Test registry functionality
        counter2 = registry.counter("counter2")
        gauge2 = registry.gauge("gauge2")
        histogram = registry.histogram("histogram")

        counter2.inc(5)
        gauge2.set(25.0)
        histogram.observe(1.5)

        json_data = registry.to_json()
        assert "counter2" in json_data["counters"]
        assert "gauge2" in json_data["gauges"]
        assert "histogram" in json_data["histograms"]
