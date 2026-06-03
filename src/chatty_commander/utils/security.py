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

    Checks against a whitelist of allowed commands and ensures no dangerous
    characters or patterns are present that could lead to command injection
    or unauthorized execution.
    """
    if not cmd or not isinstance(cmd, str):
        return False

    # 1. Check for dangerous characters that might be interpreted by some shells
    # even if we use shell=False, just to be extra safe.
    dangerous_chars = {";", "&", "|", ">", "<", "$", "`", "\\", "!", "\n"}
    if any(char in cmd for char in dangerous_chars):
        logger.warning(f"Command contains dangerous characters: {cmd}")
        return False

    try:
        # 2. Parse command using shlex
        args = shlex.split(cmd)
        if not args:
            return False

        base_cmd = args[0]

        # 3. Whitelist of allowed base commands
        # In a production app, this should probably be configurable.
        # For now, we allow 'echo' as it's used in default configs.
        allowed_commands = {"echo"}

        if base_cmd not in allowed_commands:
            logger.warning(f"Command {base_cmd!r} is not in the whitelist: {cmd}")
            return False

        # 4. Check for suspicious patterns in arguments
        for arg in args[1:]:
            # Prevent potential flag injection or path traversal in arguments
            if arg.startswith("-") and any(c in arg for c in {"/", ".."}):
                logger.warning(f"Suspicious argument detected: {arg}")
                return False

        return True
    except Exception as e:
        logger.error(f"Error validating command: {e}")
        return False
