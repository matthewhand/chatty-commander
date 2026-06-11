"""Targeted coverage for chatty_commander.cli.cli helper functions and
cli_main dispatch branches that the existing CLI test files do not exercise.

Existing coverage lives in:
- tests/test_cli_features.py    -> cli_main dispatch (help/web/gui/config/shell) + list/exec
- tests/test_main_orchestrator.py -> run_orchestrator_mode + build_advisor_sink

This file fills the gaps: run_cli_mode, run_web_mode, run_gui_mode,
run_interactive_shell, _detect_action_type edge cases, and a handful of
cli_main argument-validation / env-override branches. All heavy side effects
(model loading, server start, signal handlers, GUI launchers) are patched so
tests are hermetic and fast.
"""

from __future__ import annotations

import io
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

# Mock openwakeword the same way the other CLI test modules do, so importing
# the app stack underneath cli does not fail in CI.
sys.modules.setdefault("openwakeword", types.ModuleType("openwakeword"))
_owm = types.ModuleType("openwakeword.model")
_owm.Model = type("Model", (), {})
sys.modules.setdefault("openwakeword.model", _owm)

from chatty_commander.cli import cli as cli_mod  # noqa: E402
from chatty_commander.cli.cli import (  # noqa: E402
    _detect_action_type,
    run_cli_mode,
    run_gui_mode,
    run_interactive_shell,
    run_web_mode,
)

# ── _detect_action_type ──────────────────────────────────────────────────


class TestDetectActionType:
    def test_dict_keypress(self):
        assert _detect_action_type({"keypress": "ctrl+c"}) == "keypress"

    def test_dict_shell_and_url(self):
        assert _detect_action_type({"shell": {}}) == "shell"
        assert _detect_action_type({"url": "http://x"}) == "url"

    def test_dict_unknown(self):
        assert _detect_action_type({"mystery": 1}) == "unknown"

    def test_string_heuristic(self):
        assert _detect_action_type("open url please") == "url"
        assert _detect_action_type("run shell thing") == "shell"
        assert _detect_action_type("keypress ctrl") == "keypress"

    def test_string_unknown(self):
        assert _detect_action_type("just words") == "unknown"

    def test_non_dict_non_str(self):
        assert _detect_action_type(42) == "unknown"
        assert _detect_action_type(None) == "unknown"


# ── run_cli_mode ─────────────────────────────────────────────────────────


def _logger():
    return MagicMock()


class _Config:
    def __init__(self, actions=None):
        self.model_actions = actions or {}
        self.web_server = {}
        self.advisors = {"enabled": False}


