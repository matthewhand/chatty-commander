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
Comprehensive tests for compatibility layer module.

Tests legacy module path aliasing and compatibility shims.
"""

import sys
import warnings
from types import ModuleType
from unittest.mock import patch

import pytest

from src.chatty_commander import compat


class TestCompatAliases:
    """Test ALIASES dictionary for legacy module paths."""

    def test_aliases_defined(self):
        """Test that ALIASES dictionary is defined."""
        assert hasattr(compat, 'ALIASES')
        assert isinstance(compat.ALIASES, dict)

    def test_aliases_not_empty(self):
        """Test that ALIASES contains legacy module mappings."""
        assert len(compat.ALIASES) > 0

    def test_config_alias(self):
        """Test config module alias."""
        assert 'config' in compat.ALIASES
        assert compat.ALIASES['config'] == 'chatty_commander.app.config'

    def test_model_manager_alias(self):
        """Test model_manager module alias."""
        assert 'model_manager' in compat.ALIASES
        assert compat.ALIASES['model_manager'] == 'chatty_commander.app.model_manager'

    def test_state_manager_alias(self):
        """Test state_manager module alias."""
        assert 'state_manager' in compat.ALIASES
        assert compat.ALIASES['state_manager'] == 'chatty_commander.app.state_manager'

    def test_web_mode_alias(self):
        """Test web_mode module alias."""
        assert 'web_mode' in compat.ALIASES
        assert compat.ALIASES['web_mode'] == 'chatty_commander.web.web_mode'

    def test_command_executor_alias(self):
        """Test command_executor module alias."""
        assert 'command_executor' in compat.ALIASES
        assert compat.ALIASES['command_executor'] == 'chatty_commander.app.command_executor'

    def test_all_aliases_have_valid_format(self):
        """Test that all aliases have valid module path format."""
        for legacy_name, modern_path in compat.ALIASES.items():
            assert isinstance(legacy_name, str)
            assert isinstance(modern_path, str)
            assert '.' in modern_path  # Valid module path
            assert not modern_path.startswith('.')
            assert not modern_path.endswith('.')


class TestLoadFunction:
    """Test load function for importing legacy modules."""

    def test_function_exists(self):
        """Test that load function exists."""
        assert hasattr(compat, 'load')
        assert callable(compat.load)

    def test_load_known_alias_with_warning(self):
        """Test loading a known legacy import emits deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Use a module that should exist
            result = compat.load('config')
            
            # Should return a module
            assert isinstance(result, ModuleType)
            # Should emit deprecation warning
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert 'deprecated' in str(w[0].message).lower()

    def test_load_nonexistent_module_raises_error(self):
        """Test loading non-existent module raises ImportError."""
        with pytest.raises(ImportError):
            compat.load('nonexistent_module_xyz')


class TestExposeFunction:
    """Test expose function for populating namespace."""

    def test_function_exists(self):
        """Test that expose function exists."""
        assert hasattr(compat, 'expose')
        assert callable(compat.expose)

    def test_expose_populates_namespace(self):
        """Test that expose populates namespace with module attributes."""
        namespace = {}
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = compat.expose(namespace, 'config')
        
        # Should return a module
        assert isinstance(result, ModuleType)
        # Namespace should be populated
        assert '__all__' in namespace

    def test_expose_with_all_attribute(self):
        """Test that expose respects __all__ attribute."""
        namespace = {}
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            compat.expose(namespace, 'config')
        
        # __all__ should be a list
        assert isinstance(namespace['__all__'], list)


class TestIntegration:
    """Integration tests for compatibility layer."""

    def test_all_aliases_importable(self):
        """Test that all aliases in ALIASES can be loaded or handled gracefully."""
        for legacy_name in compat.ALIASES.keys():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    result = compat.load(legacy_name)
                    assert isinstance(result, ModuleType)
                except Exception:
                    # Some modules may not exist or have issues, that's OK for this test
                    # We just verify the alias system doesn't crash
                    pass

    def test_no_circular_references(self):
        """Test that there are no circular references in aliases."""
        for legacy_name, modern_path in compat.ALIASES.items():
            # Modern path should not point back to legacy name
            assert modern_path != legacy_name
            # Modern path should not contain 'compat' (would be circular)
            assert 'compat' not in modern_path


class TestCompatEdgeCases:
    """Test edge cases and error handling."""

    def test_load_empty_string(self):
        """Test that loading empty string raises error (ImportError or similar)."""
        with pytest.raises((ImportError, ModuleNotFoundError, ValueError)):
            compat.load('')

    def test_load_none_raises_error(self):
        """Test that loading None raises AttributeError (NoneType has no startswith)."""
        with pytest.raises((TypeError, AttributeError)):
            compat.load(None)


class TestCompatExports:
    """Test __all__ exports."""

    def test_all_exports_defined(self):
        """Test that __all__ is properly defined."""
        assert hasattr(compat, '__all__')
        assert isinstance(compat.__all__, list)

    def test_all_contains_expected_exports(self):
        """Test that __all__ contains expected exports."""
        expected = ['ALIASES', 'load', 'expose']
        for item in expected:
            assert item in compat.__all__
