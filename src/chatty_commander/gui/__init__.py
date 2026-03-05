import os
if "DISPLAY" not in os.environ and os.name == "posix":
    print("Warning: DISPLAY environment variable not set")
