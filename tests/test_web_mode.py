#!/usr/bin/env python3
"""
test_web_mode.py

Comprehensive test script for validating web mode functionality.
Tests FastAPI endpoints, WebSocket connections, and frontend integration.
"""

import asyncio
import json
import logging
import os
from unittest.mock import MagicMock, patch

import pytest
import requests
import websockets
from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.web.web_mode import WebModeServer
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DummyConfig(Config):
    def __init__(self):
        self.general_models_path = "models-idle"
        self.system_models_path = "models-computer"
        self.chat_models_path = "models-chatty"
        self.config = {"model_actions": {}}
        self.auth = {"enabled": True, "api_key": "secret", "allowed_origins": ["*"]}
        self.advisors = {"enabled": False}


def create_server(*, no_auth: bool) -> WebModeServer:
    with patch('chatty_commander.advisors.providers.build_provider_safe') as mock_build_provider:
        mock_provider = MagicMock()
        mock_provider.model = "test-model"
        mock_provider.api_mode = "completion"
        mock_build_provider.return_value = mock_provider
        cfg = DummyConfig()
        sm = StateManager()
        mm = ModelManager(cfg)
        ce = CommandExecutor(cfg, mm, sm)
        return WebModeServer(cfg, sm, mm, ce, no_auth=no_auth)


def test_status_authentication():
    server = create_server(no_auth=False)
    client = TestClient(server.app)

    resp = client.get("/api/v1/status")
    assert resp.status_code == 401

    resp = client.get("/api/v1/status", headers={"X-API-Key": "secret"})
    assert resp.status_code == 200


def test_status_no_auth():
    server = create_server(no_auth=True)
    client = TestClient(server.app)
    assert client.get("/api/v1/status").status_code == 200


def test_websocket_authentication():
    server = create_server(no_auth=False)
    client = TestClient(server.app)
    try:
        with client.websocket_connect("/ws") as ws:
            with pytest.raises(WebSocketDisconnect):
                ws.receive_json()
    except WebSocketDisconnect:
        pass
    with client.websocket_connect("/ws", headers={"X-API-Key": "secret"}) as ws:
        data = ws.receive_json()
        assert data["type"] == "connection_established"


