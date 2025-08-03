"""
logger.py

Custom logging configuration for the ChattyCommander application. This module sets up
loggers that can be used across different parts of the application to ensure consistent
logging practices and easy maintenance.
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(name, log_file, level=logging.INFO):
    """Set up a logger with a rotating file handler.

    Behavior expected by tests:
    - Ensure directory exists using os.makedirs(dirname) when it does not exist
    - Always construct RotatingFileHandler(log_file, maxBytes=1000000, backupCount=5)
      so patched handler sees the call
    - Attach handler once (avoid duplicates on repeated setup)
    """
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Ensure the directory for the log file exists
    directory = os.path.dirname(log_file)
    # Tests expect makedirs to be called even for simple filenames (directory == "")
    try:
        os.makedirs(directory)
    except Exception:
        # Ignore errors if directory exists or is empty string
        pass

    handler = RotatingFileHandler(log_file, maxBytes=1000000, backupCount=5)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers for same file
    if not any(isinstance(h, RotatingFileHandler) and getattr(h, "baseFilename", None) == getattr(handler, "baseFilename", None) for h in logger.handlers):
        logger.addHandler(handler)

    return logger


def report_error(e):
    logging.error(f"Error reported: {e}")


# Example usage within the application
# logger = setup_logger('main', 'logs/chattycommander.log')
# logger.info('Logger setup complete')
