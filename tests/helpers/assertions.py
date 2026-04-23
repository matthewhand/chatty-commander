# helpers/assertions.py
"""Shared assertion helpers for common test patterns."""

import json
from typing import Any


class TestAssertions:
    """Custom assertion helpers for cleaner tests."""
    
    @staticmethod
    def assert_valid_json_response(response, expected_keys=None, status_code=200):
        """
        Assert that a response is valid JSON with expected structure.
        
        Args:
            response: HTTP response object
            expected_keys: List of keys that must be present
            status_code: Expected HTTP status code
            
        Returns:
            Parsed JSON data
        """
        assert response.status_code == status_code, (
            f"Expected status {status_code}, got {response.status_code}"
        )
        
        data = response.json()
        assert isinstance(data, dict), f"Response is not a dict: {type(data)}"
        
        if expected_keys:
            missing = [key for key in expected_keys if key not in data]
            assert not missing, f"Missing keys in response: {missing}"
        
        return data
    
    @staticmethod
    def assert_error_response(response, expected_status, error_substring=None):
        """
        Assert that a response is an error with expected characteristics.
        
        Args:
            response: HTTP response object
            expected_status: Expected error status code
            error_substring: String that should appear in error message
        """
        assert response.status_code == expected_status, (
            f"Expected error status {expected_status}, got {response.status_code}"
        )
        
        data = response.json()
        assert "error" in data or "detail" in data or "message" in data, (
            "Error response missing error field"
        )
        
        if error_substring:
            response_text = json.dumps(data).lower()
            assert error_substring.lower() in response_text, (
                f"Error message doesn't contain '{error_substring}'"
            )
    
    @staticmethod
    def assert_command_executed(executor_mock, command_name, times=1):
        """Assert that a command was executed expected number of times."""
        if times == 0:
            executor_mock.execute_command.assert_not_called()
        else:
            assert executor_mock.execute_command.call_count == times, (
                f"Expected {times} calls, got {executor_mock.execute_command.call_count}"
            )
            if times == 1:
                executor_mock.execute_command.assert_called_with(command_name)
    
    @staticmethod
    def assert_state_transition(state_manager_mock, from_state=None, to_state=None):
        """
        Assert that state transition occurred.
        
        Args:
            state_manager_mock: Mocked state manager
            from_state: Expected previous state (optional)
            to_state: Expected new state
        """
        if to_state:
            calls = state_manager_mock.change_state.call_args_list
            called_with_state = any(
                str(call) == to_state or to_state in str(call)
                for call in calls
            )
            assert called_with_state, f"State never transitioned to '{to_state}'"
    
    @staticmethod
    def assert_valid_uuid(uuid_string):
        """Assert that string is a valid UUID format."""
        import uuid
        try:
            uuid.UUID(str(uuid_string))
        except ValueError:
            raise AssertionError(f"'{uuid_string}' is not a valid UUID")
    
    @staticmethod
    def assert_within_range(value, min_val, max_val, name="value"):
        """Assert that a numeric value is within expected range."""
        assert min_val <= value <= max_val, (
            f"{name}={value} not in range [{min_val}, {max_val}]"
        )
    
    @staticmethod
    def assert_list_length(lst, expected_length, name="list"):
        """Assert that a list has expected length."""
        actual = len(lst)
        assert actual == expected_length, (
            f"{name} has {actual} items, expected {expected_length}"
        )
    
    @staticmethod
    def assert_dict_subset(dct, subset):
        """Assert that dict contains all key-value pairs from subset."""
        for key, expected_value in subset.items():
            assert key in dct, f"Key '{key}' not found in dict"
            actual_value = dct[key]
            assert actual_value == expected_value, (
                f"Value mismatch for '{key}': expected {expected_value}, got {actual_value}"
            )
    
    @staticmethod
    def assert_mock_called_with_kwargs(mock, **kwargs):
        """Assert that mock was called with specific keyword arguments."""
        assert mock.called, "Mock was never called"
        
        call_kwargs = mock.call_args[1] if mock.call_args else {}
        for key, expected in kwargs.items():
            assert key in call_kwargs, f"Missing kwarg '{key}' in call"
            assert call_kwargs[key] == expected, (
                f"Kwarg '{key}' mismatch: expected {expected}, got {call_kwargs[key]}"
            )


# pytest-style assertion functions for direct use

def assert_success_response(response, keys=None):
    """Assert successful API response."""
    return TestAssertions.assert_valid_json_response(response, keys, 200)


def assert_created_response(response, keys=None):
    """Assert resource creation response."""
    return TestAssertions.assert_valid_json_response(response, keys, 201)


def assert_not_found(response):
    """Assert 404 not found response."""
    return TestAssertions.assert_error_response(response, 404)


def assert_bad_request(response, error_msg=None):
    """Assert 400 bad request response."""
    return TestAssertions.assert_error_response(response, 400, error_msg)


def assert_valid_command_result(result, expected_success=True):
    """Assert command execution result."""
    if expected_success:
        assert result is True, f"Expected command success, got {result}"
    else:
        assert result is False, f"Expected command failure, got {result}"
