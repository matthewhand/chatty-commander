# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Tests for test runner with coverage module.

Tests TestRunner class functionality.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.tools.run_tests_with_coverage import TestRunner


class TestTestRunnerInitialization:
    """Tests for TestRunner initialization."""

    def test_default_initialization(self):
        """Test initialization with default project root."""
        runner = TestRunner()
        assert runner.project_root == Path.cwd()
        assert runner.test_results == []

    def test_custom_project_root(self):
        """Test initialization with custom project root."""
        custom_path = "/tmp/test_project"
        runner = TestRunner(custom_path)
        assert runner.project_root == Path(custom_path)

    def test_initializes_results_list(self):
        """Test that test_results is initialized as empty list."""
        runner = TestRunner()
        assert isinstance(runner.test_results, list)
        assert len(runner.test_results) == 0


class TestRunCommand:
    """Tests for run_command method."""

    @pytest.fixture
    def runner(self):
        """Create TestRunner instance."""
        return TestRunner()

    def test_successful_command(self, runner):
        """Test running a successful command."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="success output",
                stderr=""
            )
            
            success, output = runner.run_command(
                ["echo", "test"],
                "Test command"
            )
            
            assert success is True
            assert "success output" in output

    def test_failed_command(self, runner):
        """Test running a failed command."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="error message"
            )
            
            success, output = runner.run_command(
                ["false"],
                "Failing command"
            )
            
            assert success is False
            assert "error message" in output

    def test_command_timeout(self, runner):
        """Test handling of command timeout."""
        import subprocess
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 60)
            
            success, output = runner.run_command(
                ["sleep", "100"],
                "Slow command",
                timeout=1
            )
            
            assert success is False
            assert "timed out" in output.lower() or "TIMEOUT" in output

    def test_command_exception(self, runner):
        """Test handling of command execution exception."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Command not found")
            
            success, output = runner.run_command(
                ["invalid_command"],
                "Invalid command"
            )
            
            assert success is False
            assert "Command not found" in output

    def test_custom_cwd(self, runner):
        """Test running command with custom working directory."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            custom_cwd = Path("/tmp")
            runner.run_command(
                ["pwd"],
                "Test pwd",
                cwd=custom_cwd
            )
            
            call_args = mock_run.call_args
            assert call_args[1]["cwd"] == custom_cwd

    def test_custom_timeout(self, runner):
        """Test running command with custom timeout."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            runner.run_command(
                ["sleep", "1"],
                "Test sleep",
                timeout=30
            )
            
            call_args = mock_run.call_args
            assert call_args[1]["timeout"] == 30


class TestCheckDependencies:
    """Tests for check_dependencies method."""

    @pytest.fixture
    def runner(self):
        """Create TestRunner instance."""
        return TestRunner()

    def test_returns_true_when_uv_available(self, runner):
        """Test returns True when UV is available."""
        with patch.object(runner, "run_command") as mock_run:
            mock_run.return_value = (True, "uv 0.1.0")
            
            result = runner.check_dependencies()
            
            assert result is True

    def test_returns_false_when_uv_missing(self, runner):
        """Test returns False when UV is not available."""
        with patch.object(runner, "run_command") as mock_run:
            # First call (uv --version) fails
            mock_run.return_value = (False, "not found")
            
            result = runner.check_dependencies()
            
            assert result is False

    def test_installs_pytest_cov_if_missing(self, runner):
        """Test installs pytest-cov if not available."""
        with patch.object(runner, "run_command") as mock_run:
            # UV check passes, pytest-cov check fails, install succeeds
            mock_run.side_effect = [
                (True, "uv 0.1.0"),      # UV check
                (False, "not found"),     # pytest-cov check
                (True, "installed"),      # Install pytest-cov
            ]
            
            result = runner.check_dependencies()
            
            assert result is True
            # Should have called install
            assert mock_run.call_count == 3


class TestRunUnitTests:
    """Tests for run_unit_tests method."""

    @pytest.fixture
    def runner(self):
        """Create TestRunner instance."""
        return TestRunner()

    def test_runs_pytest_with_coverage(self, runner):
        """Test that pytest runs with coverage flags."""
        with patch.object(runner, "run_command") as mock_run:
            mock_run.return_value = (True, "test output")
            
            runner.run_unit_tests()
            
            call_args = mock_run.call_args
            command = call_args[0][0]
            
            assert "pytest" in command
            assert "--cov=." in command
            assert "--cov-report=term" in command
            assert "--cov-report=html:htmlcov" in command

    def test_accepts_extra_paths(self, runner):
        """Test that custom test paths can be provided."""
        with patch.object(runner, "run_command") as mock_run:
            mock_run.return_value = (True, "test output")
            
            runner.run_unit_tests(extra_paths=["tests/test_specific.py"])
            
            call_args = mock_run.call_args
            command = call_args[0][0]
            
            assert "tests/test_specific.py" in command

    def test_records_test_results(self, runner):
        """Test that test results are recorded."""
        with patch.object(runner, "run_command") as mock_run:
            mock_run.return_value = (True, "passed")
            
            runner.run_unit_tests()
            
            assert len(runner.test_results) == 1
            assert runner.test_results[0][0] == "Unit Tests"
            assert runner.test_results[0][1] is True

    def test_returns_success_status(self, runner):
        """Test that method returns success boolean."""
        with patch.object(runner, "run_command") as mock_run:
            mock_run.return_value = (True, "passed")
            
            result = runner.run_unit_tests()
            
            assert result is True


class TestRunIntegrationTests:
    """Tests for run_integration_tests method."""

    @pytest.fixture
    def runner(self):
        """Create TestRunner instance."""
        return TestRunner()

    def test_skips_missing_files(self, runner):
        """Test that missing integration files are skipped."""
        with patch.object(runner, "run_command") as mock_run:
            # Mock the Path.exists to return False
            with patch.object(Path, "exists", return_value=False):
                runner.run_integration_tests()
                
                # Should not attempt to run any tests
                mock_run.assert_not_called()

    def test_records_results_for_each_file(self, runner):
        """Test that results are recorded for each test file."""
        with patch.object(runner, "run_command") as mock_run:
            mock_run.return_value = (True, "passed")
            
            # Mock Path.exists to return True for test files
            def mock_exists(self):
                return "test_integration" in str(self) or "test_performance" in str(self)
            
            with patch.object(Path, "exists", mock_exists):
                runner.run_integration_tests()
                
                # Should have recorded results
                assert len(runner.test_results) > 0


class TestStartWebServer:
    """Tests for start_web_server method."""

    @pytest.fixture
    def runner(self):
        """Create TestRunner instance."""
        return TestRunner()

    def test_returns_process_on_success(self, runner):
        """Test that process is returned on successful start."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Still running
        
        with patch("subprocess.Popen") as mock_popen:
            with patch("time.sleep"):  # Skip the sleep
                mock_popen.return_value = mock_process
                
                result = runner.start_web_server()
                
                assert result is mock_process

    def test_returns_none_on_failure(self, runner):
        """Test that None is returned if server fails to start."""
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Already exited with error
        
        with patch("subprocess.Popen") as mock_popen:
            with patch("time.sleep"):
                mock_popen.return_value = mock_process
                
                result = runner.start_web_server()
                
                assert result is None

    def test_uses_correct_command(self, runner):
        """Test that correct command is used to start server."""
        mock_process = Mock()
        mock_process.poll.return_value = None
        
        with patch("subprocess.Popen") as mock_popen:
            with patch("time.sleep"):
                mock_popen.return_value = mock_process
                
                runner.start_web_server()
                
                call_args = mock_popen.call_args
                command = call_args[0][0]
                
                assert "uv" in command
                assert "python" in command
                assert "main.py" in command
                assert "--web" in command
                assert "--no-auth" in command


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_command_list(self):
        """Test handling of empty command list."""
        runner = TestRunner()
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            success, output = runner.run_command([], "Empty command")
            
            # Should still work
            assert success is True

    def test_long_output_truncation(self):
        """Test that long output is truncated in logs."""
        runner = TestRunner()
        
        long_output = "x" * 1000
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout=long_output,
                stderr=""
            )
            
            # Just verify it doesn't crash with long output
            success, output = runner.run_command(
                ["echo", "test"],
                "Test with long output"
            )
            
            assert success is False  # Because returncode was 1

    def test_none_project_root(self):
        """Test handling of None project root."""
        runner = TestRunner(None)
        
        # Should default to cwd
        assert runner.project_root == Path.cwd()
