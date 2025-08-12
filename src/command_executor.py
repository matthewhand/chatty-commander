# Compatibility shim to preserve `from command_executor import CommandExecutor`
# Provide pyautogui and requests symbols for tests to patch, and lazily expose CommandExecutor
# to avoid circular import with chatty_commander.app.command_executor which imports this shim
# to read pyautogui/requests.

# Expose patch points first so app module can import them during its initialization
try:
    import pyautogui  # type: ignore
except Exception:  # noqa: BLE001 - broad to allow headless envs
    pyautogui = None  # type: ignore

try:
    import requests  # type: ignore
except Exception:  # noqa: BLE001
    requests = None  # type: ignore

__all__ = ["pyautogui", "requests"]


# Lazily load CommandExecutor to avoid circular import during app module init
def __getattr__(name: str):  # PEP 562
    if name == "CommandExecutor":
        import importlib

        m = importlib.import_module("chatty_commander.app.command_executor")
        return getattr(m, name)
    raise AttributeError(name)