class TestRunCliMode:
    def test_loop_processes_command_and_executes_action(self, monkeypatch):
        """One actionable command, then signal flips the shutdown flag."""
        logger = _logger()
        config = _Config({"hello": {"shell": {}}})

        mm = MagicMock()
        sm = MagicMock()
        sm.current_state = "idle"
        ce = MagicMock()

        # Capture the registered signal handlers so we can trigger graceful
        # shutdown deterministically instead of relying on real signals.
        handlers = {}
        monkeypatch.setattr(
            cli_mod.signal,
            "signal",
            lambda signum, handler: handlers.setdefault(signum, handler),
        )

        # update_state both reports a transition and flips the shutdown flag
        # so the loop runs exactly one full iteration.
        def update_then_stop(cmd):
            handlers[cli_mod.signal.SIGINT](cli_mod.signal.SIGINT, None)
            return "active"

        sm.update_state.side_effect = update_then_stop
        mm.listen_for_commands.return_value = "hello"

        with pytest.raises(SystemExit) as exc:
            run_cli_mode(config, mm, sm, ce, logger)
        assert exc.value.code == 0

        mm.reload_models.assert_any_call("idle")
        mm.reload_models.assert_any_call("active")
        ce.execute_command.assert_called_once_with("hello")
        mm.shutdown.assert_called_once()
        sm.shutdown.assert_called_once()

    def test_empty_command_continues_then_shutdown(self, monkeypatch):
        logger = _logger()
        config = _Config({})
        mm = MagicMock()
        sm = MagicMock()
        sm.current_state = "idle"
        ce = MagicMock()

        handlers = {}
        monkeypatch.setattr(
            cli_mod.signal,
            "signal",
            lambda signum, handler: handlers.setdefault(signum, handler),
        )

        seq = ["", None]

        def fake_listen():
            if seq:
                val = seq.pop(0)
                if not seq:
                    handlers[cli_mod.signal.SIGINT](cli_mod.signal.SIGINT, None)
                return val
            return None

        mm.listen_for_commands.side_effect = fake_listen

        with pytest.raises(SystemExit):
            run_cli_mode(config, mm, sm, ce, logger)
        ce.execute_command.assert_not_called()

    def test_inner_exception_logged_and_loop_survives(self, monkeypatch):
        logger = _logger()
        config = _Config({})
        mm = MagicMock()
        sm = MagicMock()
        sm.current_state = "idle"
        ce = MagicMock()

        handlers = {}
        monkeypatch.setattr(
            cli_mod.signal,
            "signal",
            lambda signum, handler: handlers.setdefault(signum, handler),
        )

        state = {"n": 0}

        def fake_listen():
            state["n"] += 1
            if state["n"] == 1:
                raise RuntimeError("transient")
            handlers[cli_mod.signal.SIGTERM](cli_mod.signal.SIGTERM, None)
            return None

        mm.listen_for_commands.side_effect = fake_listen

        with pytest.raises(SystemExit):
            run_cli_mode(config, mm, sm, ce, logger)
        assert any(
            "Error while processing command loop" in str(c)
            for c in logger.error.call_args_list
        )

    def test_shutdown_cleanup_errors_are_swallowed(self, monkeypatch):
        logger = _logger()
        config = _Config({})
        # model_manager.shutdown raises; finally block must catch and exit(0).
        mm = MagicMock()
        mm.shutdown.side_effect = RuntimeError("cleanup boom")
        sm = MagicMock()
        sm.current_state = "idle"
        ce = MagicMock()

        handlers = {}
        monkeypatch.setattr(
            cli_mod.signal,
            "signal",
            lambda signum, handler: handlers.setdefault(signum, handler),
        )

        def fake_listen():
            handlers[cli_mod.signal.SIGINT](cli_mod.signal.SIGINT, None)
            return None

        mm.listen_for_commands.side_effect = fake_listen

        with pytest.raises(SystemExit) as exc:
            run_cli_mode(config, mm, sm, ce, logger)
        assert exc.value.code == 0
        assert any(
            "Error during shutdown" in str(c) for c in logger.error.call_args_list
        )


# ── run_web_mode ─────────────────────────────────────────────────────────


