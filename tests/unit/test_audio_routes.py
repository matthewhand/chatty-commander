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

"""Tests for audio routes module."""

import pytest

from src.chatty_commander.web.routes.audio import (
    AudioDevices,
    AudioDeviceRequest,
)


class TestAudioDevices:
    """Tests for AudioDevices model."""

    def test_default_empty(self):
        """Test default empty audio devices."""
        devices = AudioDevices()
        assert devices.input == []
        assert devices.output == []

    def test_with_devices(self):
        """Test audio devices with values."""
        devices = AudioDevices(
            input=["Mic 1", "Mic 2"],
            output=["Speaker 1"]
        )
        assert devices.input == ["Mic 1", "Mic 2"]
        assert devices.output == ["Speaker 1"]

    def test_input_only(self):
        """Test audio devices with only input."""
        devices = AudioDevices(input=["Microphone"])
        assert devices.input == ["Microphone"]
        assert devices.output == []

    def test_output_only(self):
        """Test audio devices with only output."""
        devices = AudioDevices(output=["Headphones"])
        assert devices.input == []
        assert devices.output == ["Headphones"]


class TestAudioDeviceRequest:
    """Tests for AudioDeviceRequest model."""

    def test_valid_request(self):
        """Test creating valid request."""
        request = AudioDeviceRequest(device_id="device_123")
        assert request.device_id == "device_123"

    def test_request_with_special_chars(self):
        """Test request with special characters in device ID."""
        request = AudioDeviceRequest(device_id="device-with_special.chars")
        assert request.device_id == "device-with_special.chars"


class TestAudioModelsEdgeCases:
    """Edge case tests."""

    def test_empty_device_id(self):
        """Test with empty device ID."""
        request = AudioDeviceRequest(device_id="")
        assert request.device_id == ""

    def test_long_device_id(self):
        """Test with very long device ID."""
        long_id = "x" * 1000
        request = AudioDeviceRequest(device_id=long_id)
        assert request.device_id == long_id

    def test_audio_devices_empty_strings(self):
        """Test audio devices with empty strings."""
        devices = AudioDevices(input=[""], output=[""])
        assert devices.input == [""]
        assert devices.output == [""]
