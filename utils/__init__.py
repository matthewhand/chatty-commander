# utils package shim to satisfy tests importing 'utils.logger'
# Re-export chatty_commander.utils.logger as utils.logger
try:
    from . import logger as logger  # This allows 'import utils.logger' to succeed
except Exception:
    # If the logger module isn't available yet, ignore; tests will import it explicitly.
    pass
