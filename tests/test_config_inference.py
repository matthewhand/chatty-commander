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

"""Test config inference framework property."""

from chatty_commander.app.config import Config


class TestConfigInference:
    def test_inference_framework_property(self):
        """Test inference_framework property"""
        config = Config()
        gs = config.general_settings

        # Test getting inference_framework
        framework = gs.inference_framework
        assert isinstance(framework, str)
        assert isinstance(framework, str) and len(framework) > 0  # Common frameworks

        # Test debug_mode setter to trigger _update_general_setting
        gs.debug_mode = True
        assert gs.debug_mode is True

        gs.debug_mode = False
        assert gs.debug_mode is False

        # Test that we can access the property multiple times
        framework1 = gs.inference_framework
        framework2 = gs.inference_framework
        assert framework1 == framework2

    def test_config_general_data_access(self):
        """Test accessing general config data"""
        config = Config()

        # Test that general section exists in config_data
        general = config.config_data.get("general", {})
        assert isinstance(general, dict)

        # Test accessing inference_framework from config_data
        framework = general.get("inference_framework", "onnx")
        assert isinstance(framework, str)

        # Test accessing debug_mode from config_data
        debug = general.get("debug_mode", True)
        assert isinstance(debug, bool)

    def test_debug_mode_setter(self):
        """Test debug_mode setter functionality"""
        config = Config()
        gs = config.general_settings

        # Test setting debug_mode to various values
        gs.debug_mode = True
        assert gs.debug_mode is True

        gs.debug_mode = False
        assert gs.debug_mode is False

        gs.debug_mode = 1  # Should convert to bool
        assert gs.debug_mode is True

        gs.debug_mode = 0  # Should convert to bool
        assert gs.debug_mode is False

        gs.debug_mode = "true"  # Should convert to bool
        assert gs.debug_mode is True

        gs.debug_mode = ""  # Should convert to bool
        assert gs.debug_mode is False
