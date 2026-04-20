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
Comprehensive tests for CLI interface module.

Tests the legacy CLI shim that forwards to chatty_commander.cli.cli.
"""

import warnings
from unittest.mock import MagicMock, patch

import pytest


class TestInterfaceDeprecation:
    """Test deprecation warning functionality."""

    def test_import_emits_deprecation_warning(self):
        """Test that importing interface.py emits deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Re-import to trigger warning
            import importlib
            import src.chatty_commander.cli.interface as interface
            importlib.reload(interface)
            
            # Check for deprecation warning
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1
            assert 'legacy' in str(deprecation_warnings[0].message).lower() or 'shim' in str(deprecation_warnings[0].message).lower()


class TestInterfaceExports:
    """Test that interface properly exports cli_main."""

    def test_cli_main_exported(self):
        """Test that cli_main is exported."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from src.chatty_commander.cli.interface import cli_main
            assert cli_main is not None
            assert callable(cli_main)

    def test_cli_main_is_callable(self):
        """Test that cli_main is a callable function."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from src.chatty_commander.cli.interface import cli_main
            
            # Should be a callable function
            assert callable(cli_main)


class TestInterfaceExecution:
    """Test interface execution paths."""

    def test_module_runnable(self):
        """Test that module can be run."""
        import runpy
        import sys
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Mock cli_main to avoid actual execution
            with patch('src.chatty_commander.cli.cli.cli_main') as mock_main:
                mock_main.return_value = None
                try:
                    runpy.run_module('src.chatty_commander.cli.interface', run_name='__main__')
                    # If we get here, it didn't crash
                except SystemExit as e:
                    # SystemExit with code 0 is OK
                    if e.code != 0 and e.code is not None:
                        raise


class TestInterfaceCompatibility:
    """Backward compatibility tests."""

    def test_interface_provides_expected_symbol(self):
        """Test that interface module provides cli_main."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Legacy code might import: from cli import cli_main
            from src.chatty_commander.cli import interface
            assert hasattr(interface, 'cli_main')

    def test_interface_module_attributes(self):
        """Test that interface module has expected attributes."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import src.chatty_commander.cli.interface as interface
            
            # Should have cli_main
            assert hasattr(interface, 'cli_main')
            
            # Should have __name__
            assert interface.__name__ == 'src.chatty_commander.cli.interface'
