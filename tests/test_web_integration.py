#!/usr/bin/env python3
"""
test_web_integration.py

Comprehensive integration tests for ChattyCommander web mode.
Tests all API endpoints, WebSocket functionality, and frontend integration.
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

import requests
import websockets
from websockets.exceptions import ConnectionClosed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebIntegrationTester:
    """Comprehensive web mode integration tester."""
    
    def __init__(self, base_url: str = "http://localhost:8100", ws_url: str = "ws://localhost:8100/ws") -> None:
        self.base_url = base_url
        self.ws_url = ws_url
        self.server_process: Optional[subprocess.Popen] = None
        self.test_results: Dict[str, Any] = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "details": {}
        }
    
    def start_test_server(self, timeout: int = 30) -> bool:
        """Start the web server for testing."""
        try:
            logger.info("🚀 Starting test server...")
            
            # Start the server in web mode with no auth
            cmd = [sys.executable, "main.py", "--web", "--no-auth", "--port", "8100"]
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    response = requests.get(f"{self.base_url}/api/v1/health", timeout=2)
                    if response.status_code == 200:
                        logger.info("✅ Test server started successfully")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(1)
                    continue
            
            logger.error("❌ Failed to start test server within timeout")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error starting test server: {e}")
            return False
    
    def stop_test_server(self) -> None:
        """Stop the test server."""
        if self.server_process:
            logger.info("🛑 Stopping test server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.server_process.wait()
            logger.info("✅ Test server stopped")
    
    def test_health_endpoint(self) -> bool:
        """Test the health check endpoint."""
        try:
            logger.info("🔍 Testing health endpoint...")
            response = requests.get(f"{self.base_url}/api/v1/health")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["status", "timestamp", "uptime"]
                
                for field in required_fields:
                    if field not in data:
                        self.test_results["errors"].append(f"Health endpoint missing field: {field}")
                        return False
                
                if data["status"] != "healthy":
                    self.test_results["errors"].append(f"Health status not healthy: {data['status']}")
                    return False
                
                logger.info("✅ Health endpoint test passed")
                return True
            else:
                self.test_results["errors"].append(f"Health endpoint returned {response.status_code}")
                return False
                
        except Exception as e:
            self.test_results["errors"].append(f"Health endpoint test failed: {e}")
            return False
    
    def test_status_endpoint(self) -> bool:
        """Test the system status endpoint."""
        try:
            logger.info("🔍 Testing status endpoint...")
            response = requests.get(f"{self.base_url}/api/v1/status")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["status", "current_state", "active_models", "uptime", "version"]
                
                for field in required_fields:
                    if field not in data:
                        self.test_results["errors"].append(f"Status endpoint missing field: {field}")
                        return False
                
                if not isinstance(data["active_models"], list):
                    self.test_results["errors"].append("active_models should be a list")
                    return False
                
                logger.info("✅ Status endpoint test passed")
                self.test_results["details"]["status"] = data
                return True
            else:
                self.test_results["errors"].append(f"Status endpoint returned {response.status_code}")
                return False
                
        except Exception as e:
            self.test_results["errors"].append(f"Status endpoint test failed: {e}")
            return False
    
    def test_config_endpoints(self) -> bool:
        """Test configuration GET and PUT endpoints."""
        try:
            logger.info("🔍 Testing config endpoints...")
            
            # Test GET config
            response = requests.get(f"{self.base_url}/api/v1/config")
            if response.status_code != 200:
                self.test_results["errors"].append(f"Config GET returned {response.status_code}")
                return False
            
            original_config = response.json()
            
            # Test PUT config (update a non-critical setting)
            test_config = original_config.copy()
            test_config["test_field"] = "test_value"
            
            response = requests.put(
                f"{self.base_url}/api/v1/config",
                json=test_config,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info("✅ Config endpoints test passed")
                self.test_results["details"]["config"] = original_config
                return True
            else:
                self.test_results["errors"].append(f"Config PUT returned {response.status_code}")
                return False
                
        except Exception as e:
            self.test_results["errors"].append(f"Config endpoints test failed: {e}")
            return False
    
    def test_state_endpoints(self) -> bool:
        """Test state GET and POST endpoints."""
        try:
            logger.info("🔍 Testing state endpoints...")
            
            # Test GET state
            response = requests.get(f"{self.base_url}/api/v1/state")
            if response.status_code != 200:
                self.test_results["errors"].append(f"State GET returned {response.status_code}")
                return False
            
            state_data = response.json()
            required_fields = ["current_state", "active_models", "timestamp"]
            
            for field in required_fields:
                if field not in state_data:
                    self.test_results["errors"].append(f"State endpoint missing field: {field}")
                    return False
            
            original_state = state_data["current_state"]
            
            # Test POST state change
            valid_states = ["idle", "computer", "chatty"]
            test_state = "computer" if original_state != "computer" else "idle"
            
            response = requests.post(
                f"{self.base_url}/api/v1/state",
                json={"state": test_state},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                # Verify state changed
                time.sleep(1)  # Allow time for state change
                response = requests.get(f"{self.base_url}/api/v1/state")
                if response.status_code == 200:
                    new_state_data = response.json()
                    if new_state_data["current_state"] == test_state:
                        logger.info("✅ State endpoints test passed")
                        self.test_results["details"]["state"] = state_data
                        return True
                    else:
                        self.test_results["errors"].append("State change not reflected")
                        return False
            
            self.test_results["errors"].append(f"State POST returned {response.status_code}")
            return False
                
        except Exception as e:
            self.test_results["errors"].append(f"State endpoints test failed: {e}")
            return False
    
    def test_command_endpoint(self) -> bool:
        """Test command execution endpoint."""
        try:
            logger.info("🔍 Testing command endpoint...")
            
            # Test with a non-existent command (should return 404)
            response = requests.post(
                f"{self.base_url}/api/v1/command",
                json={"command": "non_existent_command"},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 404:
                self.test_results["errors"].append(f"Command endpoint should return 404 for invalid command, got {response.status_code}")
                return False
            
            # Test with valid command structure (even if command doesn't exist in config)
            response = requests.post(
                f"{self.base_url}/api/v1/command",
                json={"command": "test_command", "parameters": {"test": "value"}},
                headers={"Content-Type": "application/json"}
            )
            
            # Should return 404 for non-configured command
            if response.status_code == 404:
                logger.info("✅ Command endpoint test passed")
                return True
            else:
                self.test_results["errors"].append(f"Command endpoint unexpected response: {response.status_code}")
                return False
                
        except Exception as e:
            self.test_results["errors"].append(f"Command endpoint test failed: {e}")
            return False
    
    async def test_websocket_connection(self) -> bool:
        """Test WebSocket connection and messaging."""
        try:
            logger.info("🔍 Testing WebSocket connection...")
            
            async with websockets.connect(self.ws_url) as websocket:
                # Wait for connection established message
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if data.get("type") != "connection_established":
                        self.test_results["errors"].append(f"Expected connection_established, got {data.get('type')}")
                        return False
                    
                    # Test ping-pong
                    ping_message = json.dumps({"type": "ping"})
                    await websocket.send(ping_message)
                    
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    
                    if response_data.get("type") != "pong":
                        self.test_results["errors"].append(f"Expected pong response, got {response_data.get('type')}")
                        return False
                    
                    logger.info("✅ WebSocket connection test passed")
                    self.test_results["details"]["websocket"] = {
                        "connection_message": data,
                        "ping_pong": response_data
                    }
                    return True
                    
                except asyncio.TimeoutError:
                    self.test_results["errors"].append("WebSocket timeout waiting for messages")
                    return False
                    
        except Exception as e:
            self.test_results["errors"].append(f"WebSocket test failed: {e}")
            return False
    
    def test_cors_headers(self) -> bool:
        """Test CORS headers for web frontend compatibility."""
        try:
            logger.info("🔍 Testing CORS headers...")
            
            # Test preflight request
            response = requests.options(
                f"{self.base_url}/api/v1/status",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Content-Type"
                }
            )
            
            cors_headers = {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*"
            }
            
            for header, expected_value in cors_headers.items():
                if header not in response.headers:
                    self.test_results["errors"].append(f"Missing CORS header: {header}")
                    return False
            
            logger.info("✅ CORS headers test passed")
            return True
            
        except Exception as e:
            self.test_results["errors"].append(f"CORS headers test failed: {e}")
            return False
    
    def test_static_file_serving(self) -> bool:
        """Test static file serving for frontend."""
        try:
            logger.info("🔍 Testing static file serving...")
            
            # Test root endpoint
            response = requests.get(self.base_url)
            
            if response.status_code == 200:
                logger.info("✅ Static file serving test passed")
                return True
            else:
                self.test_results["errors"].append(f"Root endpoint returned {response.status_code}")
                return False
                
        except Exception as e:
            self.test_results["errors"].append(f"Static file serving test failed: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        logger.info("🧪 Starting comprehensive web integration tests...")
        
        # Start test server
        if not self.start_test_server():
            self.test_results["errors"].append("Failed to start test server")
            return self.test_results
        
        try:
            # Run all tests
            tests = [
                ("Health Endpoint", self.test_health_endpoint),
                ("Status Endpoint", self.test_status_endpoint),
                ("Config Endpoints", self.test_config_endpoints),
                ("State Endpoints", self.test_state_endpoints),
                ("Command Endpoint", self.test_command_endpoint),
                ("CORS Headers", self.test_cors_headers),
                ("Static File Serving", self.test_static_file_serving),
            ]
            
            for test_name, test_func in tests:
                try:
                    if test_func():
                        self.test_results["passed"] += 1
                        logger.info(f"✅ {test_name}: PASSED")
                    else:
                        self.test_results["failed"] += 1
                        logger.error(f"❌ {test_name}: FAILED")
                except Exception as e:
                    self.test_results["failed"] += 1
                    self.test_results["errors"].append(f"{test_name}: {e}")
                    logger.error(f"❌ {test_name}: ERROR - {e}")
            
            # Test WebSocket (async)
            try:
                if await self.test_websocket_connection():
                    self.test_results["passed"] += 1
                    logger.info("✅ WebSocket Connection: PASSED")
                else:
                    self.test_results["failed"] += 1
                    logger.error("❌ WebSocket Connection: FAILED")
            except Exception as e:
                self.test_results["failed"] += 1
                self.test_results["errors"].append(f"WebSocket Connection: {e}")
                logger.error(f"❌ WebSocket Connection: ERROR - {e}")
            
        finally:
            # Stop test server
            self.stop_test_server()
        
        return self.test_results
    
    def print_test_summary(self) -> None:
        """Print a comprehensive test summary."""
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("🧪 WEB INTEGRATION TEST SUMMARY")
        print("="*60)
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.test_results["errors"]:
            print("\n🚨 ERRORS:")
            for error in self.test_results["errors"]:
                print(f"  • {error}")
        
        if self.test_results["details"]:
            print("\n📋 TEST DETAILS:")
            for key, value in self.test_results["details"].items():
                print(f"  • {key}: {json.dumps(value, indent=2)[:100]}...")
        
        print("\n" + "="*60)
        
        if success_rate >= 80:
            print("🎉 Web integration tests mostly successful!")
        else:
            print("⚠️  Some web integration tests failed. Check errors above.")


async def main():
    """Main test execution function."""
    tester = WebIntegrationTester()
    results = await tester.run_all_tests()
    tester.print_test_summary()
    
    # Return appropriate exit code
    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)