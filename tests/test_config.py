"""Tests for chatty_commander.app.config.Config — defaults, properties, actions, updates."""

import json
import os
from itertools import product
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from chatty_commander.app.config import Config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_tmp_config(tmp_path: Path, data: dict) -> Path:
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(data), encoding="utf-8")
    return cfg_path


def _clean_env_config(monkeypatch):
    """Return a Config with all env overrides removed."""
    for name in (
        "CHATCOMM_DEBUG",
        "CHATCOMM_DEFAULT_STATE",
        "CHATCOMM_INFERENCE_FRAMEWORK",
        "CHATCOMM_START_ON_BOOT",
        "CHATCOMM_CHECK_FOR_UPDATES",
        "CHATBOT_ENDPOINT",
        "HOME_ASSISTANT_ENDPOINT",
    ):
        monkeypatch.delenv(name, raising=False)
    return Config(config_file="")


# ---------------------------------------------------------------------------
# Defaults & validation
# ---------------------------------------------------------------------------


class TestConfigDefaults:
    @pytest.fixture
    def cfg_file(self, tmp_path):
        return str(tmp_path / "config.json")

    @pytest.fixture
    def empty_cfg(self, cfg_file):
        with open(cfg_file, "w") as f:
            json.dump({}, f)
        return cfg_file

    def test_defaults_load_correctly(self, empty_cfg):
        config = Config(empty_cfg)
        assert config.default_state == "idle"
        assert config.general_models_path == "models-idle"
        assert len(config.commands) > 0
        assert "hello" in config.commands
        assert config.voice_only is False

    def test_missing_config_file_uses_defaults(self, tmp_path):
        missing = str(tmp_path / "nonexistent.json")
        config = Config(missing)
        assert isinstance(config.commands, dict)
        assert len(config.commands) > 0
        assert isinstance(config.config_data, dict)

    def test_validate_config_bad_types(self, cfg_file):
        data = {
            "state_models": "not_a_dict",
            "api_endpoints": ["not", "a", "dict"],
            "commands": 123,
        }
        with open(cfg_file, "w") as f:
            json.dump(data, f)
        config = Config(cfg_file)
        assert isinstance(config.state_models, dict)
        assert isinstance(config.api_endpoints, dict)
        assert isinstance(config.commands, dict)
        assert config.state_models == {}

    def test_state_transitions(self, cfg_file):
        data = {
            "state_transitions": {
                "idle": {"wakeword_1": "active"},
                "active": {"wakeword_2": "idle"},
            }
        }
        with open(cfg_file, "w") as f:
            json.dump(data, f)
        config = Config(cfg_file)
        assert config.state_transitions["idle"]["wakeword_1"] == "active"
        assert config.state_transitions["active"]["wakeword_2"] == "idle"

    def test_env_overrides_default_state(self, cfg_file):
        with open(cfg_file, "w") as f:
            json.dump({"default_state": "idle"}, f)
        with patch.dict(os.environ, {"CHATCOMM_DEFAULT_STATE": "super_active"}):
            config = Config(cfg_file)
            assert config.default_state == "super_active"

    def test_env_endpoint_overrides(self, cfg_file):
        with open(cfg_file, "w") as f:
            json.dump({}, f)
        with patch.dict(
            os.environ,
            {
                "CHATBOT_ENDPOINT": "http://override.local/",
                "HOME_ASSISTANT_ENDPOINT": "http://ha.local/api",
            },
        ):
            c = Config(config_file=cfg_file)
            assert c.api_endpoints["chatbot_endpoint"] == "http://override.local/"
            assert c.api_endpoints["home_assistant"] == "http://ha.local/api"

    def test_env_general_setting_overrides(self, cfg_file):
        data = {
            "general_settings": {
                "debug_mode": False,
                "default_state": "idle",
                "inference_framework": "onnx",
                "start_on_boot": False,
                "check_for_updates": True,
            }
        }
        with open(cfg_file, "w") as f:
            json.dump(data, f)
        with patch.dict(
            os.environ,
            {
                "CHATCOMM_DEBUG": "TrUe",
                "CHATCOMM_DEFAULT_STATE": "computer",
                "CHATCOMM_INFERENCE_FRAMEWORK": "pytorch",
                "CHATCOMM_START_ON_BOOT": "YeS",
                "CHATCOMM_CHECK_FOR_UPDATES": "0",
            },
        ):
            c = Config(config_file=cfg_file)
            assert c.debug_mode is True
            assert c.default_state == "computer"
            assert c.inference_framework == "pytorch"
            assert c.start_on_boot is True
            assert c.check_for_updates is False

    def test_reload_config(self, cfg_file):
        with open(cfg_file, "w") as f:
            json.dump({"default_state": "idle"}, f)
        config = Config(cfg_file)
        assert config.default_state == "idle"
        with open(cfg_file, "w") as f:
            json.dump({"default_state": "reloaded"}, f)
        assert config.reload_config() is True
        assert config.default_state == "reloaded"

    def test_state_model_permutations(self):
        config = Config()
        states = ["idle", "computer", "chatty"]
        models = [["model1"], ["model1", "model2"], []]
        for state, model_list in product(states, models):
            config.state_models[state] = model_list
            config.validate()
            assert config.state_models[state] == model_list


