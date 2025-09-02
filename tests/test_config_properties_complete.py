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

"""Test all config properties to reach 60%."""

from chatty_commander.app.config import Config


class TestConfigPropertiesComplete:
    def test_all_general_settings_properties(self):
        """Test all general settings properties"""
        config = Config()
        gs = config.general_settings

        # Test inference_framework property and setter
        framework = gs.inference_framework
        assert isinstance(framework, str)
        gs.inference_framework = "pytorch"
        assert gs.inference_framework == "pytorch"
        gs.inference_framework = "onnx"  # Reset

        # Test start_on_boot property and setter
        start_boot = gs.start_on_boot
        assert isinstance(start_boot, bool)
        gs.start_on_boot = True
        assert gs.start_on_boot is True
        gs.start_on_boot = False
        assert gs.start_on_boot is False

        # Test check_for_updates property and setter
        check_updates = gs.check_for_updates
        assert isinstance(check_updates, bool)
        gs.check_for_updates = True
        assert gs.check_for_updates is True
        gs.check_for_updates = False
        assert gs.check_for_updates is False

        # Test debug_mode property and setter
        debug = gs.debug_mode
        assert isinstance(debug, bool)
        gs.debug_mode = True
        assert gs.debug_mode is True
        gs.debug_mode = False
        assert gs.debug_mode is False

    def test_property_setters_with_type_conversion(self):
        """Test property setters with type conversion"""
        config = Config()
        gs = config.general_settings

        # Test that setters convert values to appropriate types
        gs.debug_mode = 1
        assert gs.debug_mode is True
        gs.debug_mode = 0
        assert gs.debug_mode is False

        gs.start_on_boot = 1
        assert gs.start_on_boot is True
        gs.start_on_boot = 0
        assert gs.start_on_boot is False

        gs.check_for_updates = 1
        assert gs.check_for_updates is True
        gs.check_for_updates = 0
        assert gs.check_for_updates is False

        # Test string conversion for inference_framework
        gs.inference_framework = "tensorflow"
        assert gs.inference_framework == "tensorflow"

    def test_config_data_updates(self):
        """Test that property setters update config_data"""
        config = Config()
        gs = config.general_settings

        # Set properties and verify config_data is updated
        gs.debug_mode = True
        general = config.config_data.get("general", {})
        assert general.get("debug_mode") is True

        gs.start_on_boot = True
        general = config.config_data.get("general", {})
        assert general.get("start_on_boot") is True

        gs.check_for_updates = False
        general = config.config_data.get("general", {})
        assert general.get("check_for_updates") is False

        gs.inference_framework = "custom"
        general = config.config_data.get("general", {})
        assert general.get("inference_framework") == "custom"
