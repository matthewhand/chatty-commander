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

"""Tests for __main__ entry point module."""

from unittest.mock import patch


class TestMainEntryPoint:
    """Tests for the package entry point."""

    def test_main_import(self):
        """Test that main can be imported from cli.main."""
        from src.chatty_commander.__main__ import main
        assert callable(main)

    def test_main_execution(self):
        """Test that __main__ module executes without error when mocked."""
        with patch("src.chatty_commander.cli.main.main") as mock_main:
            # Simulate running the module
            mock_main.return_value = 0
            # Import would call main() if __name__ == "__main__"
            # But in test context, we just verify the import works
            from src.chatty_commander import __main__
            assert hasattr(__main__, "main")
