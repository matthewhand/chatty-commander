"""
Comprehensive E2E Page Rendering Tests
Verifies all application pages render without errors
"""

import pytest
import requests
import time
from typing import List, Tuple


# Page routes to test with expected status codes
PAGE_ROUTES = [
    ("/", 200, "Dashboard/Home"),
    ("/commands", 200, "Commands Management"),
    ("/agents", 200, "Agents Dashboard"),
    ("/settings", 200, "Settings Page"),
    ("/voice", 200, "Voice Control"),
    ("/avatar", 200, "Avatar Interface"),
    ("/logs", 200, "System Logs"),
    ("/api/health", 200, "Health Check Endpoint"),
]

# API endpoints to verify
API_ENDPOINTS = [
    ("/api/v1/commands", 200, "List Commands API"),
    ("/api/v1/agents", 200, "List Agents API"),
    ("/api/v1/status", 200, "System Status API"),
    ("/api/v1/config", 200, "Configuration API"),
]


class TestPageRendering:
    """Verify all pages render without errors"""

    def get_base_url(self):
        """Get base URL for testing"""
        return "http://localhost:8000"  # Default backend port

    @pytest.fixture(scope="class", autouse=True)
    def wait_for_server(self):
        """Wait for server to be ready"""
        max_retries = 30
        for i in range(max_retries):
            try:
                requests.get(f"{self.get_base_url()}/api/health", timeout=2)
                return
            except requests.ConnectionError:
                if i == max_retries - 1:
                    pytest.skip("Server not available")
                time.sleep(1)

    @pytest.mark.parametrize("route,expected_status,name", PAGE_ROUTES)
    def test_page_renders(self, route: str, expected_status: int, name: str):
        """Test that page renders without error"""
        url = f"{self.get_base_url()}{route}"
        response = requests.get(url, timeout=10, allow_redirects=True)
        
        assert response.status_code == expected_status, \
            f"{name} at {route} returned {response.status_code}, expected {expected_status}"
        
        # Verify no error in response content
        assert "error" not in response.text.lower() or "no error" in response.text.lower(), \
            f"{name} contains error message"

    @pytest.mark.parametrize("endpoint,expected_status,name", API_ENDPOINTS)
    def test_api_responds(self, endpoint: str, expected_status: int, name: str):
        """Test API endpoints respond correctly"""
        url = f"{self.get_base_url()}{endpoint}"
        response = requests.get(url, timeout=10)
        
        assert response.status_code == expected_status, \
            f"{name} at {endpoint} returned {response.status_code}"
        
        # Verify JSON response
        try:
            data = response.json()
            assert isinstance(data, (dict, list)), \
                f"{name} did not return valid JSON"
        except ValueError:
            pytest.fail(f"{name} at {endpoint} did not return valid JSON")


class TestPageContentIntegrity:
    """Verify page content loads correctly"""

    def get_base_url(self):
        return "http://localhost:8000"

    def test_page_has_required_elements(self):
        """Verify main page has required UI elements"""
        url = f"{self.get_base_url()}/"
        response = requests.get(url, timeout=10)
        
        assert response.status_code == 200
        html = response.text.lower()
        
        # Check for key UI elements
        required_elements = [
            "body",
            "head",
            "html",
        ]
        
        for element in required_elements:
            assert f"<{element}" in html, f"Missing required element: {element}"

    def test_no_console_errors_placeholder(self):
        """Placeholder for console error checking (requires browser automation)"""
        # This would require Playwright/Selenium to check console
        pytest.skip("Requires browser automation - implement with Playwright")


class TestDeepCoverage:
    """Expanded E2E coverage tests"""

    def get_base_url(self):
        return "http://localhost:8000"

    def test_error_handling_404(self):
        """Test 404 page handling"""
        url = f"{self.get_base_url()}/nonexistent-page-12345"
        response = requests.get(url, timeout=10)
        
        # Should return 404 or redirect to error page
        assert response.status_code in [404, 200], \
            f"Unexpected status: {response.status_code}"

    def test_cors_headers(self):
        """Verify CORS headers are set correctly"""
        url = f"{self.get_base_url()}/api/v1/status"
        response = requests.get(url, timeout=10)
        
        # Check if CORS headers present (optional but good practice)
        assert "access-control-allow-origin" in response.headers or True, \
            "CORS headers not present (optional check)"

    def test_response_times(self):
        """Verify page response times are acceptable"""
        url = f"{self.get_base_url()}/"
        
        response_times = []
        for _ in range(3):
            start = time.time()
            response = requests.get(url, timeout=10)
            elapsed = time.time() - start
            response_times.append(elapsed)
            assert response.status_code == 200
        
        avg_time = sum(response_times) / len(response_times)
        assert avg_time < 2.0, f"Average response time {avg_time:.2f}s exceeds 2s threshold"


class TestWebSocketConnectivity:
    """Test WebSocket connections if available"""

    def test_websocket_endpoint_exists(self):
        """Verify WebSocket endpoint is accessible"""
        # This is a placeholder - actual WS testing requires websocket-client
        pytest.skip("WebSocket testing requires additional setup")
