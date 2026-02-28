from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.routes.audio import include_audio_routes


def setup_mock_config():
    config = MagicMock()
    config.config_data = {}
    config.save_config = MagicMock()
    return config


def setup_app(config):
    app = FastAPI()
    app.include_router(include_audio_routes(lambda: config))
    return TestClient(app)


class MockPyAudio:
    def __init__(self, devices):
        self._devices = devices

    def PyAudio(self):
        p = MagicMock()

        p.get_host_api_info_by_index.return_value = {"deviceCount": len(self._devices)}

        def get_device_info(api_index, device_index):
            return self._devices[device_index]

        p.get_device_info_by_host_api_device_index.side_effect = get_device_info
        return p


def test_get_audio_devices_with_pyaudio():
    devices = [
        {"name": "Mic 1", "maxInputChannels": 2, "maxOutputChannels": 0},
        {"name": "Speaker 1", "maxInputChannels": 0, "maxOutputChannels": 2},
    ]

    mock_pyaudio = MockPyAudio(devices)
    with patch.dict("sys.modules", {"pyaudio": mock_pyaudio}):
        config = setup_mock_config()
        client = setup_app(config)

        response = client.get("/api/audio/devices")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0] == {"id": "0", "name": "Mic 1", "type": "input"}
        assert data[1] == {"id": "1", "name": "Speaker 1", "type": "output"}


def test_get_audio_devices_without_pyaudio():
    with patch.dict("sys.modules", {"pyaudio": None}):
        config = setup_mock_config()
        client = setup_app(config)

        response = client.get("/api/audio/devices")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0] == {"id": "default", "name": "Default Device", "type": "input"}


def test_set_audio_device_with_pyaudio_success():
    devices = [
        {"name": "Mic 1", "maxInputChannels": 2, "maxOutputChannels": 0},
    ]

    mock_pyaudio = MockPyAudio(devices)
    with patch.dict("sys.modules", {"pyaudio": mock_pyaudio}):
        config = setup_mock_config()
        client = setup_app(config)

        response = client.post(
            "/api/audio/device", json={"id": "0", "type": "input"}
        )
        assert response.status_code == 200
        assert response.json() == {"status": "success", "active_device": "0"}

        assert config.config_data["audio_settings"]["input_device"] == "0"
        config.save_config.assert_called_once()


def test_set_audio_device_with_pyaudio_not_found():
    devices = [
        {"name": "Mic 1", "maxInputChannels": 2, "maxOutputChannels": 0},
    ]

    mock_pyaudio = MockPyAudio(devices)
    with patch.dict("sys.modules", {"pyaudio": mock_pyaudio}):
        config = setup_mock_config()
        client = setup_app(config)

        response = client.post(
            "/api/audio/device", json={"id": "99", "type": "input"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_set_audio_device_without_pyaudio_default():
    with patch.dict("sys.modules", {"pyaudio": None}):
        config = setup_mock_config()
        client = setup_app(config)

        response = client.post(
            "/api/audio/device", json={"id": "default", "type": "output"}
        )
        assert response.status_code == 200
        assert response.json() == {"status": "success", "active_device": "default"}

        assert config.config_data["audio_settings"]["output_device"] == "default"
        config.save_config.assert_called_once()


def test_set_audio_device_missing_id():
    config = setup_mock_config()
    client = setup_app(config)

    response = client.post("/api/audio/device", json={"type": "input"})
    assert response.status_code == 400
    assert "required" in response.json()["detail"].lower()
