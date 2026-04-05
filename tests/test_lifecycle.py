import pytest
from unittest.mock import Mock, patch
from chatty_commander.web.lifecycle import register_lifecycle, _handle_shutdown_signal, _atexit_handler
import signal
from fastapi import FastAPI

def test_handle_shutdown_signal():
    with patch("signal.signal") as mock_signal, \
         patch("signal.raise_signal") as mock_raise_signal:
        _handle_shutdown_signal(signal.SIGTERM, None)
        mock_signal.assert_called_once_with(signal.SIGTERM, signal.SIG_DFL)
        mock_raise_signal.assert_called_once_with(signal.SIGTERM)

def test_atexit_handler():
    # Just ensure it runs without error
    _atexit_handler()

@pytest.mark.asyncio
async def test_register_lifecycle():
    app = FastAPI()
    
    mock_startup = Mock()
    mock_shutdown = Mock()
    
    register_lifecycle(
        app,
        get_state_manager=Mock(),
        on_startup=mock_startup,
        on_shutdown=mock_shutdown
    )
    
    # Fastapi on_event is used, so we trigger startup/shutdown
    startup_handler = app.router.on_startup[0]
    shutdown_handler = app.router.on_shutdown[0]
    
    with patch("signal.signal"), patch("atexit.register"):
        await startup_handler()
        mock_startup.assert_called_once()
        
        await shutdown_handler()
        mock_shutdown.assert_called_once()

@pytest.mark.asyncio
async def test_register_lifecycle_exception():
    app = FastAPI()
    
    mock_startup = Mock(side_effect=ValueError("Test error"))
    mock_shutdown = Mock(side_effect=ValueError("Test error"))
    
    register_lifecycle(
        app,
        get_state_manager=Mock(),
        on_startup=mock_startup,
        on_shutdown=mock_shutdown
    )
    
    startup_handler = app.router.on_startup[0]
    shutdown_handler = app.router.on_shutdown[0]
    
    with patch("signal.signal"), patch("atexit.register"):
        # Should not raise
        await startup_handler()
        mock_startup.assert_called_once()
        
        await shutdown_handler()
        mock_shutdown.assert_called_once()
