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
Tests for workflow module.

Tests documentation generation orchestration.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.tools.workflow import generate_docs


class TestGenerateDocs:
    """Tests for generate_docs function."""

    def test_returns_dict(self):
        """Test that function returns a dictionary."""
        with patch("src.chatty_commander.tools.workflow.ensure_dir"):
            with patch("src.chatty_commander.tools.workflow.write_json"):
                with patch("src.chatty_commander.tools.workflow.write_text"):
                    result = generate_docs()
                    assert isinstance(result, dict)

    def test_returns_paths(self):
        """Test that function returns paths to generated files."""
        with patch("src.chatty_commander.tools.workflow.ensure_dir"):
            with patch("src.chatty_commander.tools.workflow.write_json"):
                with patch("src.chatty_commander.tools.workflow.write_text"):
                    result = generate_docs()
                    
                    assert "openapi" in result
                    assert "markdown" in result
                    assert "index" in result

    def test_paths_are_path_objects(self):
        """Test that returned paths are Path objects."""
        with patch("src.chatty_commander.tools.workflow.ensure_dir"):
            with patch("src.chatty_commander.tools.workflow.write_json"):
                with patch("src.chatty_commander.tools.workflow.write_text"):
                    result = generate_docs()
                    
                    assert isinstance(result["openapi"], Path)
                    assert isinstance(result["markdown"], Path)
                    assert isinstance(result["index"], Path)

    def test_creates_docs_directory(self):
        """Test that docs directory is created."""
        with patch("src.chatty_commander.tools.workflow.ensure_dir") as mock_ensure:
            with patch("src.chatty_commander.tools.workflow.write_json"):
                with patch("src.chatty_commander.tools.workflow.write_text"):
                    generate_docs()
                    
                    mock_ensure.assert_called_once()

    def test_writes_openapi_json(self):
        """Test that openapi.json is written."""
        with patch("src.chatty_commander.tools.workflow.ensure_dir"):
            with patch("src.chatty_commander.tools.workflow.write_json") as mock_write:
                with patch("src.chatty_commander.tools.workflow.write_text"):
                    generate_docs()
                    
                    # Should write openapi.json
                    call_args = mock_write.call_args_list
                    assert any("openapi.json" in str(call) for call in call_args)

    def test_writes_api_markdown(self):
        """Test that API.md is written."""
        with patch("src.chatty_commander.tools.workflow.ensure_dir"):
            with patch("src.chatty_commander.tools.workflow.write_json"):
                with patch("src.chatty_commander.tools.workflow.write_text") as mock_write:
                    generate_docs()
                    
                    # Should write API.md
                    call_args = mock_write.call_args_list
                    assert any("API.md" in str(call) for call in call_args)

    def test_writes_readme_index(self):
        """Test that README.md index is written."""
        with patch("src.chatty_commander.tools.workflow.ensure_dir"):
            with patch("src.chatty_commander.tools.workflow.write_json"):
                with patch("src.chatty_commander.tools.workflow.write_text") as mock_write:
                    generate_docs()
                    
                    # Should write README.md
                    call_args = mock_write.call_args_list
                    assert any("README.md" in str(call) for call in call_args)

    def test_accepts_custom_output_dir(self):
        """Test that custom output directory can be specified."""
        custom_dir = Path("/custom/docs")
        
        with patch("src.chatty_commander.tools.workflow.ensure_dir") as mock_ensure:
            with patch("src.chatty_commander.tools.workflow.write_json"):
                with patch("src.chatty_commander.tools.workflow.write_text"):
                    generate_docs(output_dir=custom_dir)
                    
                    # Should use custom directory
                    mock_ensure.assert_called_once_with(custom_dir)

    def test_uses_default_docs_dir(self):
        """Test that default docs directory is used."""
        with patch("src.chatty_commander.tools.workflow.ensure_dir") as mock_ensure:
            with patch("src.chatty_commander.tools.workflow.write_json"):
                with patch("src.chatty_commander.tools.workflow.write_text"):
                    generate_docs()
                    
                    # Should use default docs/ directory
                    call_args = mock_ensure.call_args
                    path_arg = call_args[0][0]
                    assert "docs" in str(path_arg)


