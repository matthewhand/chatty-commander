import unittest
import os
from helpers import ensure_directory_exists, format_command_output, parse_model_keybindings

class TestHelpers(unittest.TestCase):
    def test_ensure_directory_exists(self):
        test_dir = 'test_dir'
        ensure_directory_exists(test_dir)
        self.assertTrue(os.path.exists(test_dir))
        os.rmdir(test_dir)  # Clean up

    def test_format_command_output(self):
        output = 'Line1\nLine2\nLine3'
        formatted = format_command_output(output)
        self.assertEqual(formatted, 'Line1 | Line2 | Line3')

    def test_parse_model_keybindings(self):
        keybindings_str = 'model1=ctrl+shift+1,model2=alt+F4'
        expected = {'model1': 'ctrl+shift+1', 'model2': 'alt+F4'}
        result = parse_model_keybindings(keybindings_str)
        self.assertEqual(result, expected)

    def test_parse_model_keybindings_empty(self):
        result = parse_model_keybindings('')
        self.assertEqual(result, {})

if __name__ == '__main__':
    unittest.main()