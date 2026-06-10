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

import logging
import secrets
import shlex
from typing import Any

logger = logging.getLogger(__name__)


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
    """
    Validates if a shell command is safe to execute.

    Blocks potentially harmful commands like 'sudo' and prevents path traversal
    in arguments, while allowing most common system utilities for flexibility.
    """
    if not cmd or not isinstance(cmd, str):
        return False

    import os

    try:
        # 1. Parse command using shlex to respect shell quoting rules.
        # This handles cases like 'echo "Value is $10"' safely.
        args = shlex.split(cmd)
        if not args:
            return False

        # 2. Extract base command and check against blacklist.
        # We use os.path.basename to prevent bypasses like '/bin/sudo'.
        base_cmd = os.path.basename(args[0])
        forbidden_commands = {
            "sudo", "su", "rm", "mv", "chmod", "chown", "curl", "wget",
            "python", "python3", "perl", "bash", "sh", "zsh", "nc", "netcat"
        }
        if base_cmd in forbidden_commands:
            logger.warning(f"Command {base_cmd!r} is forbidden: {cmd}")
            return False

        # 3. Check all arguments for path traversal patterns.
        for arg in args[1:]:
            if ".." in arg:
                logger.warning(f"Path traversal detected in argument: {arg}")
                return False

        return True
    except Exception as e:
        logger.error(f"Error validating command: {e}")
        return False
