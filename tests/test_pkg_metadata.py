import importlib
import re

def test_version_importable():
    mod = importlib.import_module("chatty_commander")
    assert hasattr(mod, "__version__")
    assert re.match(r"^\d+\.\d+\.\d+.*|0\.0\.0\+dev$", mod.__version__)

def test_cli_alias_exists():
    cli = importlib.import_module("chatty_commander.cli.cli")
    assert hasattr(cli, "main")
    assert hasattr(cli, "cli_main")
