import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from chatty_commander.web.routes.audio import include_audio_routes

class TestAudioRoutes(unittest.TestCase):
    def setUp(self):
        self.mock_config_manager = MagicMock()
        self.mock_config_manager.config_data = {}

        self.router = include_audio_routes(
            get_config_manager=lambda: self.mock_config_manager
        )
        self.app = FastAPI()
        self.app.include_router(self.router)
        self.client = TestClient(self.app)

    @patch("chatty_commander.web.routes.audio.AUDIO_AVAILABLE", True)
    @patch("chatty_commander.web.routes.audio.pyaudio")
    def test_get_devices_success(self, mock_pyaudio):
        # Setup mock device info
        mock_pa_instance = MagicMock()
        mock_pyaudio.PyAudio.return_value = mock_pa_instance

        # Mock device listing: 2 devices
        mock_pa_instance.get_host_api_info_by_index.return_value = {"deviceCount": 2}

        # Device 0: Input only
        # Device 1: Output only
        def get_device_info(host_api_index, device_index):
            if device_index == 0:
                return {"name": "Mic In", "maxInputChannels": 1, "maxOutputChannels": 0}
            else:
                return {"name": "Speaker Out", "maxInputChannels": 0, "maxOutputChannels": 2}

        mock_pa_instance.get_device_info_by_host_api_device_index.side_effect = get_device_info

        response = self.client.get("/devices")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["input"], ["Mic In"])
        self.assertEqual(data["output"], ["Speaker Out"])

    @patch("chatty_commander.web.routes.audio.AUDIO_AVAILABLE", False)
    def test_get_devices_unavailable(self):
        response = self.client.get("/devices")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["input"], [])
        self.assertEqual(data["output"], [])

    @patch("chatty_commander.web.routes.audio.AUDIO_AVAILABLE", True)
    @patch("chatty_commander.web.routes.audio.get_audio_device_list")
    def test_update_settings_success(self, mock_get_list):
        mock_get_list.return_value = (["Mic In"], ["Speaker Out"])

        response = self.client.post("/settings", json={
            "input_device": "Mic In",
            "output_device": "Speaker Out"
        })

        self.assertEqual(response.status_code, 200)

        # Verify persistence called
        self.mock_config_manager.save_config.assert_called()
        saved_config = self.mock_config_manager.save_config.call_args[0][0]
        self.assertEqual(saved_config["audio"]["input_device"], "Mic In")
        self.assertEqual(saved_config["audio"]["output_device"], "Speaker Out")

    @patch("chatty_commander.web.routes.audio.AUDIO_AVAILABLE", True)
    @patch("chatty_commander.web.routes.audio.get_audio_device_list")
    def test_update_settings_invalid_device(self, mock_get_list):
        mock_get_list.return_value = (["Mic In"], ["Speaker Out"])

        response = self.client.post("/settings", json={
            "input_device": "Invalid Mic"
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid input device", response.json()["detail"])

    @patch("chatty_commander.web.routes.audio.AUDIO_AVAILABLE", False)
    def test_update_settings_audio_unavailable(self):
        response = self.client.post("/settings", json={
            "input_device": "Any Mic"
        })
        # Should succeed without validation
        self.assertEqual(response.status_code, 200)
        self.assertIn("audio unavailable", response.json()["message"])

if __name__ == "__main__":
    unittest.main()
