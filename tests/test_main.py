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

"""Tests for main module (backward compatibility shim)."""

from unittest.mock import MagicMock, patch

import pytest

from src.chatty_commander import main as main_module


class TestMainExports:
    """Tests for module exports."""

    def test_main_function_exists(self):
        """Test that main function is exported."""
        assert hasattr(main_module, "main")
        assert callable(main_module.main)

    def test_create_parser_exists(self):
        """Test that create_parser is exported."""
        assert hasattr(main_module, "create_parser")
        assert callable(main_module.create_parser)

    def test_run_orchestrator_mode_exists(self):
        """Test that run_orchestrator_mode is exported."""
        assert hasattr(main_module, "run_orchestrator_mode")
        assert callable(main_module.run_orchestrator_mode)

    def test_config_exported(self):
        """Test that Config is exported."""
        assert hasattr(main_module, "Config")

    def test_model_manager_exported(self):
        """Test that ModelManager is exported."""
        assert hasattr(main_module, "ModelManager")

    def test_state_manager_exported(self):
        """Test that StateManager is exported."""
        assert hasattr(main_module, "StateManager")

    def test_command_executor_exported(self):
        """Test that CommandExecutor is exported."""
        assert hasattr(main_module, "CommandExecutor")

    def test_setup_logger_exported(self):
        """Test that setup_logger is exported."""
        assert hasattr(main_module, "setup_logger")

    def test_generate_default_config_exported(self):
        """Test that generate_default_config_if_needed is exported."""
        assert hasattr(main_module, "generate_default_config_if_needed")


class TestPropagatePatches:
    """Tests for _propagate_patches function."""

    def test_propagate_patches_exists(self):
        """Test that _propagate_patches function exists."""
        assert hasattr(main_module, "_propagate_patches")


class TestAllExports:
    """Tests for __all__ definition."""

    def test_all_exports_defined(self):
        """Test that __all__ is defined."""
        assert hasattr(main_module, "__all__")
        assert isinstance(main_module.__all__, list)

    def test_main_in_all(self):
        """Test that main is in __all__."""
        assert "main" in main_module.__all__

    def test_all_items_exist(self):
        """Test that all items in __all__ exist in module."""
        for item in main_module.__all__:
            assert hasattr(main_module, item), f"{item} not found in module"
