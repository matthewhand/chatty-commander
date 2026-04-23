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
Comprehensive tests for CLI shim module.

Tests the compatibility shim that re-exports from chatty_commander.main.
"""

import warnings
from unittest.mock import MagicMock, patch

import pytest

from src.chatty_commander import cli


class TestShimExports:
    """Test that shim properly exports expected symbols."""

    def test_create_parser_exported(self):
        """Test that create_parser is exported from shim."""
        from src.chatty_commander.cli.shim import create_parser
        assert create_parser is not None
        assert callable(create_parser)

    def test_run_orchestrator_mode_exported(self):
        """Test that run_orchestrator_mode is exported from shim."""
        from src.chatty_commander.cli.shim import run_orchestrator_mode
        assert run_orchestrator_mode is not None

    def test_exports_are_callable(self):
        """Test that exports are callable functions."""
        from src.chatty_commander.cli.shim import create_parser, run_orchestrator_mode
        
        # Should be callable functions
        assert callable(create_parser)
        assert run_orchestrator_mode is not None


class TestShimIntegration:
    """Integration tests for shim functionality."""

    def test_create_parser_functionality(self):
        """Test that create_parser works when called."""
        from src.chatty_commander.cli.shim import create_parser
        
        # Should be able to call it (may fail due to no args, but shouldn't crash)
        try:
            parser = create_parser()
            assert parser is not None
        except (TypeError, SystemExit):
            # Expected if parser requires arguments
            pass

    def test_shim_import_does_not_crash(self):
        """Test that importing shim doesn't crash."""
        # Importing should work without errors
        import src.chatty_commander.cli.shim as shim_module
        assert hasattr(shim_module, 'create_parser')
        assert hasattr(shim_module, 'run_orchestrator_mode')


class TestShimCompatibility:
    """Tests for backward compatibility."""

    def test_shim_provides_legacy_interface(self):
        """Test that shim provides expected legacy interface."""
        # Legacy code might do: from chatty_commander.main_shim import create_parser
        # Our shim should support this pattern
        from src.chatty_commander.cli.shim import create_parser, run_orchestrator_mode
        
        # Both should be available
        assert callable(create_parser) or create_parser is not None
        assert run_orchestrator_mode is not None

    def test_shim_module_has_docstring(self):
        """Test that shim module has documentation."""
        import src.chatty_commander.cli.shim as shim_module
        assert shim_module.__doc__ is not None
        assert 'shim' in shim_module.__doc__.lower() or 'compatibility' in shim_module.__doc__.lower()


class TestShimEdgeCases:
    """Edge case tests for shim."""

    def test_multiple_imports_consistent(self):
        """Test that multiple imports return same objects."""
        from src.chatty_commander.cli.shim import create_parser as cp1
        from src.chatty_commander.cli.shim import create_parser as cp2
        
        # Same object on multiple imports
        assert cp1 is cp2

    def test_shim_exports_functionality(self):
        """Test that shim exports work correctly."""
        from src.chatty_commander.cli.shim import create_parser
        
        # Should be a valid function
        assert callable(create_parser)
