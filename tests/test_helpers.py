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

import os
import unittest

from chatty_commander.helpers import (
    ensure_directory_exists,
    format_command_output,
    parse_model_keybindings,
)


class TestHelpers(unittest.TestCase):
    def test_ensure_directory_exists(self):
        test_dir = "test_dir"
        ensure_directory_exists(test_dir)
        self.assertTrue(os.path.exists(test_dir))
        os.rmdir(test_dir)  # Clean up

    def test_format_command_output(self):
        output = "Line1\nLine2\nLine3"
        formatted = format_command_output(output)
        self.assertEqual(formatted, "Line1 | Line2 | Line3")

    def test_parse_model_keybindings(self):
        keybindings_str = "model1=ctrl+shift+1,model2=alt+F4"
        expected = {"model1": "ctrl+shift+1", "model2": "alt+F4"}
        result = parse_model_keybindings(keybindings_str)
        self.assertEqual(result, expected)

    def test_parse_model_keybindings_empty(self):
        result = parse_model_keybindings("")
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
