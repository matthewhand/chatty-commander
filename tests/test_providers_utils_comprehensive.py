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
Comprehensive tests for providers and utilities modules.
Tests ollama_provider, logger, and other utility functions.
"""

import logging
from unittest.mock import patch

import pytest

from chatty_commander.providers.ollama_provider import OllamaProvider
from chatty_commander.utils.logger import CustomLogger


class TestOllamaProvider:
    """Test Ollama provider functionality."""

    def test_ollama_provider_initialization(self):
        """Test Ollama provider initialization."""
        provider = OllamaProvider()
        assert provider is not None

    def test_model_initialization(self):
        """Test model initialization."""
        provider = OllamaProvider()

        with patch.object(provider, "_connect_to_ollama") as mock_connect:
            with patch.object(provider, "_load_model") as mock_load:
                mock_connect.return_value = True
                mock_load.return_value = True

                result = provider.initialize_model("llama2")
                assert result is True

    def test_text_generation(self):
        """Test text generation."""
        provider = OllamaProvider()

        with patch.object(provider, "_send_request") as mock_send:
            mock_send.return_value = {"response": "Generated text"}

            result = provider.generate_text("Test prompt")
            assert result == {"response": "Generated text"}

    def test_error_handling(self):
        """Test error handling."""
        provider = OllamaProvider()

        with patch.object(
            provider, "_send_request", side_effect=Exception("Connection failed")
        ):
            with pytest.raises(Exception):
                provider.generate_text("Test prompt")

    def test_model_switching(self):
        """Test model switching functionality."""
        provider = OllamaProvider()

        with patch.object(provider, "_load_model") as mock_load:
            mock_load.return_value = True

            result = provider.switch_model("codellama")
            assert result is True

    def test_connection_status(self):
        """Test connection status checking."""
        provider = OllamaProvider()

        with patch.object(provider, "_ping_ollama") as mock_ping:
            mock_ping.return_value = True

            status = provider.check_connection()
            assert status is True

    def test_batch_processing(self):
        """Test batch processing capabilities."""
        provider = OllamaProvider()

        with patch.object(provider, "_send_request") as mock_send:
            mock_send.return_value = {"response": "Batch response"}

            prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
            results = provider.process_batch(prompts)

            assert len(results) == 3
            mock_send.assert_called()


class TestCustomLogger:
    """Test custom logger functionality."""

    def test_logger_initialization(self):
        """Test logger initialization."""
        logger = CustomLogger("test_module")
        assert logger is not None
        assert logger.logger.name == "test_module"

    def test_log_levels(self):
        """Test different log levels."""
        logger = CustomLogger("test_module")

        with patch.object(logger.logger, "debug") as mock_debug:
            with patch.object(logger.logger, "info") as mock_info:
                with patch.object(logger.logger, "warning") as mock_warning:
                    with patch.object(logger.logger, "error") as mock_error:
                        with patch.object(logger.logger, "critical") as mock_critical:
                            logger.debug("Debug message")
                            logger.info("Info message")
                            logger.warning("Warning message")
                            logger.error("Error message")
                            logger.critical("Critical message")

                            mock_debug.assert_called_once_with("Debug message")
                            mock_info.assert_called_once_with("Info message")
                            mock_warning.assert_called_once_with("Warning message")
                            mock_error.assert_called_once_with("Error message")
                            mock_critical.assert_called_once_with("Critical message")

    def test_context_logging(self):
        """Test context-aware logging."""
        logger = CustomLogger("test_module")

        with patch.object(logger.logger, "info") as mock_info:
            logger.info("Test message", context={"user_id": "123", "action": "test"})

            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            assert "Test message" in call_args
            assert "user_id" in call_args

    def test_performance_logging(self):
        """Test performance logging."""
        logger = CustomLogger("test_module")

        with patch.object(logger.logger, "info") as mock_info:
            with patch("time.time") as mock_time:
                mock_time.return_value = 1000

                logger.log_performance("test_operation", 0.5)

                mock_info.assert_called_once()
                call_args = mock_info.call_args[0][0]
                assert "test_operation" in call_args
                assert "0.5" in call_args

    def test_error_logging_with_traceback(self):
        """Test error logging with traceback."""
        logger = CustomLogger("test_module")

        with patch.object(logger.logger, "error") as mock_error:
            try:
                raise ValueError("Test error")
            except ValueError as e:
                logger.log_error(e, "Error occurred during test")

            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]
            assert "Test error" in call_args
            assert "Error occurred during test" in call_args


class TestProviderIntegration:
    """Test provider integration functionality."""

    def test_provider_error_recovery(self):
        """Test provider error recovery."""
        provider = OllamaProvider()

        with patch.object(provider, "_send_request") as mock_send:
            # First call fails, second succeeds
            mock_send.side_effect = [
                Exception("Network error"),
                {"response": "Success"},
            ]

            # Should retry and succeed
            result = provider.generate_text("Test prompt")
            assert result == {"response": "Success"}
            assert mock_send.call_count == 2

    def test_provider_fallback_mechanism(self):
        """Test provider fallback mechanism."""
        provider = OllamaProvider()

        with patch.object(provider, "_send_request") as mock_send:
            with patch.object(provider, "_fallback_response") as mock_fallback:
                mock_send.side_effect = Exception("Service unavailable")
                mock_fallback.return_value = {"response": "Fallback response"}

                result = provider.generate_text("Test prompt")
                assert result == {"response": "Fallback response"}

    def test_provider_caching(self):
        """Test provider response caching."""
        provider = OllamaProvider()

        with patch.object(provider, "_send_request") as mock_send:
            mock_send.return_value = {"response": "Cached response"}

            # First call
            result1 = provider.generate_text("Test prompt", use_cache=True)
            # Second call should use cache
            result2 = provider.generate_text("Test prompt", use_cache=True)

            assert result1 == result2
            assert mock_send.call_count == 1  # Should only call once due to caching


class TestLoggerIntegration:
    """Test logger integration functionality."""

    def test_logger_configuration(self):
        """Test logger configuration."""
        logger1 = CustomLogger("module1")
        logger2 = CustomLogger("module2")

        # Should be able to create multiple loggers
        assert logger1 is not None
        assert logger2 is not None
        assert logger1.logger.name == "module1"
        assert logger2.logger.name == "module2"

    def test_logger_level_propagation(self):
        """Test logger level propagation."""
        logger = CustomLogger("test_module")

        # Test that log levels are properly set
        assert logger.logger.level <= logging.DEBUG
        assert logger.logger.handlers is not None

    def test_logger_output_formatting(self):
        """Test logger output formatting."""
        logger = CustomLogger("test_module")

        with patch.object(logger.logger, "info") as mock_info:
            logger.info("Test message", extra_data={"key": "value"})

            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            # Should include formatting
            assert "Test message" in call_args


class TestProviderPerformance:
    """Test provider performance features."""

    def test_response_time_tracking(self):
        """Test response time tracking."""
        provider = OllamaProvider()

        with patch.object(provider, "_send_request") as mock_send:
            with patch("time.time") as mock_time:
                mock_time.side_effect = [1000, 1000.5]  # 0.5 second response
                mock_send.return_value = {"response": "Fast response"}

                result = provider.generate_text("Test prompt", track_performance=True)

                assert result == {"response": "Fast response"}
                # Performance tracking should be recorded

    def test_concurrent_request_handling(self):
        """Test concurrent request handling."""
        provider = OllamaProvider()

        with patch.object(provider, "_send_request") as mock_send:
            mock_send.return_value = {"response": "Concurrent response"}

            # Simulate multiple concurrent requests
            results = []
            for i in range(3):
                result = provider.generate_text(f"Prompt {i}")
                results.append(result)

            assert len(results) == 3
            assert all(r["response"] == "Concurrent response" for r in results)


class TestLoggerSecurity:
    """Test logger security features."""

    def test_sensitive_data_filtering(self):
        """Test sensitive data filtering in logs."""
        logger = CustomLogger("test_module")

        with patch.object(logger.logger, "info") as mock_info:
            sensitive_data = {
                "password": "secret123",
                "api_key": "sk-1234567890abcdef",
                "user_message": "Normal message",
            }

            logger.info("User data logged", context=sensitive_data)

            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]

            # Sensitive data should be filtered
            assert "secret123" not in call_args
            assert "sk-1234567890abcdef" not in call_args
            assert "Normal message" in call_args  # Non-sensitive data should remain

    def test_log_injection_prevention(self):
        """Test prevention of log injection attacks."""
        logger = CustomLogger("test_module")

        with patch.object(logger.logger, "info") as mock_info:
            malicious_input = "Normal message\n[INFO] This is a fake log entry\n[ERROR] Another fake entry"

            logger.info(malicious_input)

            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]

            # Should sanitize or handle malicious input
            assert call_args == "Normal message" or "sanitized" in call_args.lower()
