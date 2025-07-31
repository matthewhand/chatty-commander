import os
import io
import importlib
import unittest
from contextlib import redirect_stdout

class TestGuiHeadless(unittest.TestCase):
    def setUp(self):
        # Backup the DISPLAY environment variable if it exists
        self.original_display = os.environ.get('DISPLAY')
        if 'DISPLAY' in os.environ:
            del os.environ['DISPLAY']
        # Remove gui module from cache to force re-execution of top-level code
        if 'gui' in globals():
            del globals()['gui']
        if 'gui' in importlib.sys.modules:
            del importlib.sys.modules['gui']

    def tearDown(self):
        # Restore the original DISPLAY environment variable
        if self.original_display is not None:
            os.environ['DISPLAY'] = self.original_display
        elif 'DISPLAY' in os.environ:
            del os.environ['DISPLAY']

    def test_missing_display_warning(self):
        # Capture the printed output when importing gui
        f = io.StringIO()
        with redirect_stdout(f):
            import gui
            importlib.reload(gui)
        output = f.getvalue()
        self.assertIn("Warning: DISPLAY environment variable not set", output)

if __name__ == '__main__':
    unittest.main()