class TestRunWebMode:
    def _patch_web(self, monkeypatch, server=None):
        """Install a fake WebModeServer + no-op env validation + no-op signals."""
        fake_server = server or MagicMock()
        fake_module = types.ModuleType("chatty_commander.web.web_mode")
        fake_module.WebModeServer = MagicMock(return_value=fake_server)
        monkeypatch.setitem(
            sys.modules, "chatty_commander.web.web_mode", fake_module
        )
        monkeypatch.setattr(
            cli_mod.signal, "signal", lambda *a, **k: None
        )
        return fake_server, fake_module

    def test_import_error_exits_1(self, monkeypatch):
        # Force the lazy import to raise ImportError.
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *a, **k):
            if name == "chatty_commander.web.web_mode":
                raise ImportError("no fastapi")
            return real_import(name, *a, **k)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        logger = _logger()
        with pytest.raises(SystemExit) as exc:
            run_web_mode(_Config(), MagicMock(), MagicMock(), MagicMock(), logger)
        assert exc.value.code == 1
        logger.error.assert_called()

    def test_happy_path_runs_server_and_shuts_down(self, monkeypatch):
        server, _ = self._patch_web(monkeypatch)
        # Patch env validation to a no-op.
        env_mod = types.ModuleType("chatty_commander.app.env_validation")
        env_mod.EnvValidationError = type("EnvValidationError", (Exception,), {})
        env_mod.validate_startup_env = MagicMock()
        monkeypatch.setitem(
            sys.modules, "chatty_commander.app.env_validation", env_mod
        )
        logger = _logger()
        mm = MagicMock()
        sm = MagicMock()
        ce = MagicMock()

        run_web_mode(_Config(), mm, sm, ce, logger, host="1.2.3.4", port=9000)

        server.run.assert_called_once_with(host="1.2.3.4", port=9000)
        mm.add_command_callback.assert_called_once()
        sm.add_state_change_callback.assert_called_once()
        mm.shutdown.assert_called_once()
        sm.shutdown.assert_called_once()

    def test_no_auth_disables_auth_in_dict_config(self, monkeypatch):
        server, _ = self._patch_web(monkeypatch)
        env_mod = types.ModuleType("chatty_commander.app.env_validation")
        env_mod.EnvValidationError = type("EnvValidationError", (Exception,), {})
        env_mod.validate_startup_env = MagicMock()
        monkeypatch.setitem(
            sys.modules, "chatty_commander.app.env_validation", env_mod
        )
        config = _Config()
        config.web_server = {"auth_enabled": True}
        run_web_mode(
            config, MagicMock(), MagicMock(), MagicMock(), _logger(), no_auth=True
        )
        assert config.web_server["auth_enabled"] is False

    def test_env_validation_error_exits_1(self, monkeypatch):
        self._patch_web(monkeypatch)
        err_cls = type("EnvValidationError", (Exception,), {})
        env_mod = types.ModuleType("chatty_commander.app.env_validation")
        env_mod.EnvValidationError = err_cls

        def _raise(*a, **k):
            raise err_cls("missing OPENAI_API_KEY")

        env_mod.validate_startup_env = _raise
        monkeypatch.setitem(
            sys.modules, "chatty_commander.app.env_validation", env_mod
        )
        logger = _logger()
        stderr = io.StringIO()
        monkeypatch.setattr(sys, "stderr", stderr)
        with pytest.raises(SystemExit) as exc:
            run_web_mode(_Config(), MagicMock(), MagicMock(), MagicMock(), logger)
        assert exc.value.code == 1
        assert "missing OPENAI_API_KEY" in stderr.getvalue()

    def test_env_host_port_and_log_level_overrides(self, monkeypatch):
        server, _ = self._patch_web(monkeypatch)
        env_mod = types.ModuleType("chatty_commander.app.env_validation")
        env_mod.EnvValidationError = type("EnvValidationError", (Exception,), {})
        env_mod.validate_startup_env = MagicMock()
        monkeypatch.setitem(
            sys.modules, "chatty_commander.app.env_validation", env_mod
        )
        monkeypatch.setenv("CHATCOMM_HOST", "10.0.0.1")
        monkeypatch.setenv("CHATCOMM_PORT", "7777")
        monkeypatch.setenv("CHATCOMM_LOG_LEVEL", "DEBUG")
        logger = MagicMock()
        run_web_mode(
            _Config(), MagicMock(), MagicMock(), MagicMock(), logger,
            host="0.0.0.0", port=8100,
        )
        server.run.assert_called_once_with(host="10.0.0.1", port=7777)
        logger.setLevel.assert_called()  # DEBUG applied

    def test_invalid_env_port_warns_and_keeps_default(self, monkeypatch):
        server, _ = self._patch_web(monkeypatch)
        env_mod = types.ModuleType("chatty_commander.app.env_validation")
        env_mod.EnvValidationError = type("EnvValidationError", (Exception,), {})
        env_mod.validate_startup_env = MagicMock()
        monkeypatch.setitem(
            sys.modules, "chatty_commander.app.env_validation", env_mod
        )
        monkeypatch.setenv("CHATCOMM_PORT", "not-a-number")
        logger = MagicMock()
        run_web_mode(
            _Config(), MagicMock(), MagicMock(), MagicMock(), logger,
            host="0.0.0.0", port=8100,
        )
        server.run.assert_called_once_with(host="0.0.0.0", port=8100)
        assert any(
            "Invalid CHATCOMM_PORT" in str(c) for c in logger.warning.call_args_list
        )

    def test_invalid_env_log_level_warns(self, monkeypatch):
        server, _ = self._patch_web(monkeypatch)
        env_mod = types.ModuleType("chatty_commander.app.env_validation")
        env_mod.EnvValidationError = type("EnvValidationError", (Exception,), {})
        env_mod.validate_startup_env = MagicMock()
        monkeypatch.setitem(
            sys.modules, "chatty_commander.app.env_validation", env_mod
        )
        monkeypatch.setenv("CHATCOMM_LOG_LEVEL", "BOGUS")
        logger = MagicMock()
        run_web_mode(
            _Config(), MagicMock(), MagicMock(), MagicMock(), logger,
            host="0.0.0.0", port=8100,
        )
        assert any(
            "Invalid CHATCOMM_LOG_LEVEL" in str(c)
            for c in logger.warning.call_args_list
        )

    def test_run_error_still_runs_shutdown_cleanup(self, monkeypatch):
        server = MagicMock()
        server.run.side_effect = RuntimeError("server crashed")
        self._patch_web(monkeypatch, server=server)
        env_mod = types.ModuleType("chatty_commander.app.env_validation")
        env_mod.EnvValidationError = type("EnvValidationError", (Exception,), {})
        env_mod.validate_startup_env = MagicMock()
        monkeypatch.setitem(
            sys.modules, "chatty_commander.app.env_validation", env_mod
        )
        mm = MagicMock()
        with pytest.raises(RuntimeError):
            run_web_mode(_Config(), mm, MagicMock(), MagicMock(), _logger())
        # finally still ran shutdown
        mm.shutdown.assert_called_once()


