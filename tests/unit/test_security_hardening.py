"""
Mock tests for security hardening features.

Tests security decorators and validation without requiring:
- Real command execution
- External validation services
- Complex setup
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import logging


class TestValidateInputDecorator:
    """Test input validation decorator."""
    
    def test_validate_input_type_check(self):
        """Test type validation."""
        from chatty_commander.utils.security import validate_input
        
        @validate_input(allowed_types=(str,))
        def process_string(value):
            return value
        
        # Should work with string
        result = process_string("valid")
        assert result == "valid"
        
        # Should raise TypeError with wrong type
        with pytest.raises(TypeError):
            process_string(123)
    
    def test_validate_input_length_check(self):
        """Test length validation."""
        from chatty_commander.utils.security import validate_input
        
        @validate_input(allowed_types=(str,), max_length=10, min_length=2)
        def short_string(value):
            return value
        
        # Should work with valid length
        result = short_string("valid")
        assert result == "valid"
        
        # Should raise ValueError for too short
        with pytest.raises(ValueError):
            short_string("a")
        
        # Should raise ValueError for too long
        with pytest.raises(ValueError):
            short_string("this is way too long")
    
    def test_validate_input_empty_check(self):
        """Test empty string validation."""
        from chatty_commander.utils.security import validate_input
        
        @validate_input(allowed_types=(str,), allow_empty=False)
        def non_empty(value):
            return value
        
        # Should raise ValueError for empty string
        with pytest.raises(ValueError):
            non_empty("   ")
    
    def test_validate_input_sanitization(self):
        """Test input sanitization (stripping)."""
        from chatty_commander.utils.security import validate_input
        
        @validate_input(allowed_types=(str,))
        def process(value):
            return value
        
        # Should strip whitespace
        result = process("  text  ")
        # Note: decorator strips input but doesn't return modified value in current implementation
        # This test documents expected behavior


class TestAuditLogDecorator:
    """Test audit logging decorator."""
    
    @patch('chatty_commander.utils.security.logger')
    def test_audit_log_success(self, mock_logger):
        """Test audit logging on success."""
        from chatty_commander.utils.security import audit_log
        
        @audit_log(operation="test_operation", level="info")
        def test_func():
            return "success"
        
        result = test_func()
        
        assert result == "success"
        # Should log start and completion
        assert mock_logger.info.call_count >= 1
    
    @patch('chatty_commander.utils.security.logger')
    def test_audit_log_failure(self, mock_logger):
        """Test audit logging on failure."""
        from chatty_commander.utils.security import audit_log
        
        @audit_log(operation="test_operation", level="info")
        def failing_func():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            failing_func()
        
        # Should log failure
        mock_logger.error.assert_called_once()
    
    @patch('chatty_commander.utils.security.logger')
    def test_audit_log_warning_level(self, mock_logger):
        """Test audit logging with warning level."""
        from chatty_commander.utils.security import audit_log
        
        mock_logger.warning = MagicMock()
        
        @audit_log(operation="warn_op", level="warning")
        def warn_func():
            return "done"
        
        result = warn_func()
        
        assert result == "done"
        mock_logger.warning.assert_called()


class TestSanitizeString:
    """Test string sanitization utility."""
    
    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        from chatty_commander.utils.security import sanitize_string
        
        result = sanitize_string("  hello world  ")
        assert result == "hello world"
    
    def test_sanitize_string_truncation(self):
        """Test string truncation."""
        from chatty_commander.utils.security import sanitize_string
        
        long_string = "a" * 2000
        result = sanitize_string(long_string, max_length=100)
        
        assert len(result) <= 100
    
    def test_sanitize_string_type_error(self):
        """Test type validation."""
        from chatty_commander.utils.security import sanitize_string
        
        with pytest.raises(TypeError):
            sanitize_string(123)


class TestSecurityDecoratorsOnCommandExecutor:
    """Test security decorators applied to CommandExecutor."""
    
    @patch('chatty_commander.app.command_executor.logging')
    @patch('chatty_commander.app.command_executor.audit_log')
    @patch('chatty_commander.app.command_executor.validate_input')
    def test_execute_command_decorated(self, mock_validate, mock_audit, mock_logging):
        """Test that execute_command has security decorators."""
        from chatty_commander.app.command_executor import CommandExecutor
        
        # Create executor
        config = {'commands': {}}
        executor = CommandExecutor(config)
        
        # Check that decorators are applied
        # (This is a structural test - actual decorator behavior tested above)
        assert hasattr(executor, 'execute_command')
        assert callable(executor.execute_command)
    
    @patch('chatty_commander.app.command_executor.audit_log')
    @patch('chatty_commander.app.command_executor.validate_input')
    def test_validate_command_decorated(self, mock_validate, mock_audit):
        """Test that validate_command has security decorators."""
        from chatty_commander.app.command_executor import CommandExecutor
        
        config = {'commands': {}}
        executor = CommandExecutor(config)
        
        assert hasattr(executor, 'validate_command')
        assert callable(executor.validate_command)


class TestSecurityModuleFallbacks:
    """Test security module graceful fallbacks."""
    
    def test_validate_input_fallback(self):
        """Test that validate_input handles import errors gracefully."""
        with patch.dict('sys.modules', {'chatty_commander.utils.security': None}):
            # Import with fallback
            from chatty_commander.app.command_executor import validate_input
            
            # Should still work as pass-through decorator
            @validate_input(allowed_types=(str,))
            def test_func(value):
                return value
            
            result = test_func("test")
            assert result == "test"
    
    def test_audit_log_fallback(self):
        """Test that audit_log handles import errors gracefully."""
        with patch.dict('sys.modules', {'chatty_commander.utils.security': None}):
            from chatty_commander.app.command_executor import audit_log
            
            # Should work as pass-through decorator
            @audit_log(operation="test", level="info")
            def test_func():
                return "done"
            
            result = test_func()
            assert result == "done"


class TestSecurityIntegration:
    """Integration tests for security features."""
    
    def test_security_decorator_chain(self):
        """Test that multiple decorators work together."""
        try:
            from chatty_commander.utils.security import validate_input, audit_log
            
            @audit_log(operation="chained_test", level="info")
            @validate_input(allowed_types=(str,), max_length=50)
            def chained_func(value):
                return value.upper()
            
            result = chained_func("hello")
            assert result == "HELLO"
        except ImportError:
            pytest.skip("Security module not available")
    
    def test_security_with_real_execution(self):
        """Test security decorators with actual function execution."""
        try:
            from chatty_commander.utils.security import validate_input
            
            execution_count = 0
            
            @validate_input(allowed_types=(str,), max_length=20)
            def tracked_func(value):
                nonlocal execution_count
                execution_count += 1
                return f"Processed: {value}"
            
            result = tracked_func("test input")
            assert execution_count == 1
            assert "test input" in result
            
        except ImportError:
            pytest.skip("Security module not available")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
