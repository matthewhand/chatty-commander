"""ChattyCommander package.

Legacy modules previously lived at the repository root (e.g. ``from config import Config``).
Those shims have been removed; import from the package namespace instead. For convenience,
common classes are re-exported here.
"""

from .app.command_executor import CommandExecutor
from .app.config import Config
from .app.model_manager import ModelManager
from .app.state_manager import StateManager

__all__ = ["CommandExecutor", "Config", "ModelManager", "StateManager"]
