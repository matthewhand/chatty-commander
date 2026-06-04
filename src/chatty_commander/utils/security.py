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

import secrets
from typing import Any


def constant_time_compare(provided: str | None, expected: str | None) -> bool:
    """Compare two credential strings in constant time.

    Returns False if either value is None or empty, preventing both
    timing attacks and NoneType bypass issues.
    """
    if not provided or not expected:
        return False
    return secrets.compare_digest(
        provided.encode("utf-8"),
        str(expected).encode("utf-8"),
    )


def mask_sensitive_data(data: Any) -> Any:
    """Recursively mask sensitive keys in a dictionary or list."""
    sensitive_patterns = {
        "api_key",
        "api_token",
        "access_token",
        "auth_token",
        "bridge_token",
        "password",
        "passwd",
        "secret",
        "database_url",
        "token",
    }

    if isinstance(data, dict):
        masked = {}
        # Logic flow
        for k, v in data.items():
            if any(p in str(k).lower() for p in sensitive_patterns):
                masked[k] = "********"
            # Logic flow
            elif str(k).lower() == "auth":
                # Special case for 'auth' which often contains credentials
                if isinstance(v, dict):
                    masked[k] = mask_sensitive_data(v)
                else:
                    masked[k] = "********"
            else:
                masked[k] = mask_sensitive_data(v)
        return masked
    elif isinstance(data, list):
        # Logic flow
        return [mask_sensitive_data(item) for item in data]
    return data


def is_safe_command(cmd: str) -> bool:
    """Check if a shell command is safe to execute."""
    # Only allow "echo" commands for now
    if not cmd.startswith("echo "):
        return False

    # Prevent shell metacharacters
    dangerous_chars = [";", "|", "&", "<", ">", "$", "(", ")", "`"]
    if any(c in cmd for c in dangerous_chars):
        return False

    # Check for flag injection or path traversal
    # by splitting arguments (basic space split is enough here since we blocked metacharacters and quotes aren't strictly needed for echo)
    parts = cmd.split()
    for part in parts[1:]:
        if part.startswith("-"):  # block flag injection
            return False
        if (
            "/" in part or "\\" in part or ".." in part
        ):  # block path traversal in arguments
            return False

    return True
