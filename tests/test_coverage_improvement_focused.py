"""Focused tests to improve coverage on specific high-impact modules."""

import logging
from unittest.mock import MagicMock, patch

import pytest
import requests

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager


class TestCoverageImprovementFocused:
    @pytest.fixture
    def config(self):
        config = Config()
        config.model_actions = {
            'test_keypress': {'action': 'keypress', 'keys': 'ctrl+c'},
            'test_url': {'action': 'url', 'url': 'http://example.com'},
            'test_custom': {'action': 'custom_message', 'message': 'Hello'},
            'test_invalid': {'action': 'invalid_action'},
        }
        return config

    @pytest.fixture
    def executor(self, config):
        model_manager = ModelManager(config)
        state_manager = StateManager()
        return CommandExecutor(config, model_manager, state_manager)

    # CommandExecutor Tests - Target specific missed lines
    def test_execute_keypress_with_shim_import_error(self, executor):
        """Test keypress execution when shim import fails"""
        with patch('builtins.__import__', side_effect=ImportError("No module")):
            with patch('chatty_commander.app.command_executor.pyautogui') as mock_pg:
                mock_pg.hotkey = MagicMock()

                result = executor.execute_command('test_keypress')

                assert result is True
                mock_pg.hotkey.assert_called_once_with('ctrl', 'c')

    def test_execute_keypress_pyautogui_none_error(self, executor):
        """Test keypress execution when pyautogui is None"""
        with patch('chatty_commander.app.command_executor.pyautogui', None):
            with patch('logging.error') as mock_log:
                result = executor.execute_command('test_keypress')

                assert result is False
                mock_log.assert_called()

    def test_execute_keypress_runtime_error_handling(self, executor):
        """Test keypress execution runtime error handling"""
        with patch('chatty_commander.app.command_executor.pyautogui') as mock_pg:
            mock_pg.hotkey.side_effect = RuntimeError("pyautogui not available")

            with patch('logging.error') as mock_log, patch('logging.critical') as mock_critical:
                result = executor.execute_command('test_keypress')

                assert result is False
                mock_critical.assert_called()

    def test_execute_url_request_exception(self, executor):
        """Test URL execution with request exception"""
        with patch('requests.get', side_effect=requests.RequestException("Connection failed")):
            with patch('logging.error') as mock_log, patch('logging.critical') as mock_critical:
                result = executor.execute_command('test_url')

                assert result is False
                mock_log.assert_called()
                mock_critical.assert_called()

    def test_execute_invalid_action_type(self, executor):
        """Test execution with invalid action type"""
        with patch('logging.error') as mock_log:
            result = executor.execute_command('test_invalid')

            assert result is False
            mock_log.assert_called()

    def test_execute_nonexistent_command_error(self, executor):
        """Test execution of nonexistent command"""
        with patch('logging.error') as mock_log:
            result = executor.execute_command('nonexistent_command')

            assert result is False
            mock_log.assert_called()

    def test_report_error_logging(self, executor):
        """Test report_error method logging"""
        with patch('logging.critical') as mock_log:
            executor.report_error('test_cmd', 'Test error message')

            mock_log.assert_called_once_with('Error in test_cmd: Test error message')

    def test_execute_keypress_with_list_keys(self, executor):
        """Test keypress execution with list of keys"""
        executor.config.model_actions['test_list'] = {'action': 'keypress', 'keys': ['ctrl', 'c']}

        with patch('chatty_commander.app.command_executor.pyautogui') as mock_pg:
            mock_pg.hotkey = MagicMock()

            result = executor.execute_command('test_list')

            assert result is True
            mock_pg.hotkey.assert_called_once_with('ctrl', 'c')

    def test_execute_keypress_single_key(self, executor):
        """Test keypress execution with single key"""
        executor.config.model_actions['test_single'] = {'action': 'keypress', 'keys': 'a'}

        with patch('chatty_commander.app.command_executor.pyautogui') as mock_pg:
            mock_pg.press = MagicMock()

            result = executor.execute_command('test_single')

            assert result is True
            mock_pg.press.assert_called_once_with('a')

    def test_execute_keypress_invalid_keys_type(self, executor):
        """Test keypress execution with invalid keys type"""
        executor.config.model_actions['test_invalid_keys'] = {'action': 'keypress', 'keys': 123}

        with patch('chatty_commander.app.command_executor.pyautogui') as mock_pg:
            with patch('logging.error') as mock_log:
                result = executor.execute_command('test_invalid_keys')

                assert result is False
                mock_log.assert_called()

    def test_execute_url_success_logging(self, executor):
        """Test URL execution success with logging"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            with patch('logging.info') as mock_log:
                result = executor.execute_command('test_url')

                assert result is True
                mock_get.assert_called_once_with('http://example.com', timeout=10)

    def test_execute_custom_message_logging(self, executor):
        """Test custom message execution with logging"""
        with patch('logging.info') as mock_log:
            result = executor.execute_command('test_custom')

            assert result is True
            mock_log.assert_called()

    # Voice Pipeline Tests - Basic coverage
    def test_voice_pipeline_initialization(self):
        """Test VoicePipeline initialization"""
        from chatty_commander.voice.pipeline import VoicePipeline

        pipeline = VoicePipeline()
        assert pipeline is not None

    def test_voice_pipeline_with_config(self):
        """Test VoicePipeline with config manager"""
        from chatty_commander.voice.pipeline import VoicePipeline

        mock_config = MagicMock()
        pipeline = VoicePipeline(config_manager=mock_config)
        assert pipeline is not None

    def test_voice_pipeline_with_executor(self):
        """Test VoicePipeline with command executor"""
        from chatty_commander.voice.pipeline import VoicePipeline

        mock_executor = MagicMock()
        pipeline = VoicePipeline(command_executor=mock_executor)
        assert pipeline is not None

    # Additional edge case tests
    def test_command_executor_edge_cases(self, executor):
        """Test command executor edge cases"""
        # Test empty command action
        executor.config.model_actions['empty'] = {}

        with patch('logging.error') as mock_log:
            result = executor.execute_command('empty')
            assert result is False
            mock_log.assert_called()

    # Additional coverage for missed lines in other modules
    def test_additional_coverage_scenarios(self):
        """Test additional coverage scenarios"""
        # Test Config module edge cases
        config = Config()

        # Test that config has expected attributes
        assert hasattr(config, 'model_actions')
        assert hasattr(config, 'inference_framework')

        # Test ModelManager initialization
        model_manager = ModelManager(config)
        assert model_manager.config == config

        # Test StateManager initialization
        state_manager = StateManager()
        assert state_manager is not None

    def test_logging_edge_cases(self):
        """Test logging edge cases"""
        from chatty_commander.utils.logger import setup_logger

        # Test logger setup with different configurations
        logger = setup_logger("test_logger")
        assert logger is not None

        # Test logger with custom config
        config = MagicMock()
        config.logging = {"level": "DEBUG", "format": "simple"}
        logger = setup_logger("test_debug", config=config)
        assert logger is not None

    def test_error_handling_edge_cases(self):
        """Test error handling edge cases"""
        from chatty_commander.utils.logger import report_error

        # Test error reporting with different error types
        error = ValueError("Test error")
        with patch('logging.error'):
            report_error(error)

        # Test error reporting with config
        config = MagicMock()
        with patch('logging.error'):
            report_error(error, config=config)