class WebModeValidator:
    """Validates web mode functionality including API endpoints and WebSocket connections."""

    def __init__(self, base_url: str = "http://localhost:8100") -> None:
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws") + "/ws"
        self.session = requests.Session()
        self.test_results: dict[str, bool] = {}

    def test_server_health(self) -> bool:
        """Test if the server is running and responsive."""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/status", timeout=5)
            success = response.status_code == 200
            if success:
                logger.info("✅ Server health check passed")
            else:
                logger.error(f"❌ Server health check failed: {response.status_code}")
            return success
        except Exception as e:
            logger.error(f"❌ Server health check failed: {e}")
            return False

    def test_api_endpoints(self) -> bool:
        """Test all API endpoints for proper responses."""
        endpoints = [
            ("/api/v1/status", "GET"),
            ("/api/v1/config", "GET"),
            ("/api/v1/state", "GET"),
        ]

        all_passed = True
        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)

                if response.status_code == 200:
                    logger.info(f"✅ {method} {endpoint} - Status: {response.status_code}")
                    # Validate JSON response
                    try:
                        data = response.json()
                        logger.info(
                            f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'Non-dict response'}"
                        )
                    except json.JSONDecodeError:
                        logger.warning(f"   Non-JSON response for {endpoint}")
                else:
                    logger.error(f"❌ {method} {endpoint} - Status: {response.status_code}")
                    all_passed = False

            except Exception as e:
                logger.error(f"❌ {method} {endpoint} - Error: {e}")
                all_passed = False

        return all_passed

    def test_command_endpoint(self) -> bool:
        """Test the command execution endpoint."""
        try:
            # Test with a safe command
            test_command = {"command": "test_command"}
            response = self.session.post(
                f"{self.base_url}/api/v1/command", json=test_command, timeout=5
            )

            # We expect this to fail gracefully since test_command doesn't exist
            if response.status_code in [400, 404, 422]:  # Expected error codes
                logger.info(
                    f"✅ POST /api/v1/command - Proper error handling: {response.status_code}"
                )
                return True
            elif response.status_code == 200:
                logger.info(f"✅ POST /api/v1/command - Success: {response.status_code}")
                return True
            else:
                logger.error(f"❌ POST /api/v1/command - Unexpected status: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ POST /api/v1/command - Error: {e}")
            return False

    async def test_websocket_connection(self) -> bool:
        """Test WebSocket connection and message handling."""
        try:
            async with websockets.connect(self.ws_url) as websocket:
                logger.info("✅ WebSocket connection established")

                # Send a test message
                test_message = {"type": "ping", "data": "test"}
                await websocket.send(json.dumps(test_message))
                logger.info("✅ WebSocket message sent")

                # Try to receive a response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    logger.info(f"✅ WebSocket response received: {response[:100]}...")
                except TimeoutError:
                    logger.info("✅ WebSocket connection stable (no immediate response expected)")

                return True

        except Exception as e:
            logger.error(f"❌ WebSocket test failed: {e}")
            return False

    def test_static_files(self) -> bool:
        """Test that static files are served correctly."""
        try:
            # Test main index.html
            response = self.session.get(f"{self.base_url}/", timeout=5)
            if (
                response.status_code == 200
                and "html" in response.headers.get("content-type", "").lower()
            ):
                logger.info("✅ Static file serving - index.html")
                return True
            else:
                logger.error(f"❌ Static file serving failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Static file test failed: {e}")
            return False

    def test_cors_headers(self) -> bool:
        """Test CORS headers for frontend compatibility."""
        try:
            response = self.session.options(f"{self.base_url}/api/v1/status")
            cors_headers = {
                "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                "access-control-allow-methods": response.headers.get(
                    "access-control-allow-methods"
                ),
                "access-control-allow-headers": response.headers.get(
                    "access-control-allow-headers"
                ),
            }

            if any(cors_headers.values()):
                logger.info("✅ CORS headers present")
                for header, value in cors_headers.items():
                    if value:
                        logger.info(f"   {header}: {value}")
                return True
            else:
                logger.warning("⚠️  No CORS headers found (may cause frontend issues)")
                return False

        except Exception as e:
            logger.error(f"❌ CORS test failed: {e}")
            return False

    async def run_all_tests(self) -> dict[str, bool]:
        """Run all web mode tests and return results."""
        logger.info("🚀 Starting Web Mode Validation Tests")
        logger.info(f"Testing server at: {self.base_url}")

        # Basic connectivity
        self.test_results["server_health"] = self.test_server_health()

        if not self.test_results["server_health"]:
            logger.error("❌ Server not accessible. Skipping remaining tests.")
            return self.test_results

        # API tests
        self.test_results["api_endpoints"] = self.test_api_endpoints()
        self.test_results["command_endpoint"] = self.test_command_endpoint()

        # WebSocket tests
        self.test_results["websocket"] = await self.test_websocket_connection()

        # Frontend tests
        self.test_results["static_files"] = self.test_static_files()
        self.test_results["cors_headers"] = self.test_cors_headers()

        return self.test_results

    def print_summary(self) -> None:
        """Print a summary of test results."""
        logger.info("\n📊 Web Mode Test Summary:")
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)

        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"   {test_name}: {status}")

        logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")

        if passed == total:
            logger.info("🎉 All web mode tests passed! The application is ready for use.")
        else:
            logger.warning(f"⚠️  {total - passed} test(s) failed. Please check the logs above.")


async def main():
    """Main test execution function."""
    validator = WebModeValidator()

    # Wait a moment for server to be ready
    logger.info("Waiting 2 seconds for server to be ready...")
    await asyncio.sleep(2)

    results = await validator.run_all_tests()
    validator.print_summary()

    # Return exit code based on results
    all_passed = all(results.values())
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
