with open("tests/test_system_routes.py", "r") as f:
    content = f.read()

# Replace entire test_system_info
import re
content = re.sub(
    r'def test_system_info\(client\):.*?def test_system_info_psutil_missing',
    '''def test_system_info(client):
    with patch("time.time", return_value=1100.0), \\
         patch("psutil.cpu_percent", return_value=25.0), \\
         patch("psutil.virtual_memory") as mock_mem:
        mock_mem.return_value.percent = 40.0
        response = client.get("/api/system/info")
        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert "cpu_percent" in data
        assert "platform" in data

def test_system_info_psutil_missing''',
    content,
    flags=re.DOTALL
)

with open("tests/test_system_routes.py", "w") as f:
    f.write(content)
