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

import warnings
from unittest.mock import MagicMock, patch

import pytest

from chatty_commander import compat


def test_load_with_alias():
    """Test that compat.load triggers a DeprecationWarning for aliased modules."""
    mock_aliases = {"old_mod": "new_mod"}
    with patch("chatty_commander.compat.ALIASES", mock_aliases):
        with patch("importlib.import_module") as mock_import:
            mock_import.return_value = MagicMock()
            with pytest.warns(DeprecationWarning, match="chatty_commander.old_mod is deprecated; use new_mod"):
                compat.load("old_mod")
            mock_import.assert_called_once_with("new_mod")

def test_load_without_alias():
    """Test that compat.load does not trigger a warning for non-aliased modules."""
    mock_aliases = {"old_mod": "new_mod"}
    with patch("chatty_commander.compat.ALIASES", mock_aliases):
        with patch("importlib.import_module") as mock_import:
            mock_import.return_value = MagicMock()
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                compat.load("new_mod")
                # Ensure no DeprecationWarning from chatty_commander was issued
                for warning in w:
                    if issubclass(warning.category, DeprecationWarning) and "chatty_commander" in str(warning.message):
                        pytest.fail(f"Unexpected DeprecationWarning: {warning.message}")
            mock_import.assert_called_once_with("new_mod")

def test_expose_with_all():
    """Test that compat.expose correctly populates the namespace using __all__."""
    mock_module = MagicMock()
    mock_module.attr1 = "val1"
    mock_module.attr2 = "val2"
    mock_module._private = "private"
    mock_module.__all__ = ["attr1"]

    namespace = {}
    with patch("chatty_commander.compat.load") as mock_load:
        mock_load.return_value = mock_module
        compat.expose(namespace, "some_mod")

        assert namespace["attr1"] == "val1"
        assert "attr2" not in namespace
        assert "_private" not in namespace
        assert namespace["__all__"] == ["attr1"]

def test_expose_without_all():
    """Test compat.expose when __all__ is not defined."""
    class MockModule:
        def __init__(self):
            self.attr1 = "val1"
            self.attr2 = "val2"
            self._private = "private"

    mock_module = MockModule()
    namespace = {}
    with patch("chatty_commander.compat.load") as mock_load:
        mock_load.return_value = mock_module
        compat.expose(namespace, "some_mod")

        assert namespace["attr1"] == "val1"
        assert namespace["attr2"] == "val2"
        assert "_private" not in namespace
        assert set(namespace["__all__"]) == {"attr1", "attr2"}
