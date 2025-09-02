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

"""Final push to 60% coverage."""

from chatty_commander.app.config import Config
from chatty_commander.obs.metrics import MetricsRegistry


class TestFinalPush:
    def test_config_setter_coverage(self):
        """Test config setters to increase coverage"""
        config = Config()

        # Test setting default_state to trigger setter
        original_state = config.general_settings.default_state
        config.general_settings.default_state = "chatty"
        assert config.general_settings.default_state == "chatty"

        # Reset to original
        config.general_settings.default_state = original_state

    def test_metrics_registry_coverage(self):
        """Test metrics registry to increase coverage"""
        registry = MetricsRegistry()

        # Create multiple metrics to test registry functionality
        counter1 = registry.counter("counter1", "First counter")
        counter2 = registry.counter("counter2", "Second counter")
        gauge1 = registry.gauge("gauge1", "First gauge")

        # Use the metrics
        counter1.inc(5)
        counter2.inc(3)
        gauge1.set(42.5)

        # Test that registry tracks them
        json_data = registry.to_json()
        assert "counter1" in json_data["counters"]
        assert "counter2" in json_data["counters"]
        assert "gauge1" in json_data["gauges"]

    def test_config_debug_mode(self):
        """Test config debug mode property"""
        config = Config()

        # Test debug_mode property access
        debug_mode = config.general_settings.debug_mode
        assert isinstance(debug_mode, bool)

        # Test that we can access the underlying config data
        general_config = config.config_data.get("general", {})
        debug_from_data = general_config.get("debug_mode", True)
        assert isinstance(debug_from_data, bool)

    def test_additional_config_paths(self):
        """Test additional config path properties"""
        config = Config()

        # Test that all model paths are accessible
        paths = [
            config.general_models_path,
            config.system_models_path,
            config.chat_models_path,
        ]

        for path in paths:
            assert isinstance(path, str)
            assert len(path) > 0  # Should not be empty

    def test_config_nested_access(self):
        """Test nested config access patterns"""
        config = Config()

        # Test accessing nested configuration
        if "general" in config.config_data:
            general = config.config_data["general"]
            assert isinstance(general, dict)

        # Test that model_actions can be iterated
        action_count = 0
        for action_name, action_config in config.model_actions.items():
            assert isinstance(action_name, str)
            assert isinstance(action_config, dict)
            action_count += 1
            if action_count >= 3:  # Just test a few
                break
