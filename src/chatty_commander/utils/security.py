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

import re
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


# Patterns are matched against keys normalized to lowercase alphanumerics,
# so "Api-Key", "apiKey", "API KEY" and "api_key" all reduce to "apikey".
_SENSITIVE_KEY_PATTERNS = frozenset(
    {
        "apikey",
        "apitoken",
        "accesstoken",
        "authtoken",
        "bridgetoken",
        "keyhash",
        "password",
        "passwd",
        "secret",
        "databaseurl",
        "token",
    }
)

_KEY_NORMALIZE_RE = re.compile(r"[^a-z0-9]+")


def _is_sensitive_key(key: Any) -> bool:
    normalized = _KEY_NORMALIZE_RE.sub("", str(key).lower())
    return any(p in normalized for p in _SENSITIVE_KEY_PATTERNS)


def mask_sensitive_data(data: Any) -> Any:
    """Recursively mask sensitive keys in dicts, lists and tuples.

    Keys are matched case-insensitively and separator-insensitively, so
    variants like "Api-Key", "apiKey" and "API KEY" cannot bypass masking.
    """
    if isinstance(data, dict):
        masked = {}
        for k, v in data.items():
            if _is_sensitive_key(k):
                masked[k] = "********"
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
        return [mask_sensitive_data(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(mask_sensitive_data(item) for item in data)
    return data
