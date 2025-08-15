"""Utility helpers for application-wide logging configuration."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
import sys as _sys

# Ensure this module is also accessible as ``utils.logger`` so tests patching that path
# affect the same module object. This creates an alias in :mod:`sys.modules`.
_utils_mod = _sys.modules.setdefault("utils", _sys.modules.get("utils", type(_sys)("utils")))
_sys.modules["utils.logger"] = _sys.modules[__name__]
setattr(_utils_mod, "logger", _sys.modules[__name__])

class JSONFormatter(logging.Formatter):
    """Simple JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 - short
        log_record = {
            "time": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


class HTTPLogHandler(logging.Handler):
    """Log handler that POSTs logs to an HTTP endpoint."""

    def __init__(self, url: str, timeout: int = 5) -> None:
        super().__init__()
        self.url = url
        self.timeout = timeout
        try:  # pragma: no cover - network library optional
            import requests  # type: ignore
        except Exception:  # noqa: BLE001
            requests = None  # type: ignore
        self._requests = requests

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401 - short
        if not self._requests:
            return
        try:  # pragma: no cover - best effort
            data = self.format(record)
            headers = {"Content-Type": "application/json"}
            self._requests.post(self.url, data=data, headers=headers, timeout=self.timeout)
        except Exception:  # noqa: BLE001
            pass


def setup_logger(name, log_file=None, level=logging.INFO, config=None):
    """Set up a logger with configurable handlers.

    Parameters are kept backward compatible with the original implementation so that
    existing tests expecting ``setup_logger('name', 'file.log')`` still succeed. When a
    ``config`` object (``Config`` or duck-typed) providing a ``logging`` dictionary is
    supplied, the logger will honor the user-defined level, format, and destinations.
    """

    # Determine configuration
    log_cfg = getattr(config, "logging", {}) if config else {}
    level_name = log_cfg.get("level") if log_cfg else level
    level = getattr(logging, str(level_name).upper(), level)
    fmt = log_cfg.get("format", "plain")
    handlers = log_cfg.get("handlers")
    if handlers is None:
        handlers = ["file"] if log_file else ["console"]
    log_file = log_cfg.get("file", log_file)
    external_url = log_cfg.get("external_url")

    formatter = (
        JSONFormatter()
        if fmt.lower() == "json"
        else logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)

    def _handler_exists(new_handler: logging.Handler) -> bool:
        for h in list(logger.handlers):
            if type(h) is type(new_handler):
                if isinstance(h, RotatingFileHandler) and isinstance(new_handler, RotatingFileHandler):
                    if getattr(h, "baseFilename", None) == getattr(new_handler, "baseFilename", None):
                        return True
                else:
                    return True
        return False

    for dest in handlers:
        if dest == "console":
            handler = logging.StreamHandler()
        elif dest == "file" and log_file:
            directory = os.path.dirname(log_file)
            try:
                if not os.path.exists(directory):
                    os.makedirs(directory)
            except Exception:
                pass
            handler = RotatingFileHandler(log_file, maxBytes=1000000, backupCount=5)
        elif dest == "external" and external_url:
            handler = HTTPLogHandler(external_url)
        else:
            continue

        handler.setFormatter(formatter)
        if not _handler_exists(handler):
            logger.addHandler(handler)
    return logger


def report_error(e, config=None, context=None):
    """Log an error and optionally send telemetry or write diagnostics."""

    logging.error(f"Error reported: {e}")
    diagnostics = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "error": str(e),
    }
    if context:
        diagnostics["context"] = context

    log_cfg = getattr(config, "logging", {}) if config else {}
    telemetry_url = log_cfg.get("telemetry_url") or os.environ.get("CHATCOMM_TELEMETRY_URL")
    diag_file = log_cfg.get("diagnostics_file") or os.environ.get("CHATCOMM_DIAG_FILE")

    if telemetry_url:
        try:  # pragma: no cover - network best effort
            import requests  # type: ignore

            requests.post(telemetry_url, json=diagnostics, timeout=5)
        except Exception:  # noqa: BLE001
            logging.debug("Telemetry send failed", exc_info=True)

    if diag_file:
        try:
            directory = os.path.dirname(diag_file)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            with open(diag_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(diagnostics) + "\n")
        except Exception:  # pragma: no cover - best effort
            logging.debug("Writing diagnostics failed", exc_info=True)


# Example usage within the application
# logger = setup_logger('main', 'logs/chattycommander.log')
# logger.info('Logger setup complete')
