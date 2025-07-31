"""
logger.py

Custom logging configuration for the ChattyCommander application. This module sets up
loggers that can be used across different parts of the application to ensure consistent
logging practices and easy maintenance.
"""

import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name, log_file, level=logging.INFO):
    """Set up a logger with a rotating file handler."""
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Ensure the directory for the log file exists
    directory = os.path.dirname(log_file)
    if not os.path.exists(directory):
        os.makedirs(directory)

    handler = RotatingFileHandler(log_file, maxBytes=1000000, backupCount=5)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

def report_error(e):
    logging.error(f"Error reported: {e}")

# Example usage within the application
# logger = setup_logger('main', 'logs/chattycommander.log')
# logger.info('Logger setup complete')