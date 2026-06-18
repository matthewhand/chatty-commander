"""Tests for interface module."""


from chatty_commander.cli.interface import cli_main


class TestInterface:
    """Test interface functionality."""

    def test_imports(self):
        """Verify module imports."""
        assert cli_main is not None
