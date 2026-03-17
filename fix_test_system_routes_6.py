with open("tests/test_system_routes.py", "r") as f:
    content = f.read()

content = content.replace('assert response.status_code == 200\n        data = response.json()\n        assert "uptime_seconds" in data\n        assert "cpu_percent" in data', 'assert response.status_code == 200\n        data = response.json()\n        assert "uptime_seconds" in data\n        assert "cpu_percent" in data\n        assert "platform" in data')

with open("tests/test_system_routes.py", "w") as f:
    f.write(content)
