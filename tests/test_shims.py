import pytest

def test_shims_import():
    import chatty_commander.config
    assert hasattr(chatty_commander.config, "Config")

    import chatty_commander.helpers
    
    import chatty_commander.model_manager
    assert hasattr(chatty_commander.model_manager, "ModelManager")
    
    import chatty_commander.config_cli
    
    import chatty_commander.command_executor
    assert hasattr(chatty_commander.command_executor, "CommandExecutor")

def test_compat():
    import chatty_commander.compat as compat
    import warnings
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Test loading a module with an alias
        module = compat.load("config")
        assert "Config" in dir(module)
        assert len(w) == 1
        assert "is deprecated" in str(w[-1].message)
        
    # Test expose
    namespace = {}
    compat.expose(namespace, "config")
    assert "Config" in namespace
    assert "__all__" in namespace
    assert isinstance(namespace["__all__"], list)

def test_compat_no_alias():
    import chatty_commander.compat as compat
    import warnings
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        module = compat.load("chatty_commander.app.config")
        assert "Config" in dir(module)
        assert len(w) == 0
