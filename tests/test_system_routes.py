import importlib
import re
import sys
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatty_commander.web.routes.system import include_system_routes
from chatty_commander.web.web_mode import create_app

# Create a minimal app to mount the router
app = FastAPI()
router = include_system_routes(get_start_time=lambda: 1000.0)
app.include_router(router)
client = TestClient(app)


class MockMemory:
    def __init__(self):
        self.total = 16 * 1024 * 1024 * 1024  # 16 GB
        self.used = 8 * 1024 * 1024 * 1024  # 8 GB
        self.percent = 50.0


class MockDisk:
    def __init__(self):
        self.total = 500 * 1024 * 1024 * 1024  # 500 GB
        self.used = 250 * 1024 * 1024 * 1024  # 250 GB
        self.percent = 50.0


@patch("time.time", return_value=1100.0)
@patch("platform.platform", return_value="TestPlatform-1.0")
@patch("psutil.cpu_percent", return_value=25.5)
@patch("psutil.virtual_memory", return_value=MockMemory())
@patch("psutil.disk_usage", return_value=MockDisk())
def test_system_info_with_psutil(
    mock_disk, mock_mem, mock_cpu, mock_platform, mock_time
):
    # Ensure psutil is 'available' by letting imports succeed
    response = client.get("/api/system/info")
    assert response.status_code == 200
    data = response.json()

    assert data["python_version"] == sys.version.split(" ")[0]
    assert data["platform"] == "TestPlatform-1.0"
    assert data["uptime_seconds"] == 100.0

    # Check psutil fields
    assert data["cpu_percent"] == 25.5
    assert data["memory_total_mb"] == 16 * 1024
    assert data["memory_used_mb"] == 8 * 1024
    assert data["memory_percent"] == 50.0
    assert data["disk_total_gb"] == 500.0
    assert data["disk_used_gb"] == 250.0
    assert data["disk_percent"] == 50.0


@patch("time.time", return_value=1100.0)
@patch("platform.platform", return_value="TestPlatform-1.0")
def test_system_info_without_psutil(mock_platform, mock_time):
    # We mock __import__ to raise ImportError when 'psutil' is imported
    original_import = __import__

    def mock_import(name, *args, **kwargs):
        if name == "psutil":
            raise ImportError("No module named 'psutil'")
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        response = client.get("/api/system/info")

    assert response.status_code == 200
    data = response.json()

    # Basic info should still be present
    assert data["python_version"] == sys.version.split(" ")[0]
    assert data["platform"] == "TestPlatform-1.0"
    assert data["uptime_seconds"] == 100.0

    # psutil fields should be None
    assert data["cpu_percent"] is None
    assert data["memory_total_mb"] is None
    assert data["memory_used_mb"] is None
    assert data["memory_percent"] is None
    assert data["disk_total_gb"] is None
    assert data["disk_used_gb"] is None
    assert data["disk_percent"] is None


def test_version_endpoint_ok():
    version_app = create_app(no_auth=True)
    version_client = TestClient(version_app)

    resp = version_client.get("/api/v1/version")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert data.get("version") == "0.2.0"
    # git_sha may be None if git is unavailable in the environment
    assert "git_sha" in data
    assert (data["git_sha"] is None) or isinstance(data["git_sha"], str)


def test_version_importable():
    mod = importlib.import_module("chatty_commander")
    assert hasattr(mod, "__version__")
    assert re.match(r"^\d+\.\d+\.\d+.*|0\.0\.0\+dev$", mod.__version__)


def test_cli_alias_exists():
    cli = importlib.import_module("chatty_commander.cli.cli")
    assert hasattr(cli, "main") or hasattr(cli, "cli_main")
