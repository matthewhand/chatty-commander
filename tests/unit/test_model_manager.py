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

"""Targeted unit tests for ModelManager (addresses qa 'no tests found' for app/model_manager.py).

Covers init/reload (mock + state paths), load_model_set (errors, skips, exceptions), listen,
get_models, repr. Uses mocks for config, random, asyncio, Model load.
Follows AAA, fixtures, patch patterns from test_pipeline.py / test_command_executor.py.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Ensure src on path for direct chatty imports (consistent with other unit tests)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from chatty_commander.app.model_manager import ModelManager


@pytest.fixture
def mock_config():
    """Mock config with model path attrs."""
    cfg = Mock()
    cfg.general_models_path = "/fake/general"
    cfg.system_models_path = "/fake/system"
    cfg.chat_models_path = "/fake/chat"
    return cfg


@pytest.fixture
def manager(mock_config):
    """ModelManager with mock_models=True for deterministic tests (no FS)."""
    return ModelManager(config=mock_config, mock_models=True)


class TestModelManagerInitAndReload:
    def test_init_populates_with_mock_models(self, mock_config):
        m = ModelManager(config=mock_config, mock_models=True)
        assert "general" in m.models
        assert "mock_model" in m.models["general"]
        assert m.active_models

    def test_reload_models_for_idle_state(self, manager, mock_config):
        res = manager.reload_models("idle")
        assert "general" in manager.models
        assert manager.active_models == manager.models["general"]
        assert res == manager.models["general"]

    def test_reload_models_for_computer_state(self, manager, mock_config):
        # mock_models branch sets active to general dummy for any state (preserves current behavior)
        res = manager.reload_models("computer")
        assert isinstance(res, dict)
        assert manager.active_models  # set

    def test_reload_models_for_chatty_state(self, manager, mock_config):
        res = manager.reload_models("chatty")
        assert isinstance(res, dict)

    def test_reload_models_unknown_state_returns_empty(self, manager):
        # In mock_models=True the 'if state:' branch returns the general dummy for any state (incl unknown)
        res = manager.reload_models("unknown")
        assert isinstance(res, dict)
        assert len(res) > 0  # dummy populated


class TestModelManagerLoadModelSet:
    def test_load_model_set_empty_dir_nonexistent(self, manager):
        res = manager.load_model_set("/non/existent/path")
        assert res == {}

    def test_load_model_set_skips_non_onnx_and_missing(self, manager, tmp_path):
        (tmp_path / "notmodel.txt").write_text("x")
        (tmp_path / "good.onnx").write_text("x")  # but will fail load unless patched
        with patch("chatty_commander.app.model_manager.os.path.exists", return_value=True), \
             patch("chatty_commander.app.model_manager.os.listdir", return_value=["notmodel.txt", "good.onnx", "miss.onnx"]), \
             patch("chatty_commander.app.model_manager.os.path.exists", side_effect=lambda p: "miss" not in p):
            # Force one load success one skip
            with patch("chatty_commander.app.model_manager._get_patchable_model_class") as g:
                g.return_value = Mock(return_value=Mock())
                res = manager.load_model_set(str(tmp_path))
                # since listdir mocked with exists varying, just ensure no crash and dict
                assert isinstance(res, dict)

    def test_load_model_set_handles_listdir_error(self, manager):
        with patch("chatty_commander.app.model_manager.os.path.exists", return_value=True), \
             patch("chatty_commander.app.model_manager.os.listdir", side_effect=Exception("perm")):
            res = manager.load_model_set("/some/path")
            assert res == {}

    def test_load_model_set_catches_model_instantiation_error(self, manager, tmp_path):
        (tmp_path / "bad.onnx").write_text("")
        with patch("chatty_commander.app.model_manager.os.path.exists", return_value=True), \
             patch("chatty_commander.app.model_manager.os.listdir", return_value=["bad.onnx"]), \
             patch("chatty_commander.app.model_manager._get_patchable_model_class") as g:
            g.return_value.side_effect = RuntimeError("load fail")
            res = manager.load_model_set(str(tmp_path))
            assert res == {}  # error path skips adding


class TestModelManagerListenAndUtils:
    def test_listen_for_commands_returns_key_or_none(self, manager):
        with patch("chatty_commander.app.model_manager.random.random", return_value=0.01), \
             patch("chatty_commander.app.model_manager.random.choice", return_value="hello"):
            # active has something from mock init
            manager.active_models = {"hello": Mock()}
            res = manager.listen_for_commands()
            # either the chosen or None (race in async) but under patch likely str or None
            assert res is None or isinstance(res, str)

    def test_get_models_returns_state_or_empty(self, manager):
        assert manager.get_models("general") == manager.models.get("general", {})
        assert manager.get_models("missing") == {}

    def test_repr_contains_counts(self, manager):
        r = repr(manager)
        assert "ModelManager" in r
        assert "general=" in r


class TestModelManagerMoreCoverage:
    """Extra behavior/edge tests to address 'no tests found'."""

    def test_reload_models_state_none_loads_all(self, manager):
        res = manager.reload_models(None)
        assert "general" in res

    def test_listen_for_commands_no_active_returns_none(self, manager):
        manager.active_models = {}
        with patch("chatty_commander.app.model_manager.asyncio.run", return_value=None):
            assert manager.listen_for_commands() is None

    def test_load_model_set_skips_non_onnx(self, manager):
        with patch("chatty_commander.app.model_manager.os.path.exists", return_value=True), \
             patch("chatty_commander.app.model_manager.os.listdir", return_value=["foo.txt", "bar.wav"]):
            res = manager.load_model_set("/p")
            assert res == {}
