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
Test Ultimate Utils - Utility functions for ChattyCommander ultimate tests
"""

import json
import shutil
import tempfile
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import Mock


class TestUtils:
    """Utility functions for common test operations."""

    @staticmethod
    @contextmanager
    def temporary_file(
        suffix: str = ".json", content: str | None = None
    ) -> Generator[Path, None, None]:
        """Create a temporary file with optional content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
            temp_path = Path(f.name)
            if content:
                f.write(content)
                f.flush()
        try:
            yield temp_path
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)

    @staticmethod
    @contextmanager
    def temporary_directory() -> Generator[Path, None, None]:
        """Create a temporary directory."""
        temp_dir = Path(tempfile.mkdtemp(prefix="test_"))
        try:
            yield temp_dir
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def create_test_config_file(data: dict[str, Any]) -> Path:
        """Create a test configuration file with the given data."""
        temp_file = Path(tempfile.mktemp(suffix=".json"))
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=2)
        return temp_file

    @staticmethod
    def mock_environment_variables(**kwargs) -> Mock:
        """Create a mock for environment variables."""
        mock_env = Mock()
        mock_env.get = Mock(
            side_effect=lambda key, default=None: kwargs.get(key, default)
        )
        return mock_env

    @staticmethod
    def generate_test_data(size: int, pattern: str = "test_{}") -> list[str]:
        """Generate test data following a pattern."""
        return [pattern.format(i) for i in range(size)]

    @staticmethod
    def measure_execution_time(func: callable, *args, **kwargs) -> tuple:
        """Measure the execution time of a function."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = end_time - start_time
        return result, duration
