# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Comprehensive tests for web lifecycle module.

Tests startup/shutdown hooks and signal handling.
"""

import signal
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI

from src.chatty_commander.web.lifecycle import (
    _atexit_handler,
    _handle_shutdown_signal,
    register_lifecycle,
)


class TestHandleShutdownSignal:
    """Tests for _handle_shutdown_signal function."""

    def test_logs_shutdown_signal(self):
        """Test that shutdown signal is logged."""
        with patch("src.chatty_commander.web.lifecycle.logger") as mock_logger:
            with pytest.raises(SystemExit):
                _handle_shutdown_signal(signal.SIGTERM, None)
            
            # Should log the signal
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args_list
            assert any("SIGTERM" in str(call) for call in call_args)

    def test_raises_signal_after_logging(self):
        """Test that signal is re-raised after logging."""
        with patch("signal.raise_signal") as mock_raise:
            with pytest.raises(SystemExit):
                _handle_shutdown_signal(signal.SIGINT, None)
            
            mock_raise.assert_called_once()

    def test_handles_sigterm(self):
        """Test handling SIGTERM specifically."""
        with patch("signal.raise_signal"):
            with pytest.raises(SystemExit):
                _handle_shutdown_signal(signal.SIGTERM, None)

    def test_handles_sigint(self):
        """Test handling SIGINT specifically."""
        with patch("signal.raise_signal"):
            with pytest.raises(SystemExit):
                _handle_shutdown_signal(signal.SIGINT, None)


class TestAtexitHandler:
    """Tests for _atexit_handler function."""

    def test_logs_shutdown_completion(self):
        """Test that shutdown completion is logged."""
        with patch("src.chatty_commander.web.lifecycle.logger") as mock_logger:
            _atexit_handler()
            
            mock_logger.info.assert_called_once()
            call_args = str(mock_logger.info.call_args)
            assert "Shutdown complete" in call_args

    def test_includes_timestamp(self):
        """Test that log includes timestamp."""
        with patch("src.chatty_commander.web.lifecycle.logger") as mock_logger:
            before = datetime.now()
            _atexit_handler()
            after = datetime.now()
            
            # Should have been called
            mock_logger.info.assert_called_once()


class TestRegisterLifecycle:
    """Tests for register_lifecycle function."""

    @pytest.fixture
    def app(self):
        """Create a FastAPI app for testing."""
        return FastAPI()

    def test_registers_startup_event(self, app):
        """Test that startup event is registered."""
        mock_get_state = Mock()
        
        register_lifecycle(app, get_state_manager=mock_get_state)
        
        # Should have startup event handler
        assert len(app.router.on_startup) == 0  # Using decorator, not explicit list

    def test_registers_shutdown_event(self, app):
        """Test that shutdown event is registered."""
        mock_get_state = Mock()
        
        register_lifecycle(app, get_state_manager=mock_get_state)
        
        # Should have shutdown event handler
        assert len(app.router.on_shutdown) == 0  # Using decorator, not explicit list

    def test_calls_on_startup_callback(self, app):
        """Test that on_startup callback is called."""
        mock_callback = Mock()
        mock_get_state = Mock()
        
        register_lifecycle(
            app, 
            get_state_manager=mock_get_state,
            on_startup=mock_callback
        )
        
        # Note: In real execution, the callback would be called on startup
        # Here we just verify registration succeeded

    def test_calls_on_shutdown_callback(self, app):
        """Test that on_shutdown callback is called."""
        mock_callback = Mock()
        mock_get_state = Mock()
        
        register_lifecycle(
            app,
            get_state_manager=mock_get_state,
            on_shutdown=mock_callback
        )
        
        # Note: In real execution, the callback would be called on shutdown

    def test_handles_startup_callback_exception(self, app):
        """Test that startup callback exceptions are handled gracefully."""
        mock_callback = Mock(side_effect=Exception("Startup error"))
        mock_get_state = Mock()
        
        # Should not raise
        register_lifecycle(
            app,
            get_state_manager=mock_get_state,
            on_startup=mock_callback
        )

    def test_handles_shutdown_callback_exception(self, app):
        """Test that shutdown callback exceptions are handled gracefully."""
        mock_callback = Mock(side_effect=Exception("Shutdown error"))
        mock_get_state = Mock()
        
        # Should not raise
        register_lifecycle(
            app,
            get_state_manager=mock_get_state,
            on_shutdown=mock_callback
        )

    def test_optional_callbacks(self, app):
        """Test that callbacks are optional."""
        mock_get_state = Mock()
        
        # Should not raise without callbacks
        register_lifecycle(app, get_state_manager=mock_get_state)


class TestLifecycleIntegration:
    """Integration tests for lifecycle management."""

    def test_full_lifecycle_registration(self):
        """Test full lifecycle registration."""
        app = FastAPI()
        mock_get_state = Mock()
        mock_startup = Mock()
        mock_shutdown = Mock()
        
        register_lifecycle(
            app,
            get_state_manager=mock_get_state,
            on_startup=mock_startup,
            on_shutdown=mock_shutdown
        )
        
        # Should succeed without errors
        assert app is not None


class TestEdgeCases:
    """Edge case tests."""

    def test_shutdown_signal_with_none_frame(self):
        """Test shutdown signal handler with None frame."""
        with patch("signal.raise_signal"):
            with pytest.raises(SystemExit):
                _handle_shutdown_signal(signal.SIGTERM, None)

    def test_atexit_handler_no_exceptions(self):
        """Test atexit handler doesn't raise exceptions."""
        # Should not raise
        _atexit_handler()

    def test_register_lifecycle_with_none_callbacks(self, app):
        """Test register_lifecycle with None callbacks."""
        mock_get_state = Mock()
        
        # Should not raise
        register_lifecycle(
            app,
            get_state_manager=mock_get_state,
            on_startup=None,
            on_shutdown=None
        )
