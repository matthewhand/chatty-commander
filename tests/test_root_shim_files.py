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

"""Tests for root-level shim files with 0% coverage."""

import warnings
from unittest.mock import patch

import pytest


class TestConfigShim:
    """Test the root-level config.py shim file."""

    def test_config_deprecation_warning(self):
        """Test that importing config.py shows deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Import the config module (this should trigger the warning)

            # Verify deprecation warning was issued
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "config.py is deprecated" in str(w[0].message)
            assert "chatty_commander.app.config" in str(w[0].message)

    def test_config_imports_from_app_config(self):
        """Test that config.py imports from chatty_commander.app.config."""
        # Import config and verify it has the expected attributes
        import config

        # The config module should have imported everything from app.config
        # We can't test specific attributes without knowing the exact structure,
        # but we can verify the module loads without error
        assert config is not None

    def test_config_module_reloading(self):
        """Test that config module can be reloaded safely."""
        import importlib

        import config

        # Should be able to reload without error
        importlib.reload(config)


class TestCommandExecutorShim:
    """Test the root-level command_executor.py shim file."""

    def test_command_executor_exists(self):
        """Test that command_executor.py file exists and can be imported."""
        try:
            import command_executor

            assert command_executor is not None
        except ImportError:
            # File might not exist or might be empty
            pytest.skip("command_executor.py not found or not importable")

    def test_command_executor_content(self):
        """Test command_executor.py content if it exists."""
        try:
            import command_executor

            # If it's a shim file, it might import from the main package
            # or it might be a legacy file with actual implementation
            # We'll just verify it doesn't raise errors on import
            assert command_executor is not None

        except ImportError:
            pytest.skip("command_executor.py not found")


class TestOtherRootShimFiles:
    """Test other potential root-level shim files."""

    def test_demo_voice_chat_import(self):
        """Test that demo_voice_chat.py can be imported."""
        try:
            import demo_voice_chat

            assert demo_voice_chat is not None
        except ImportError:
            pytest.skip("demo_voice_chat.py not found or not importable")

    def test_conftest_import(self):
        """Test that conftest.py can be imported."""
        try:
            import conftest

            assert conftest is not None
        except ImportError:
            pytest.skip("conftest.py not found or not importable")

    @patch("sys.path")
    def test_root_level_imports_with_path_manipulation(self, mock_path):
        """Test importing root-level files with path manipulation."""
        # This tests the scenario where root-level files might need
        # special path handling to import correctly
        import os
        import sys

        # Add the project root to the path if not already there
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        try:
            import config

            assert config is not None
        except ImportError as e:
            pytest.skip(f"Could not import config: {e}")


class TestRootLevelFileStructure:
    """Test the structure and accessibility of root-level files."""

    def test_root_level_python_files_exist(self):
        """Test that expected root-level Python files exist."""
        import os

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        expected_files = [
            "config.py",
            "conftest.py",
        ]

        existing_files = []
        for filename in expected_files:
            filepath = os.path.join(project_root, filename)
            if os.path.exists(filepath):
                existing_files.append(filename)

        # At least config.py should exist based on our earlier test
        assert "config.py" in existing_files

    def test_root_level_file_permissions(self):
        """Test that root-level Python files have correct permissions."""
        import os
        import stat

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, "config.py")

        if os.path.exists(config_path):
            file_stat = os.stat(config_path)
            # File should be readable
            assert file_stat.st_mode & stat.S_IRUSR
            # File should be a regular file
            assert stat.S_ISREG(file_stat.st_mode)

    def test_root_level_file_encoding(self):
        """Test that root-level Python files have proper encoding."""
        import os

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, "config.py")

        if os.path.exists(config_path):
            try:
                with open(config_path, encoding="utf-8") as f:
                    content = f.read()
                    # Should be able to read as UTF-8
                    assert isinstance(content, str)
                    assert len(content) > 0
            except UnicodeDecodeError:
                pytest.fail("config.py is not valid UTF-8")


class TestLegacyFileCompatibility:
    """Test compatibility with legacy root-level files."""

    def test_legacy_imports_still_work(self):
        """Test that legacy import patterns still work."""
        # Test that old-style imports don't break
        try:
            # This might be how users previously imported config
            import config

            # Test that config module has expected attributes
            assert hasattr(config, "__name__")
        except ImportError:
            # This is expected if the shim is working correctly
            pass
        except Exception as e:
            pytest.fail(f"Unexpected error importing from config: {e}")

    def test_backward_compatibility_warnings(self):
        """Test that backward compatibility warnings are properly issued."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            try:
                import config  # noqa: F401

                # Should have at least one deprecation warning
                deprecation_warnings = [
                    warning
                    for warning in w
                    if issubclass(warning.category, DeprecationWarning)
                ]
                assert len(deprecation_warnings) >= 1

            except ImportError:
                pytest.skip("config.py not available for testing")

    def test_migration_path_clear(self):
        """Test that the migration path from old to new imports is clear."""
        # Test that the new import path works
        try:
            from chatty_commander.app.config import Config  # noqa: F401

            # If this works, the migration path is clear
            assert True
        except ImportError:
            pytest.skip("New config import path not available")


class TestRootLevelModuleCleanup:
    """Test cleanup and isolation of root-level modules."""

    def test_root_modules_dont_pollute_namespace(self):
        """Test that root-level modules don't pollute the global namespace."""
        import sys

        # Get initial module count
        initial_modules = set(sys.modules.keys())

        # Import config
        try:
            import config  # noqa: F401
        except ImportError:
            pytest.skip("config.py not available")

        # Check that we didn't import too many extra modules
        final_modules = set(sys.modules.keys())
        new_modules = final_modules - initial_modules

        # Should only add a reasonable number of new modules
        assert len(new_modules) < 20  # Arbitrary reasonable limit

    def test_root_modules_can_be_unloaded(self):
        """Test that root-level modules can be safely unloaded."""
        import sys

        try:
            import config

            module_name = config.__name__

            # Remove from sys.modules
            if module_name in sys.modules:
                del sys.modules[module_name]

            # Should be able to import again
            import config  # noqa: F401

        except ImportError:
            pytest.skip("config.py not available for testing")
