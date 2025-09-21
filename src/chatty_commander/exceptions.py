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

"""
Standardized exception hierarchy for Chatty Commander.

This module defines a consistent set of exceptions used throughout the application
to provide better error handling and debugging capabilities.
"""

from __future__ import annotations


class ChattyCommanderError(Exception):
    """
    Base exception class for all Chatty Commander errors.

    This serves as the root of the exception hierarchy and should be used
    for catching all application-specific errors.
    """

    pass


class ConfigurationError(ChattyCommanderError, ValueError):
    """
    Raised when there are issues with configuration loading, validation, or processing.

    This includes invalid config files, missing required settings, or malformed data.
    """

    pass


class ValidationError(ChattyCommanderError, ValueError):
    """
    Raised when input validation fails.

    This includes invalid command names, malformed data structures, or constraint violations.
    """

    pass


class ExecutionError(ChattyCommanderError, Exception):
    """
    Raised when command execution fails.

    This includes shell command failures, HTTP request errors, or keybinding execution issues.
    """

    pass


class DependencyError(ChattyCommanderError, ImportError):
    """
    Raised when required dependencies are missing or unavailable.

    This includes optional libraries like pyautogui or requests that may not be installed.
    """

    pass
