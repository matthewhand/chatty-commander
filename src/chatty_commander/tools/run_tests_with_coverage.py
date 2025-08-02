#!/usr/bin/env python3
"""
run_tests_with_coverage.py

Comprehensive test runner with coverage reporting for ChattyCommander.
Runs all tests including unit tests, integration tests, and web mode validation.
"""

import logging
import subprocess
import sys
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestRunner:
    """Comprehensive test runner with coverage reporting."""

    def __init__(self, project_root: str | None = None) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.test_results: list[tuple[str, bool, str]] = []

    def run_command(
        self, command: list[str], description: str, cwd: Path | None = None
    ) -> tuple[bool, str]:
        """Run a command and return success status and output."""
        try:
            logger.info(f"🔄 Running: {description}")
            logger.debug(f"Command: {' '.join(command)}")

            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            success = result.returncode == 0
            output = result.stdout + result.stderr

            if success:
                logger.info(f"✅ {description} - PASSED")
            else:
                logger.error(f"❌ {description} - FAILED (exit code: {result.returncode})")
                logger.error(f"Output: {output[-500:]}...")  # Last 500 chars

            return success, output

        except subprocess.TimeoutExpired:
            logger.error(f"❌ {description} - TIMEOUT")
            return False, "Test timed out after 5 minutes"
        except Exception as e:
            logger.error(f"❌ {description} - ERROR: {e}")
            return False, str(e)

    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed."""
        logger.info("🔍 Checking dependencies...")

        # Check if uv is available
        success, _ = self.run_command(["uv", "--version"], "UV package manager check")
        if not success:
            logger.error("❌ UV package manager not found. Please install uv first.")
            return False

        # Check if pytest-cov is installed
        success, _ = self.run_command(
            ["uv", "run", "python", "-c", "import pytest_cov"], "pytest-cov availability"
        )
        if not success:
            logger.warning("⚠️  pytest-cov not found. Installing...")
            install_success, _ = self.run_command(["uv", "add", "pytest-cov"], "Install pytest-cov")
            if not install_success:
                logger.error("❌ Failed to install pytest-cov")
                return False

        return True

    def run_unit_tests(self) -> bool:
        """Run unit tests with coverage."""
        command = [
            "uv",
            "run",
            "pytest",
            "tests/",
            "--cov=.",
            "--cov-report=term",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            "--cache-clear",
            "-v",
        ]

        success, output = self.run_command(command, "Unit tests with coverage")
        self.test_results.append(("Unit Tests", success, output))
        return success

    def run_integration_tests(self) -> bool:
        """Run integration tests separately."""
        integration_files = ["tests/test_integration_voice.py", "tests/test_performance.py"]

        all_success = True
        for test_file in integration_files:
            if (self.project_root / test_file).exists():
                command = ["uv", "run", "pytest", test_file, "-v"]
                success, output = self.run_command(command, f"Integration test: {test_file}")
                self.test_results.append((f"Integration: {test_file}", success, output))
                all_success = all_success and success

        return all_success

    def start_web_server(self) -> subprocess.Popen | None:
        """Start the web server for testing."""
        try:
            logger.info("🚀 Starting web server for testing...")
            process = subprocess.Popen(
                ["uv", "run", "python", "main.py", "--web", "--no-auth"],
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for server to start
            time.sleep(3)

            if process.poll() is None:  # Process is still running
                logger.info("✅ Web server started successfully")
                return process
            else:
                logger.error("❌ Web server failed to start")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to start web server: {e}")
            return None

    def run_web_mode_tests(self) -> bool:
        """Run web mode validation tests."""
        # Start web server
        server_process = self.start_web_server()
        if not server_process:
            self.test_results.append(("Web Mode Tests", False, "Failed to start web server"))
            return False

        try:
            # Run web mode tests
            command = ["uv", "run", "python", "test_web_mode.py"]
            success, output = self.run_command(command, "Web mode validation tests")
            self.test_results.append(("Web Mode Tests", success, output))
            return success

        finally:
            # Clean up server process
            if server_process:
                logger.info("🛑 Stopping web server...")
                server_process.terminate()
                try:
                    server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_process.kill()
                    server_process.wait()

    def run_linting(self) -> bool:
        """Run code quality checks."""
        # Check if flake8 is available
        try:
            command = ["uv", "run", "python", "-c", "import flake8"]
            success, _ = self.run_command(command, "Check flake8 availability")

            if success:
                # Run flake8 linting
                command = [
                    "uv",
                    "run",
                    "flake8",
                    ".",
                    "--max-line-length=120",
                    "--exclude=archive,webui/frontend",
                ]
                success, output = self.run_command(command, "Code linting (flake8)")
                self.test_results.append(("Code Linting", success, output))
                return success
            else:
                logger.info("ℹ️  Flake8 not available, skipping linting")
                return True

        except Exception as e:
            logger.warning(f"⚠️  Linting check failed: {e}")
            return True  # Don't fail the entire test suite for linting

    def generate_coverage_report(self) -> None:
        """Generate and display coverage summary."""
        coverage_file = self.project_root / "htmlcov" / "index.html"
        if coverage_file.exists():
            logger.info(f"📊 Coverage report generated: {coverage_file}")
            logger.info("   Open the HTML file in a browser to view detailed coverage")

        # Try to show coverage summary
        try:
            command = ["uv", "run", "coverage", "report", "--show-missing"]
            success, output = self.run_command(command, "Coverage summary")
            if success:
                logger.info("📈 Coverage Summary:")
                for line in output.split('\n')[-10:]:  # Last 10 lines
                    if line.strip():
                        logger.info(f"   {line}")
        except Exception:
            logger.info("ℹ️  Coverage summary not available")

    def print_final_summary(self) -> bool:
        """Print final test summary and return overall success."""
        logger.info("\n" + "=" * 60)
        logger.info("📊 COMPREHENSIVE TEST SUMMARY")
        logger.info("=" * 60)

        passed = 0
        total = len(self.test_results)

        for test_name, success, _ in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            logger.info(f"   {test_name:<25} {status}")
            if success:
                passed += 1

        logger.info(f"\n🎯 Overall Result: {passed}/{total} test suites passed")

        if passed == total:
            logger.info("🎉 ALL TESTS PASSED! The application is ready for production.")
            return True
        else:
            logger.warning(
                f"⚠️  {total - passed} test suite(s) failed. Please review the logs above."
            )
            return False

    def run_all_tests(self) -> bool:
        """Run the complete test suite."""
        logger.info("🚀 Starting Comprehensive Test Suite")
        logger.info(f"Project root: {self.project_root}")

        # Check dependencies
        if not self.check_dependencies():
            return False

        # Run all test categories
        self.run_unit_tests()
        self.run_integration_tests()
        self.run_web_mode_tests()
        self.run_linting()

        # Generate reports
        self.generate_coverage_report()

        # Final summary
        return self.print_final_summary()


def main():
    """Main execution function."""
    runner = TestRunner()
    success = runner.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
