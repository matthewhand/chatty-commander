import os
import sys
from src.chatty_commander.gui.avatar_gui import _avatar_index_path

# Ensure placeholder exists for this test
path = _avatar_index_path()
print("Avatar index path:", path)
print("Exists:", path.exists())

# Simulate headless import test (no DISPLAY)
os.environ.pop('DISPLAY', None)

# Just import main and ensure GUI code path remains guarded
import importlib
main = importlib.import_module('src.chatty_commander.main')
print('Main module imported, gui path guarded OK')
