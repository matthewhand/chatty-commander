import logging

import pytest

from model_manager import load_model


# Dummy exception to simulate model load failure.
class DummyError(Exception):
    pass


# A fake onnx.load function that always fails.
def fake_onnx_load_failure(model_path):
    raise DummyError("Failed to load model")


# Test to simulate repeated failures and inspect logging diagnostics.
def test_model_loading_logging_retry(monkeypatch, caplog):
    try:
        import onnx
    except ImportError:
        pytest.skip("onnx not available")

    # Patch onnx.load to always raise an error.
    monkeypatch.setattr(onnx, "load", fake_onnx_load_failure)

    # Patch the centralized error-reporting function.
    error_reported = {"called": False}

    def fake_report_error(exc):
        error_reported["called"] = True

    monkeypatch.setattr("utils.logger.report_error", fake_report_error)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(Exception) as exc_info:
            load_model("path/to/model.onnx")

        # Confirm that the exception message indicates max retries exceeded.
        assert "Max retries exceeded" in str(exc_info.value)

    # Verify that detailed diagnostics were logged.
    logs = caplog.text
    assert "Failed to load model" in logs
    assert "path/to/model.onnx" in logs
    assert "retry" in logs

    # Verify that the error reporting function was called.
    assert error_reported["called"]
