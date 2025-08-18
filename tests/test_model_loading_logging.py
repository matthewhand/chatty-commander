import logging

import pytest

from chatty_commander.app.model_manager import ModelManager


class DummyError(Exception):
    pass


class FailingModel:
    def __init__(self, path):  # pragma: no cover - simulated failure
        raise DummyError("Failed to load model")


def test_model_loading_logging_retry(monkeypatch, caplog, tmp_path):
    # Patch model class to always fail.
    monkeypatch.setattr(
        "chatty_commander.app.model_manager._get_patchable_model_class",
        lambda: FailingModel,
    )
    monkeypatch.setattr(
        "src.chatty_commander.app.model_manager._get_patchable_model_class",
        lambda: FailingModel,
        raising=False,
    )

    # Patch the centralized error-reporting function.
    error_reported = {"called": False}

    def fake_report_error(exc):
        error_reported["called"] = True

    monkeypatch.setattr("chatty_commander.utils.logger.report_error", fake_report_error)

    # Prevent __init__ from preloading models.
    monkeypatch.setattr(ModelManager, "reload_models", lambda *args, **kwargs: {})

    model_file = tmp_path / "model.onnx"
    model_file.write_text("dummy")

    class Config:
        def __init__(self):
            self.general_models_path = str(tmp_path)
            self.system_models_path = str(tmp_path)
            self.chat_models_path = str(tmp_path)

    mm = ModelManager(Config())

    with caplog.at_level(logging.ERROR):
        models = mm.load_model_set(str(tmp_path))

    assert models == {}

    logs = caplog.text
    assert "Failed to load model" in logs
    assert str(model_file) in logs
    assert "retry" in logs

    assert error_reported["called"]
