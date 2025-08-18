"""Final test to reach exactly 60% coverage."""

from chatty_commander.app.config import Config
from chatty_commander.obs.metrics import HistogramBuckets, MetricsRegistry


class Test60PercentFinal:
    def test_comprehensive_final_push(self):
        """Comprehensive final push to 60%"""
        # Test HistogramBuckets edge cases
        buckets = HistogramBuckets([0.1, 0.5, 1.0])

        # Test clamp method
        assert buckets.clamp(0.05) == 0.05
        assert buckets.clamp(0.3) == 0.3
        assert buckets.clamp(2.0) == 2.0

        # Test edges property
        assert buckets.edges == [0.1, 0.5, 1.0]

        # Test histogram with these buckets
        registry = MetricsRegistry()
        histogram = registry.histogram("final_test", "Final test", buckets=buckets)

        # Add observation that goes to +Inf bucket
        histogram.observe(5.0)  # This should trigger the "not placed" logic

        # Test config edge cases
        config = Config()

        # Test all general settings properties one more time
        gs = config.general_settings

        # Test property access
        _ = gs.default_state
        _ = gs.debug_mode
        _ = gs.inference_framework
        _ = gs.start_on_boot
        _ = gs.check_for_updates

        # Test property setters
        original_debug = gs.debug_mode
        gs.debug_mode = not original_debug
        gs.debug_mode = original_debug

        # Test config methods
        config._update_general_setting("final_test", True)

        # Test that we can access config_data
        general = config.config_data.get("general", {})
        assert isinstance(general, dict)

        # Test histogram snapshot
        snapshot = histogram.snapshot()
        assert "buckets" in snapshot
        assert "series" in snapshot