# ---------------------------------------------------------------------------
# Property getters / setters (GeneralSettings proxy)
# ---------------------------------------------------------------------------


class TestConfigProperties:
    def test_all_general_settings_properties(self):
        config = Config()
        gs = config.general_settings

        framework = gs.inference_framework
        assert isinstance(framework, str) and len(framework) > 0
        gs.inference_framework = "pytorch"
        assert gs.inference_framework == "pytorch"
        gs.inference_framework = "onnx"

        start_boot = gs.start_on_boot
        assert type(start_boot) is bool
        gs.start_on_boot = True
        assert gs.start_on_boot is True
        gs.start_on_boot = False
        assert gs.start_on_boot is False

        check_updates = gs.check_for_updates
        assert type(check_updates) is bool
        gs.check_for_updates = True
        assert gs.check_for_updates is True
        gs.check_for_updates = False
        assert gs.check_for_updates is False

        debug = gs.debug_mode
        assert type(debug) is bool
        gs.debug_mode = True
        assert gs.debug_mode is True
        gs.debug_mode = False
        assert gs.debug_mode is False

    def test_property_setters_with_type_conversion(self):
        config = Config()
        gs = config.general_settings

        gs.debug_mode = 1
        assert gs.debug_mode is True
        gs.debug_mode = 0
        assert gs.debug_mode is False

        gs.start_on_boot = 1
        assert gs.start_on_boot is True
        gs.start_on_boot = 0
        assert gs.start_on_boot is False

        gs.check_for_updates = 1
        assert gs.check_for_updates is True
        gs.check_for_updates = 0
        assert gs.check_for_updates is False

        gs.inference_framework = "tensorflow"
        assert gs.inference_framework == "tensorflow"

    def test_config_data_updates(self):
        config = Config()
        gs = config.general_settings

        gs.debug_mode = True
        assert config.config_data.get("general", {}).get("debug_mode") is True

        gs.start_on_boot = True
        assert config.config_data.get("general", {}).get("start_on_boot") is True

        gs.check_for_updates = False
        assert config.config_data.get("general", {}).get("check_for_updates") is False

        gs.inference_framework = "custom"
        assert (
            config.config_data.get("general", {}).get("inference_framework") == "custom"
        )

    def test_inference_framework_repeated_access(self):
        config = Config()
        gs = config.general_settings
        framework = gs.inference_framework
        assert isinstance(framework, str) and len(framework) > 0
        assert gs.inference_framework == framework

    def test_debug_mode_string_conversion(self):
        config = Config()
        gs = config.general_settings
        gs.debug_mode = "true"
        assert gs.debug_mode is True
        gs.debug_mode = ""
        assert gs.debug_mode is False

    def test_config_general_data_defaults(self):
        config = Config()
        general = config.config_data.get("general", {})
        assert isinstance(general, dict)
        framework = general.get("inference_framework", "onnx")
        assert isinstance(framework, str) and len(framework) > 0
        debug = general.get("debug_mode", True)
        assert type(debug) is bool


# ---------------------------------------------------------------------------
# Action building (commands -> model_actions)
# ---------------------------------------------------------------------------


