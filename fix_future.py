import sys
import glob

def remove_future_annotations(filepath):
    try:
        with open(filepath, 'r') as file:
            content = file.read()

        if "from __future__ import annotations\n" in content:
            new_content = content.replace("from __future__ import annotations\n", "")
            with open(filepath, 'w') as file:
                file.write(new_content)
            print(f"Removed from {filepath}")
    except Exception as e:
        pass

for filepath in glob.glob("**/*.py", recursive=True):
    if "venv" not in filepath and ".venv" not in filepath:
        remove_future_annotations(filepath)
