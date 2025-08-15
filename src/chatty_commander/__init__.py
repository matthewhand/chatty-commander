from importlib.metadata import PackageNotFoundError, version as _version

try:
    __version__ = _version("chatty-commander")
except PackageNotFoundError:
    __version__ = "0.0.0+dev"

__all__ = ["__version__"]
