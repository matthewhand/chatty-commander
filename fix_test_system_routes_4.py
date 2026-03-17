with open("tests/test_system_routes.py", "r") as f:
    content = f.read()

content = content.replace('def test_system_info(client):\n    with patch("time.time", return_value=1100.0), \\\n         patch("psutil.cpu_percent", return_value=25.0), \\\n         patch("psutil.virtual_memory") as mock_mem:\n        mock_mem.return_value.percent = 40.0\n        response = client.get("/api/system/info")\n        assert response.status_code == 200\n        data = response.json()\n        assert "cpu" in data or "cpu_percent" in data\n        assert "memory" in data or "memory_percent" in data', 'def test_system_info(client):\n    with patch("time.time", return_value=1100.0), \\\n         patch("psutil.cpu_percent", return_value=25.0), \\\n         patch("psutil.virtual_memory") as mock_mem:\n        mock_mem.return_value.percent = 40.0\n        response = client.get("/api/system/info")\n        assert response.status_code == 200\n        data = response.json()\n        assert "uptime_seconds" in data\n        assert data["cpu_percent"] == 25.0')

with open("tests/test_system_routes.py", "w") as f:
    f.write(content)
