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

"""Config update behavior and update-check tests."""

from unittest.mock import MagicMock, patch

from chatty_commander.app.config import Config


def _new_config(monkeypatch):
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


def test_update_general_setting_initializes_general(monkeypatch):
    config = _new_config(monkeypatch)
    config.config_data.pop("general", None)

    config._update_general_setting("debug_mode", False)

    assert config.config_data["general"]["debug_mode"] is False


def test_set_check_for_updates_updates_config(monkeypatch):
    config = _new_config(monkeypatch)

    config.set_check_for_updates(0)
    assert config.check_for_updates is False
    assert config.config_data["general"]["check_for_updates"] is False

    config.set_check_for_updates(1)
    assert config.check_for_updates is True
    assert config.config_data["general"]["check_for_updates"] is True


def test_set_start_on_boot_calls_hooks(monkeypatch):
    config = _new_config(monkeypatch)

    with patch.object(config, "_enable_start_on_boot") as enable_mock, patch.object(
        config, "_disable_start_on_boot"
    ) as disable_mock:
        config.set_start_on_boot(True)
        enable_mock.assert_called_once()
        disable_mock.assert_not_called()
        assert config.start_on_boot is True
        assert config.config_data["general"]["start_on_boot"] is True

        config.set_start_on_boot(False)
        disable_mock.assert_called_once()
        assert config.start_on_boot is False
        assert config.config_data["general"]["start_on_boot"] is False


def test_perform_update_check_disabled(monkeypatch):
    config = _new_config(monkeypatch)
    config.set_check_for_updates(False)

    with patch("chatty_commander.app.config.subprocess.run") as run_mock:
        assert config.perform_update_check() is None
        run_mock.assert_not_called()


def test_perform_update_check_not_in_git_repo(monkeypatch):
    config = _new_config(monkeypatch)
    config.set_check_for_updates(True)

    mock_result = MagicMock(returncode=1, stdout="")
    with patch(
        "chatty_commander.app.config.subprocess.run", return_value=mock_result
    ) as run_mock:
        assert config.perform_update_check() is None
        assert run_mock.call_count == 1
        assert run_mock.call_args.args[0] == ["git", "rev-parse", "--git-dir"]


def test_perform_update_check_updates_available(monkeypatch):
    config = _new_config(monkeypatch)
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


def test_perform_update_check_no_updates(monkeypatch):
    config = _new_config(monkeypatch)
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
