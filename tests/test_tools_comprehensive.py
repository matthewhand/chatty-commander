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
Comprehensive tests for tools module functionality.
Tests bridge_nodejs, browser_analyst, builder, cli, fs_ops, generate_api_docs,
run_tests_with_coverage, validate_config, and workflow utilities.
"""

from unittest.mock import Mock, mock_open, patch

import pytest

from chatty_commander.tools.bridge_nodejs import NodeJSBridge
from chatty_commander.tools.browser_analyst import BrowserAnalyst
from chatty_commander.tools.builder import ProjectBuilder
from chatty_commander.tools.cli import CLITool
from chatty_commander.tools.fs_ops import FileSystemOps
from chatty_commander.tools.generate_api_docs import APIDocsGenerator
from chatty_commander.tools.run_tests_with_coverage import CoverageRunner
from chatty_commander.tools.validate_config import ConfigValidator
from chatty_commander.tools.workflow import WorkflowManager


class TestNodeJSBridge:
    """Test NodeJS bridge functionality."""

    def test_nodejs_bridge_initialization(self):
        """Test NodeJS bridge initialization."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = Mock()
            mock_popen.return_value = mock_process

            bridge = NodeJSBridge()
            assert bridge.process is not None
            mock_popen.assert_called_once()

    def test_nodejs_bridge_communication(self):
        """Test NodeJS bridge communication."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = Mock()
            mock_process.communicate.return_value = (b'{"result": "success"}', b"")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            bridge = NodeJSBridge()
            result = bridge.send_message({"action": "test"})

            assert result == {"result": "success"}
            mock_process.communicate.assert_called_once()

    def test_nodejs_bridge_error_handling(self):
        """Test NodeJS bridge error handling."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = Mock()
            mock_process.communicate.return_value = (b"", b"Error occurred")
            mock_process.returncode = 1
            mock_popen.return_value = mock_process

            bridge = NodeJSBridge()

            with pytest.raises(Exception):
                bridge.send_message({"action": "error_test"})


class TestBrowserAnalyst:
    """Test browser analyst functionality."""

    def test_browser_analyst_initialization(self):
        """Test browser analyst initialization."""
        analyst = BrowserAnalyst()
        assert analyst is not None

    def test_browser_analysis_workflow(self):
        """Test browser analysis workflow."""
        analyst = BrowserAnalyst()

        with patch.object(analyst, "_launch_browser") as mock_launch:
            with patch.object(analyst, "_analyze_page") as mock_analyze:
                mock_launch.return_value = True
                mock_analyze.return_value = {"analysis": "complete"}

                result = analyst.analyze_url("https://example.com")
                assert result == {"analysis": "complete"}

    def test_browser_error_handling(self):
        """Test browser error handling."""
        analyst = BrowserAnalyst()

        with patch.object(
            analyst, "_launch_browser", side_effect=Exception("Browser failed")
        ):
            with pytest.raises(Exception):
                analyst.analyze_url("https://example.com")


class TestProjectBuilder:
    """Test project builder functionality."""

    def test_builder_initialization(self):
        """Test project builder initialization."""
        builder = ProjectBuilder()
        assert builder is not None

    def test_build_process(self):
        """Test build process execution."""
        builder = ProjectBuilder()

        with patch.object(builder, "_validate_requirements") as mock_validate:
            with patch.object(builder, "_install_dependencies") as mock_install:
                with patch.object(builder, "_run_build_commands") as mock_build:
                    mock_validate.return_value = True
                    mock_install.return_value = True
                    mock_build.return_value = True

                    result = builder.build_project(".")
                    assert result is True

    def test_build_validation_failure(self):
        """Test build validation failure."""
        builder = ProjectBuilder()

        with patch.object(builder, "_validate_requirements", return_value=False):
            result = builder.build_project(".")
            assert result is False


class TestCLITool:
    """Test CLI tool functionality."""

    def test_cli_initialization(self):
        """Test CLI tool initialization."""
        cli_tool = CLITool()
        assert cli_tool is not None

    def test_command_execution(self):
        """Test CLI command execution."""
        cli_tool = CLITool()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Success")

            result = cli_tool.execute_command(["echo", "test"])
            assert result.returncode == 0

    def test_command_with_error(self):
        """Test CLI command with error."""
        cli_tool = CLITool()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stderr="Error occurred")

            result = cli_tool.execute_command(["false"])
            assert result.returncode == 1


class TestFileSystemOps:
    """Test file system operations."""

    def test_file_system_initialization(self):
        """Test file system operations initialization."""
        fs_ops = FileSystemOps()
        assert fs_ops is not None

    def test_file_operations(self):
        """Test basic file operations."""
        fs_ops = FileSystemOps()

        with patch("builtins.open", mock_open(read_data="test content")) as mock_file:
            with patch("os.path.exists", return_value=True):
                result = fs_ops.read_file("test.txt")
                assert result == "test content"

    def test_directory_operations(self):
        """Test directory operations."""
        fs_ops = FileSystemOps()

        with patch("os.makedirs") as mock_makedirs:
            with patch("os.path.exists", return_value=False):
                fs_ops.ensure_directory("test_dir")
                mock_makedirs.assert_called_once_with("test_dir", exist_ok=True)


class TestAPIDocsGenerator:
    """Test API documentation generator."""

    def test_api_docs_initialization(self):
        """Test API docs generator initialization."""
        docs_gen = APIDocsGenerator()
        assert docs_gen is not None

    def test_api_extraction(self):
        """Test API extraction from source."""
        docs_gen = APIDocsGenerator()

        with patch.object(docs_gen, "_parse_python_file") as mock_parse:
            mock_parse.return_value = [{"endpoint": "/api/test", "method": "GET"}]

            result = docs_gen.generate_docs("src/chatty_commander")
            assert len(result) > 0


class TestCoverageRunner:
    """Test coverage runner functionality."""

    def test_coverage_runner_initialization(self):
        """Test coverage runner initialization."""
        runner = CoverageRunner()
        assert runner is not None

    def test_coverage_execution(self):
        """Test coverage execution."""
        runner = CoverageRunner()

        with patch.object(runner, "_run_with_coverage") as mock_run:
            mock_run.return_value = {"coverage": 85.5}

            result = runner.run_coverage_analysis("tests/")
            assert result["coverage"] == 85.5


class TestConfigValidator:
    """Test configuration validator."""

    def test_config_validator_initialization(self):
        """Test config validator initialization."""
        validator = ConfigValidator()
        assert validator is not None

    def test_config_validation(self):
        """Test configuration validation."""
        validator = ConfigValidator()

        valid_config = {
            "app_name": "test_app",
            "version": "1.0.0",
            "settings": {"debug": True, "port": 8000},
        }

        with patch.object(validator, "_validate_schema") as mock_validate:
            mock_validate.return_value = True

            result = validator.validate_config(valid_config)
            assert result is True


class TestWorkflowManager:
    """Test workflow manager functionality."""

    def test_workflow_manager_initialization(self):
        """Test workflow manager initialization."""
        workflow = WorkflowManager()
        assert workflow is not None

    def test_workflow_execution(self):
        """Test workflow execution."""
        workflow = WorkflowManager()

        with patch.object(workflow, "_execute_step") as mock_step:
            mock_step.return_value = {"status": "completed"}

            result = workflow.execute_workflow("test_workflow")
            assert result["status"] == "completed"

    def test_workflow_rollback(self):
        """Test workflow rollback."""
        workflow = WorkflowManager()

        with patch.object(workflow, "_rollback_step") as mock_rollback:
            mock_rollback.return_value = True

            result = workflow.rollback_workflow("test_workflow")
            assert result is True
