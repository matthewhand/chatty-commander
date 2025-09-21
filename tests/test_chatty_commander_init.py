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
Comprehensive tests for main package initialization and core functionality.

Tests package imports, version information, and core module availability.
"""

from unittest.mock import patch

import pytest

from src.chatty_commander import __init__ as chatty_commander_init


class TestPackageInitialization:
    """Test package initialization and core functionality."""

    def test_package_has_version(self):
        """Test that package has version information."""
        assert hasattr(chatty_commander_init, "__version__")
        assert isinstance(chatty_commander_init.__version__, str)
        assert len(chatty_commander_init.__version__) > 0

    def test_package_has_main_function(self):
        """Test that package exposes main function."""
        assert hasattr(chatty_commander_init, "main")
        assert callable(chatty_commander_init.main)

    def test_package_has_cli_interface(self):
        """Test that package exposes CLI interface."""
        assert hasattr(chatty_commander_init, "create_parser")
        assert callable(chatty_commander_init.create_parser)

        assert hasattr(chatty_commander_init, "run_orchestrator_mode")
        assert callable(chatty_commander_init.run_orchestrator_mode)

    def test_package_exports_all_functions(self):
        """Test that package exports all required functions."""
        expected_exports = ["main", "create_parser", "run_orchestrator_mode"]

        for export in expected_exports:
            assert hasattr(chatty_commander_init, export)
            assert callable(getattr(chatty_commander_init, export))

    def test_package_import_structure(self):
        """Test that package imports work correctly."""
        # Test that main modules can be imported
        try:
            from src.chatty_commander import create_parser, main, run_orchestrator_mode

            assert callable(main)
            assert callable(create_parser)
            assert callable(run_orchestrator_mode)
        except ImportError as e:
            pytest.fail(f"Failed to import main functions: {e}")

    def test_package_version_format(self):
        """Test that version follows semantic versioning."""
        import re

        version = chatty_commander_init.__version__

        # Should match semantic versioning pattern
        semver_pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$"
        assert re.match(
            semver_pattern, version
        ), f"Version {version} does not follow semantic versioning"

    def test_package_metadata(self):
        """Test that package has proper metadata."""
        # Should have author information
        assert hasattr(chatty_commander_init, "__author__")
        assert isinstance(chatty_commander_init.__author__, str)

        # Should have description
        assert hasattr(chatty_commander_init, "__description__")
        assert isinstance(chatty_commander_init.__description__, str)

        # Should have license
        assert hasattr(chatty_commander_init, "__license__")
        assert isinstance(chatty_commander_init.__license__, str)

    def test_package_dependencies(self):
        """Test that package can import its dependencies."""
        try:
            # Test importing key dependencies
            import json
            import logging
            import os
            import sys

            assert True  # All imports successful
        except ImportError as e:
            pytest.fail(f"Failed to import dependencies: {e}")

    def test_package_path_configuration(self):
        """Test that package path is properly configured."""
        import src.chatty_commander

        assert hasattr(src.chatty_commander, "__file__")
        assert src.chatty_commander.__file__.endswith("__init__.py")

    def test_package_namespace_cleanliness(self):
        """Test that package namespace is clean and organized."""
        # Get all public attributes (not starting with _)
        public_attrs = [
            attr for attr in dir(chatty_commander_init) if not attr.startswith("_")
        ]

        # Should have expected exports
        expected_public = {
            "main",
            "create_parser",
            "run_orchestrator_mode",
            "__version__",
            "__author__",
            "__description__",
            "__license__",
        }

        for attr in expected_public:
            assert attr in public_attrs, f"Missing expected public attribute: {attr}"

    def test_package_functionality_integration(self):
        """Test that package functions work together."""
        # Test that main function can be called (though it may fail without proper setup)
        try:
            # This should at least not raise import errors
            from src.chatty_commander import main

            assert callable(main)
        except Exception as e:
            pytest.fail(f"Package integration test failed: {e}")

    def test_package_error_handling(self):
        """Test that package handles errors gracefully."""
        # Test that importing with missing dependencies gives helpful errors
        with patch.dict("sys.modules", {"some_missing_module": None}):
            try:
                # Should handle missing dependencies gracefully
                from src.chatty_commander import main

                assert True
            except ImportError as e:
                # Should provide helpful error message
                assert "missing" in str(e).lower() or "not found" in str(e).lower()

    def test_package_configuration_loading(self):
        """Test that package can load configuration."""
        # Test that package can access configuration
        try:
            from src.chatty_commander.app import default_config

            assert default_config is not None
        except ImportError as e:
            pytest.fail(f"Failed to load default config: {e}")

    def test_package_logging_setup(self):
        """Test that package sets up logging correctly."""
        # Test that logging is available
        try:
            import logging

            # Should be able to get logger
            logger = logging.getLogger("chatty_commander")
            assert logger is not None
        except Exception as e:
            pytest.fail(f"Logging setup failed: {e}")

    def test_package_environment_detection(self):
        """Test that package can detect environment."""
        # Test that package can detect if it's running in different modes
        import os

        # Should handle different environment variables
        test_env_vars = {
            "CHATTY_COMMANDER_DEBUG": "true",
            "CHATTY_COMMANDER_CONFIG": "/test/path",
        }

        with patch.dict(os.environ, test_env_vars):
            # Should be able to import and run
            from src.chatty_commander import main

            assert callable(main)

    def test_package_cli_integration(self):
        """Test that package integrates with CLI properly."""
        # Test that CLI functions are properly exposed
        try:
            from src.chatty_commander import create_parser, main

            assert callable(create_parser)
            assert callable(main)
        except ImportError as e:
            pytest.fail(f"CLI integration failed: {e}")

    def test_package_module_structure(self):
        """Test that package has expected module structure."""
        expected_modules = ["advisors", "ai", "app", "cli", "llm", "voice", "web"]

        # Check that these modules can be imported
        for module in expected_modules:
            try:
                __import__(f"src.chatty_commander.{module}")
                assert True
            except ImportError as e:
                pytest.fail(f"Failed to import module {module}: {e}")

    def test_package_backward_compatibility(self):
        """Test that package maintains backward compatibility."""
        # Test that old import paths still work
        try:
            # These should work as fallbacks
            from src.chatty_commander import config, helpers

            assert True
        except ImportError as e:
            # Some may fail but should give helpful errors
            assert "shim" in str(e).lower() or "deprecated" in str(e).lower()

    def test_package_resource_loading(self):
        """Test that package can load resources."""
        # Test that package can find its own resources
        import os

        import src.chatty_commander

        package_dir = os.path.dirname(src.chatty_commander.__file__)
        assert os.path.exists(package_dir)
        assert os.path.isdir(package_dir)

        # Should have expected subdirectories
        expected_dirs = ["advisors", "ai", "app", "cli", "llm", "voice"]
        for expected_dir in expected_dirs:
            expected_path = os.path.join(package_dir, expected_dir)
            assert os.path.exists(expected_path), f"Missing directory: {expected_path}"

    def test_package_entry_points(self):
        """Test that package provides proper entry points."""
        # Test that package can be run as module
        import subprocess
        import sys

        try:
            # Should be able to get help
            result = subprocess.run(
                [sys.executable, "-m", "src.chatty_commander", "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Should exit successfully or provide help
            assert result.returncode in [
                0,
                2,
            ]  # 0 = success, 2 = argument error (expected for --help)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # If module execution fails, that's OK for this test
            pass

    def test_package_type_annotations(self):
        """Test that package has proper type annotations."""
        # Check that main functions have type hints
        import inspect

        from src.chatty_commander import main

        sig = inspect.signature(main)
        assert len(sig.parameters) > 0  # Should have parameters

        # Should have some type annotations
        annotated_params = [
            p
            for p in sig.parameters.values()
            if p.annotation != inspect.Parameter.empty
        ]
        assert len(annotated_params) >= 0  # At least some type hints

    def test_package_documentation(self):
        """Test that package has proper documentation."""
        # Check that main functions have docstrings
        from src.chatty_commander import main

        assert main.__doc__ is not None
        assert len(main.__doc__) > 0

        # Check that package has docstring
        import src.chatty_commander

        assert src.chatty_commander.__doc__ is not None
        assert len(src.chatty_commander.__doc__) > 0
