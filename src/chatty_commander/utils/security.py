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


# Security hardening utilities for input validation and audit logging

import functools
from typing import Callable, Any, Tuple


def validate_input(
    allowed_types: Tuple[type, ...] = (str,),
    max_length: int = 1000,
    min_length: int = 1,
    allow_empty: bool = False
) -> Callable:
    """
    Decorator to validate function inputs for security.

    Args:
        allowed_types: Tuple of allowed types for first positional arg
        max_length: Maximum string length (if string input)
        min_length: Minimum string length (if string input)
        allow_empty: Whether to allow empty strings

    Returns:
        Decorated function with input validation
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check first positional arg
            if args:
                value = args[0]

                # Type validation
                if not isinstance(value, allowed_types):
                    raise TypeError(
                        f"{func.__name__}: Expected {allowed_types}, got {type(value)}"
                    )

                # String-specific validation
                if isinstance(value, str):
                    # Empty check
                    if not allow_empty and len(value.strip()) == 0:
                        raise ValueError(f"{func.__name__}: Input cannot be empty")

                    # Min length check
                    if len(value) < min_length:
                        raise ValueError(
                            f"{func.__name__}: Input too short (min {min_length})"
                        )

                    # Max length check (security: prevent DoS)
                    if len(value) > max_length:
                        raise ValueError(
                            f"{func.__name__}: Input too long (max {max_length})"
                        )

                    # Sanitize: strip whitespace
                    value = value.strip()

            # Audit logging for security monitoring
            logger.info(f"SECURITY: {func.__name__} called")

            return func(*args, **kwargs)
        return wrapper
    return decorator


def audit_log(operation: str, level: str = "info") -> Callable:
    """
    Decorator to add audit logging for sensitive operations.

    Args:
        operation: Description of the operation being performed
        level: Log level (info, warning, error)

    Returns:
        Decorated function with audit logging
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Log before execution
            log_func = getattr(logger, level)
            log_func(f"AUDIT: {operation} - {func.__name__} started")

            try:
                result = func(*args, **kwargs)
                # Log success
                log_func(f"AUDIT: {operation} - {func.__name__} completed")
                return result
            except Exception as e:
                # Log failure
                logger.error(f"AUDIT: {operation} - {func.__name__} failed: {e}")
                raise
        return wrapper
    return decorator


def sanitize_string(input_str: str, max_length: int = 1000) -> str:
    """
    Sanitize a string input for safe processing.

    Args:
        input_str: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not isinstance(input_str, str):
        raise TypeError(f"Expected str, got {type(input_str)}")

    # Strip whitespace
    sanitized = input_str.strip()

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        logger.warning(f"Input truncated to {max_length} characters")

    return sanitized