# ── run_gui_mode ─────────────────────────────────────────────────────────


class TestRunGuiMode:
    def test_no_gui_returns_0(self):
        assert (
            run_gui_mode(_Config(), MagicMock(), MagicMock(), MagicMock(), _logger(),
                         no_gui=True)
            == 0
        )

    def test_headless_posix_skips(self, monkeypatch):
        monkeypatch.setattr(cli_mod.os, "name", "posix")
        monkeypatch.delenv("DISPLAY", raising=False)
        logger = MagicMock()
        rc = run_gui_mode(_Config(), MagicMock(), MagicMock(), MagicMock(), logger)
        assert rc == 0
        logger.warning.assert_called()

    def test_display_override_applied(self, monkeypatch):
        monkeypatch.setattr(cli_mod.os, "name", "posix")
        monkeypatch.delenv("DISPLAY", raising=False)
        # With a display override set but no real avatar GUI, the avatar import
        # will fail and fall through; we only assert DISPLAY got set and an int
        # is returned.
        rc = run_gui_mode(
            _Config(), MagicMock(), MagicMock(), MagicMock(), MagicMock(),
            display_override=":99",
        )
        assert cli_mod.os.environ.get("DISPLAY") == ":99"
        assert isinstance(rc, int)

    def test_avatar_gui_success(self, monkeypatch):
        monkeypatch.setattr(cli_mod.os, "name", "posix")
        monkeypatch.setenv("DISPLAY", ":0")
        avatar_mod = types.ModuleType("chatty_commander.avatars.avatar_gui")
        avatar_mod.run_avatar_gui = MagicMock(return_value=None)
        monkeypatch.setitem(
            sys.modules, "chatty_commander.avatars.avatar_gui", avatar_mod
        )
        rc = run_gui_mode(_Config(), MagicMock(), MagicMock(), MagicMock(), _logger())
        assert rc == 0
        avatar_mod.run_avatar_gui.assert_called_once()

    def test_avatar_gui_returns_code(self, monkeypatch):
        monkeypatch.setattr(cli_mod.os, "name", "posix")
        monkeypatch.setenv("DISPLAY", ":0")
        avatar_mod = types.ModuleType("chatty_commander.avatars.avatar_gui")
        avatar_mod.run_avatar_gui = MagicMock(return_value=3)
        monkeypatch.setitem(
            sys.modules, "chatty_commander.avatars.avatar_gui", avatar_mod
        )
        rc = run_gui_mode(_Config(), MagicMock(), MagicMock(), MagicMock(), _logger())
        assert rc == 3

    def test_falls_back_to_tray_popup(self, monkeypatch):
        monkeypatch.setattr(cli_mod.os, "name", "posix")
        monkeypatch.setenv("DISPLAY", ":0")
        # avatar + pyqt5 both raise on import -> tray popup path.
        avatar_mod = types.ModuleType("chatty_commander.avatars.avatar_gui")

        def _avatar_boom():
            raise RuntimeError("no webview")

        avatar_mod.run_avatar_gui = _avatar_boom
        monkeypatch.setitem(
            sys.modules, "chatty_commander.avatars.avatar_gui", avatar_mod
        )

        pyqt_mod = types.ModuleType("chatty_commander.gui.pyqt5_avatar")

        def _pyqt_boom():
            raise RuntimeError("no pyqt")

        pyqt_mod.run_pyqt5_avatar = _pyqt_boom
        monkeypatch.setitem(
            sys.modules, "chatty_commander.gui.pyqt5_avatar", pyqt_mod
        )

        tray_mod = types.ModuleType("chatty_commander.gui.tray_popup")
        tray_mod.run_tray_popup = MagicMock(return_value=None)
        monkeypatch.setitem(
            sys.modules, "chatty_commander.gui.tray_popup", tray_mod
        )

        rc = run_gui_mode(_Config(), MagicMock(), MagicMock(), MagicMock(), _logger())
        assert rc == 0
        tray_mod.run_tray_popup.assert_called_once()