class TestGeneratedContent:
    """Tests for content of generated documentation."""

    def test_openapi_content_is_dict(self):
        """Test that OpenAPI content is a dictionary."""
        captured_content = {}
        
        def capture_json(path, content):
            if "openapi.json" in str(path):
                captured_content["openapi"] = content
        
        with patch("src.chatty_commander.tools.workflow.ensure_dir"):
            with patch("src.chatty_commander.tools.workflow.write_json", side_effect=capture_json):
                with patch("src.chatty_commander.tools.workflow.write_text"):
                    generate_docs()
                    
                    assert isinstance(captured_content["openapi"], dict)
                    assert "openapi" in captured_content["openapi"]

    def test_markdown_is_string(self):
        """Test that markdown content is a string."""
        captured_content = {}
        
        def capture_text(path, content):
            if "API.md" in str(path):
                captured_content["markdown"] = content
        
        with patch("src.chatty_commander.tools.workflow.ensure_dir"):
            with patch("src.chatty_commander.tools.workflow.write_json"):
                with patch("src.chatty_commander.tools.workflow.write_text", side_effect=capture_text):
                    generate_docs()
                    
                    assert isinstance(captured_content["markdown"], str)
                    assert len(captured_content["markdown"]) > 0

    def test_index_contains_links(self):
        """Test that index contains documentation links."""
        captured_content = {}
        
        def capture_text(path, content):
            if "README.md" in str(path):
                captured_content["index"] = content
        
        with patch("src.chatty_commander.tools.workflow.ensure_dir"):
            with patch("src.chatty_commander.tools.workflow.write_json"):
                with patch("src.chatty_commander.tools.workflow.write_text", side_effect=capture_text):
                    generate_docs()
                    
                    assert "API.md" in captured_content["index"]
                    assert "openapi.json" in captured_content["index"]

    def test_index_contains_quick_start(self):
        """Test that index contains quick start section."""
        captured_content = {}
        
        def capture_text(path, content):
            if "README.md" in str(path):
                captured_content["index"] = content
        
        with patch("src.chatty_commander.tools.workflow.ensure_dir"):
            with patch("src.chatty_commander.tools.workflow.write_json"):
                with patch("src.chatty_commander.tools.workflow.write_text", side_effect=capture_text):
                    generate_docs()
                    
                    assert "Quick Start" in captured_content["index"] or "quick" in captured_content["index"].lower()


class TestWorkflowIntegration:
    """Integration-style tests."""

    def test_all_files_generated(self):
        """Test that all three files are generated."""
        with patch("src.chatty_commander.tools.workflow.ensure_dir"):
            with patch("src.chatty_commander.tools.workflow.write_json") as mock_json:
                with patch("src.chatty_commander.tools.workflow.write_text") as mock_text:
                    result = generate_docs()
                    
                    # Should write 1 JSON file
                    assert mock_json.call_count == 1
                    
                    # Should write 2 text files (API.md, README.md)
                    assert mock_text.call_count == 2

    def test_returns_absolute_paths(self):
        """Test that returned paths are absolute."""
        with patch("src.chatty_commander.tools.workflow.ensure_dir"):
            with patch("src.chatty_commander.tools.workflow.write_json"):
                with patch("src.chatty_commander.tools.workflow.write_text"):
                    result = generate_docs()
                    
                    assert result["openapi"].is_absolute() or str(result["openapi"]).startswith("/")


class TestEdgeCases:
    """Edge case tests."""

    def test_handles_write_errors(self):
        """Test handling of write errors."""
        with patch("src.chatty_commander.tools.workflow.ensure_dir"):
            with patch("src.chatty_commander.tools.workflow.write_json"):
                with patch("src.chatty_commander.tools.workflow.write_text", side_effect=IOError("Write failed")):
                    with pytest.raises(IOError):
                        generate_docs()

    def test_output_dir_created_if_missing(self):
        """Test that output directory is created if it doesn't exist."""
        custom_dir = Path("/nonexistent/path/docs")
        
        with patch("src.chatty_commander.tools.workflow.ensure_dir") as mock_ensure:
            with patch("src.chatty_commander.tools.workflow.write_json"):
                with patch("src.chatty_commander.tools.workflow.write_text"):
                    generate_docs(output_dir=custom_dir)
                    
                    # Should create the directory
                    mock_ensure.assert_called_once_with(custom_dir)