class TestConfigActions:
    def test_builds_model_actions_from_commands_and_keybindings(self, tmp_path):
        data = {
            "keybindings": {"do_paste": "ctrl+v"},
            "commands": {
                "paste": {"action": "keypress", "keys": "do_paste"},
                "call_bot": {"action": "url", "url": "{chatbot_endpoint}/run"},
                "say": {"action": "custom_message", "message": "hello"},
            },
            "api_endpoints": {"chatbot_endpoint": "http://example.test"},
            "general_settings": {"debug_mode": True},
        }
        cfg_file = _write_tmp_config(tmp_path, data)
        cfg = Config.load(str(cfg_file))
        assert cfg.debug_mode is True
        assert cfg.model_actions["paste"] == {"keypress": "ctrl+v"}
        assert cfg.model_actions["call_bot"]["url"] == "http://example.test/run"
        assert cfg.model_actions["say"] == {"shell": "echo hello"}

    def test_builds_keypress_without_keybinding_name(self, tmp_path):
        data = {
            "commands": {"press": {"action": "keypress", "keys": "alt+tab"}},
        }
        cfg_file = _write_tmp_config(tmp_path, data)
        cfg = Config.load(str(cfg_file))
        assert cfg.model_actions["press"] == {"keypress": "alt+tab"}

    def test_handles_empty_commands(self, tmp_path):
        data = {"commands": {}}
        cfg_file = _write_tmp_config(tmp_path, data)
        cfg = Config.load(str(cfg_file))
        assert cfg.model_actions == {}


# ---------------------------------------------------------------------------
# Update settings & update-check
# ---------------------------------------------------------------------------


class TestConfigUpdates:
    def test_update_general_setting_initializes_general(self, monkeypatch):
        config = _clean_env_config(monkeypatch)
        config.config_data.pop("general", None)
        config._update_general_setting("debug_mode", False)
        assert config.config_data["general"]["debug_mode"] is False

    def test_set_check_for_updates(self, monkeypatch):
        config = _clean_env_config(monkeypatch)
        config.set_check_for_updates(0)
        assert config.check_for_updates is False
        assert config.config_data["general"]["check_for_updates"] is False
        config.set_check_for_updates(1)
        assert config.check_for_updates is True
        assert config.config_data["general"]["check_for_updates"] is True

    def test_set_start_on_boot_calls_hooks(self, monkeypatch):
        config = _clean_env_config(monkeypatch)
        with (
            patch.object(config, "_enable_start_on_boot") as enable,
            patch.object(config, "_disable_start_on_boot") as disable,
        ):
            config.set_start_on_boot(True)
            enable.assert_called_once()
            disable.assert_not_called()
            assert config.start_on_boot is True
            assert config.config_data["general"]["start_on_boot"] is True

            config.set_start_on_boot(False)
            disable.assert_called_once()
            assert config.start_on_boot is False
            assert config.config_data["general"]["start_on_boot"] is False

    def test_perform_update_check_disabled(self, monkeypatch):
        config = _clean_env_config(monkeypatch)
        config.set_check_for_updates(False)
        with patch("chatty_commander.app.config.subprocess.run") as run_mock:
            assert config.perform_update_check() is None
            run_mock.assert_not_called()

    def test_perform_update_check_not_in_git_repo(self, monkeypatch):
        config = _clean_env_config(monkeypatch)
        config.set_check_for_updates(True)
        mock_result = MagicMock(returncode=1, stdout="")
        with patch(
            "chatty_commander.app.config.subprocess.run", return_value=mock_result
        ) as run_mock:
            assert config.perform_update_check() is None
            assert run_mock.call_count == 1
            assert run_mock.call_args.args[0] == ["git", "rev-parse", "--git-dir"]

    def test_perform_update_check_updates_available(self, monkeypatch):
        config = _clean_env_config(monkeypatch)
        config.set_check_for_updates(True)
        run_results = [
            MagicMock(returncode=0, stdout=""),
            MagicMock(returncode=0, stdout=""),
            MagicMock(returncode=0, stdout="2\n"),
            MagicMock(returncode=0, stdout="Fix bug\n"),
        ]
        with patch(
            "chatty_commander.app.config.subprocess.run", side_effect=run_results
        ) as run_mock:
            result = config.perform_update_check()
        assert run_mock.call_count == 4
        assert result == {
            "updates_available": True,
            "update_count": 2,
            "latest_commit": "Fix bug",
        }

    def test_perform_update_check_no_updates(self, monkeypatch):
        config = _clean_env_config(monkeypatch)
        config.set_check_for_updates(True)
        run_results = [
            MagicMock(returncode=0, stdout=""),
            MagicMock(returncode=0, stdout=""),
            MagicMock(returncode=0, stdout="0\n"),
        ]
        with patch(
            "chatty_commander.app.config.subprocess.run", side_effect=run_results
        ) as run_mock:
            result = config.perform_update_check()
        assert run_mock.call_count == 3
        assert result == {"updates_available": False, "update_count": 0}