# ── run_interactive_shell ────────────────────────────────────────────────


def _feed_inputs(monkeypatch, lines):
    it = iter(lines)

    def fake_input(prompt=""):
        try:
            return next(it)
        except StopIteration as exc:
            raise EOFError from exc

    monkeypatch.setattr("builtins.input", fake_input)


class TestRunInteractiveShell:
    def _patch_readline(self, monkeypatch):
        fake_readline = types.ModuleType("readline")
        fake_readline.set_completer = MagicMock()
        fake_readline.parse_and_bind = MagicMock()
        monkeypatch.setitem(sys.modules, "readline", fake_readline)
        return fake_readline

    def test_help_state_models_and_exit(self, monkeypatch, capsys):
        self._patch_readline(monkeypatch)
        config = _Config({"foo": {"shell": {}}})
        sm = MagicMock()
        sm.current_state = "idle"
        mm = MagicMock()
        mm.models = {"general": {"m1": object()}, "system": {}}
        _feed_inputs(monkeypatch, ["", "help", "state", "models", "exit"])
        run_interactive_shell(config, mm, sm, MagicMock(), MagicMock())
        out = capsys.readouterr().out
        assert "Available commands: help, exit" in out
        assert "Current state: idle" in out
        assert "Loaded models: m1" in out

    def test_execute_known_and_unknown(self, monkeypatch, capsys):
        self._patch_readline(monkeypatch)
        config = _Config({"foo": {"shell": {}}})
        sm = MagicMock()
        ce = MagicMock()
        mm = MagicMock()
        mm.models = {}
        _feed_inputs(
            monkeypatch, ["execute foo", "execute nope", "exit"]
        )
        run_interactive_shell(config, mm, sm, ce, MagicMock())
        out = capsys.readouterr().out
        ce.execute_command.assert_called_once_with("foo")
        assert "Executed: foo" in out
        assert "Unknown command: nope" in out

    def test_execute_known_raises_prints_error(self, monkeypatch, capsys):
        self._patch_readline(monkeypatch)
        config = _Config({"foo": {"shell": {}}})
        ce = MagicMock()
        ce.execute_command.side_effect = RuntimeError("kaboom")
        mm = MagicMock()
        mm.models = {}
        _feed_inputs(monkeypatch, ["execute foo", "exit"])
        run_interactive_shell(config, mm, MagicMock(), ce, MagicMock())
        out = capsys.readouterr().out
        assert "Error executing 'foo': kaboom" in out

    def test_voice_simulation_transitions_and_executes(self, monkeypatch, capsys):
        self._patch_readline(monkeypatch)
        config = _Config({"hello": {"shell": {}}})
        sm = MagicMock()
        sm.update_state.return_value = "active"
        mm = MagicMock()
        mm.models = {}
        ce = MagicMock()
        _feed_inputs(monkeypatch, ["hello", "exit"])
        run_interactive_shell(config, mm, sm, ce, MagicMock())
        sm.update_state.assert_called_with("hello")
        mm.reload_models.assert_called_with("active")
        ce.execute_command.assert_called_once_with("hello")

    def test_voice_simulation_execute_error(self, monkeypatch, capsys):
        self._patch_readline(monkeypatch)
        config = _Config({"hello": {"shell": {}}})
        sm = MagicMock()
        sm.update_state.return_value = None
        mm = MagicMock()
        mm.models = {}
        ce = MagicMock()
        ce.execute_command.side_effect = RuntimeError("bad")
        _feed_inputs(monkeypatch, ["hello", "exit"])
        run_interactive_shell(config, mm, sm, ce, MagicMock())
        assert "Error executing 'hello': bad" in capsys.readouterr().out

    def test_eof_terminates_loop(self, monkeypatch):
        self._patch_readline(monkeypatch)
        config = _Config({})
        mm = MagicMock()
        mm.models = {}
        _feed_inputs(monkeypatch, [])  # immediate EOFError
        # Should return cleanly without raising.
        run_interactive_shell(config, mm, MagicMock(), MagicMock(), MagicMock())

    def test_completer_logic(self, monkeypatch):
        """Exercise the tab-completer closure set via readline.set_completer."""
        fake_readline = self._patch_readline(monkeypatch)
        config = _Config({"alpha": {"shell": {}}, "beta": {"url": "u"}})
        mm = MagicMock()
        mm.models = {}
        _feed_inputs(monkeypatch, ["exit"])
        run_interactive_shell(config, mm, MagicMock(), MagicMock(), MagicMock())

        completer = fake_readline.set_completer.call_args[0][0]
        # Top-level commands starting with 'e' -> 'execute', 'exit'
        first = completer("e", 0)
        assert first in ("execute", "exit")
        # Exhausted -> None
        assert completer("zzz", 0) is None
        # 'execute ' subcompletion over model_actions
        assert completer("execute al", 0) == "execute alpha"
        assert completer("execute al", 5) is None


