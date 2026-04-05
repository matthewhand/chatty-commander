import pytest
import warnings

def test_cli_interface_shim():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        import chatty_commander.cli.interface as interface
        assert "cli_main" in dir(interface)
        assert len(w) == 1
        assert "is a legacy shim" in str(w[-1].message)

def test_cli_shim():
    import chatty_commander.cli.shim as shim
    assert "create_parser" in dir(shim)
    assert "run_orchestrator_mode" in dir(shim)

def test_main_shim():
    import chatty_commander.__main__
    assert "main" in dir(chatty_commander.__main__)
