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

import importlib
import io
import os
import unittest
from contextlib import redirect_stdout


class TestGuiHeadless(unittest.TestCase):
    def setUp(self):
        # Backup the DISPLAY environment variable if it exists
        self.original_display = os.environ.get("DISPLAY")
        if "DISPLAY" in os.environ:
            del os.environ["DISPLAY"]
        # Remove gui module from cache to force re-execution of top-level code
        if "chatty_commander.gui" in globals():
            del globals()["chatty_commander.gui"]
        if "chatty_commander.gui" in importlib.sys.modules:
            del importlib.sys.modules["chatty_commander.gui"]

    def tearDown(self):
        # Restore the original DISPLAY environment variable
        if self.original_display is not None:
            os.environ["DISPLAY"] = self.original_display
        elif "DISPLAY" in os.environ:
            del os.environ["DISPLAY"]

    def test_missing_display_warning(self):
        # Capture the printed output when importing gui
        f = io.StringIO()
        with redirect_stdout(f):
            import chatty_commander.gui as gui

            importlib.reload(gui)
        output = f.getvalue()
        self.assertIn("Warning: DISPLAY environment variable not set", output)


if __name__ == "__main__":
    unittest.main()