# ── cli_main argument validation branches ────────────────────────────────


class _DummyConfig:
    def __init__(self):
        self.model_actions = {}
        self.web_server = {}
        self.advisors = {"enabled": False}


def _install_light_app(monkeypatch):
    """Patch cli_main's lazily-resolved heavy deps with light fakes."""
    monkeypatch.setattr(cli_mod, "Config", lambda: _DummyConfig())
    monkeypatch.setattr(cli_mod, "ModelManager", lambda *a, **k: MagicMock())
    monkeypatch.setattr(cli_mod, "StateManager", lambda *a, **k: MagicMock())
    monkeypatch.setattr(cli_mod, "CommandExecutor", lambda *a, **k: MagicMock())
    monkeypatch.setattr(cli_mod, "generate_default_config_if_needed", lambda: False)


def _run_main(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", ["chatty-commander"] + argv)
    stdout, stderr = io.StringIO(), io.StringIO()
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)
    try:
        code = cli_mod.cli_main()
    except SystemExit as e:
        code = int(e.code) if e.code is not None else 0
    return code, stdout.getvalue(), stderr.getvalue()


class TestCliMainArgValidation:
    def test_low_port_with_web_errors(self, monkeypatch):
        # parser.error -> SystemExit(2)
        code, _out, err = _run_main(monkeypatch, ["--web", "--port", "80"])
        assert code == 2
        assert "Port must be 1024 or higher" in err

    def test_no_auth_without_web_errors(self, monkeypatch):
        code, _out, err = _run_main(monkeypatch, ["--no-auth"])
        assert code == 2
        assert "--no-auth only applicable in web mode" in err

    def test_orchestrate_dispatch(self, monkeypatch):
        _install_light_app(monkeypatch)
        # skip AI core + env validation by going through orchestrate path,
        # but env validation still runs for non-config; patch it to no-op.
        env_mod = types.ModuleType("chatty_commander.app.env_validation")
        env_mod.EnvValidationError = type("EnvValidationError", (Exception,), {})
        env_mod.validate_startup_env = MagicMock()
        monkeypatch.setitem(
            sys.modules, "chatty_commander.app.env_validation", env_mod
        )
        # Skip AI core import.
        monkeypatch.setattr(
            cli_mod, "run_orchestrator_mode", lambda *a, **k: 0
        )
        with patch(
            "chatty_commander.ai.create_intelligence_core",
            side_effect=Exception("no ai"),
        ):
            code, out, _err = _run_main(
                monkeypatch, ["--orchestrate", "--test-mode"]
            )
        assert code == 0

    def test_shell_dispatch(self, monkeypatch):
        _install_light_app(monkeypatch)
        env_mod = types.ModuleType("chatty_commander.app.env_validation")
        env_mod.EnvValidationError = type("EnvValidationError", (Exception,), {})
        env_mod.validate_startup_env = MagicMock()
        monkeypatch.setitem(
            sys.modules, "chatty_commander.app.env_validation", env_mod
        )
        with patch.object(cli_mod, "run_interactive_shell") as shell:
            code, _o, _e = _run_main(monkeypatch, ["--shell", "--test-mode"])
        assert code == 0
        shell.assert_called_once()

    def test_env_validation_failure_returns_1(self, monkeypatch):
        _install_light_app(monkeypatch)
        err_cls = type("EnvValidationError", (Exception,), {})
        env_mod = types.ModuleType("chatty_commander.app.env_validation")
        env_mod.EnvValidationError = err_cls

        def _raise(*a, **k):
            raise err_cls("OPENAI_API_KEY required")

        env_mod.validate_startup_env = _raise
        monkeypatch.setitem(
            sys.modules, "chatty_commander.app.env_validation", env_mod
        )
        code, _o, err = _run_main(monkeypatch, ["--shell", "--test-mode"])
        assert code == 1
        assert "OPENAI_API_KEY required" in err

    def test_default_cli_mode_dispatch(self, monkeypatch):
        _install_light_app(monkeypatch)
        env_mod = types.ModuleType("chatty_commander.app.env_validation")
        env_mod.EnvValidationError = type("EnvValidationError", (Exception,), {})
        env_mod.validate_startup_env = MagicMock()
        monkeypatch.setitem(
            sys.modules, "chatty_commander.app.env_validation", env_mod
        )
        # Provide a non-mode arg so interactive_mode is False and we reach the
        # default run_cli_mode branch.
        with patch.object(cli_mod, "run_cli_mode") as cli_run:
            code, _o, _e = _run_main(
                monkeypatch, ["--log-level", "DEBUG", "--test-mode"]
            )
        assert code == 0
        cli_run.assert_called_once()
