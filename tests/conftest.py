import os
import sys

# Ensure project root is at front so 'import main' resolves to repo's main.py shim, not any site-packages main.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
