# Test Quality Guide for ChattyCommander

This guide outlines best practices for writing high-quality tests in the ChattyCommander project.

## Table of Contents

1. [Test Organization](#test-organization)
1. [Test Naming Conventions](#test-naming-conventions)
1. [Fixture Usage](#fixture-usage)
1. [Mocking Best Practices](#mocking-best-practices)
1. [Assertion Guidelines](#assertion-guidelines)
1. [Test Isolation](#test-isolation)
1. [Performance Testing](#performance-testing)
1. [Code Coverage](#code-coverage)

## Test Organization

### Directory Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
├── integration/            # Integration tests
├── e2e/                    # End-to-end tests
├── performance/            # Performance benchmarks
├── fixtures/               # Shared test fixtures
├── conftest.py            # Pytest configuration
└── test_utils.py          # Shared test utilities
```

### Test File Naming

- `test_{module_name}.py` - Unit tests for specific modules
- `test_{feature}_integration.py` - Integration tests
- `test_{component}_e2e.py` - End-to-end tests
- `test_{component}_performance.py` - Performance tests

## Test Naming Conventions

### Function Names

```python
def test_should_{expected_behavior}_when_{condition}():
    """Test that {expected behavior} occurs when {condition}."""

def test_given_{initial_state}_when_{action}_then_{expected_result}():
    """Given {initial state}, when {action}, then {expected result}."""
```

### Examples

```python
def test_should_return_true_when_command_valid():
    """Test that validate_command returns True for valid commands."""

def test_given_invalid_config_when_loading_then_raises_error():
    """Given invalid config data, when loading config, then raises error."""
```

## Fixture Usage

### Shared Fixtures (in conftest.py)

```python
@pytest.fixture
def temp_dir():
    """Provide a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_config():
    """Provide a properly configured mock Config."""
    return TestDataFactory.create_mock_config()

@pytest.fixture
def real_config(temp_file, valid_config_data):
    """Provide a real Config instance for testing."""
    with open(temp_file, 'w') as f:
        json.dump(valid_config_data, f)
    return Config(str(temp_file))
```

### Fixture Scoping

- `function` (default): New fixture instance per test
- `class`: Shared across tests in a class
- `module`: Shared across tests in a module
- `session`: Shared across entire test session

## Mocking Best Practices

### Use Spec for Type Safety

```python
# Good: Use spec to ensure mock matches real interface
config_mock = Mock(spec=Config)

# Bad: Generic mock without type checking
config_mock = Mock()
```

### Configure Return Values Properly

```python
# Good: Configure specific return values
mock.method.return_value = expected_value
mock.method.side_effect = [value1, value2, exception]

# Bad: Overly broad mocking
mock.method = Mock(return_value=anything)
```

### Use Context Managers for Patching

```python
# Good: Use context manager for clear scope
with patch('module.Class.method') as mock_method:
    mock_method.return_value = expected_value
    # Test code here

# Bad: Patch decorator can hide issues
@patch('module.Class.method')
def test_something(mock_method):
    # Patch applies to entire function
```

## Assertion Guidelines

### Use Descriptive Assertions

```python
# Good: Clear assertion with descriptive message
assert result == expected, f"Expected {expected}, got {result} for input {input_value}"

# Bad: Bare assertion
assert result == expected
```

### Assert One Thing Per Test

```python
# Good: Single responsibility
def test_should_validate_email_format():
    assert is_valid_email("user@example.com")

def test_should_reject_invalid_email():
    assert not is_valid_email("invalid-email")

# Bad: Multiple assertions in one test
def test_email_validation():
    assert is_valid_email("user@example.com")
    assert not is_valid_email("invalid-email")
    assert not is_valid_email("")
```

### Use Appropriate Assertion Methods

```python
# For collections
assert len(items) == expected_count
assert item in collection
assert collection == expected_collection

# For exceptions
with pytest.raises(ValueError):
    function_that_raises()

# For approximate values
assert abs(actual - expected) < tolerance
```

## Test Isolation

### Clean Up Resources

```python
@pytest.fixture(autouse=True)
def cleanup_files():
    """Clean up any files created during tests."""
    yield
    # Cleanup code here
```

### Isolate External Dependencies

```python
# Use mocks for external services
@patch('requests.get')
def test_api_call(mock_get):
    mock_get.return_value.status_code = 200
    # Test code
```

### Avoid Global State

```python
# Bad: Modifies global state
def test_modify_global():
    global_var = "modified"
    # Test code

# Good: Use local state or fixtures
def test_with_local_state():
    local_var = "test_value"
    # Test code
```

## Performance Testing

### Use pytest-benchmark

```python
@pytest.mark.benchmark
def test_function_performance(benchmark):
    """Test function performance."""
    result = benchmark(function_under_test, arg1, arg2)
    assert result is not None
```

### Profile Memory Usage

```python
from memory_profiler import profile

@profile
def test_memory_usage():
    """Test memory usage of function."""
    # Test code that might have memory issues
```

## Code Coverage

### Coverage Goals

- **Unit Tests**: >90% coverage
- **Integration Tests**: >80% coverage
- **Overall**: >85% coverage

### Coverage Configuration (pyproject.toml)

```toml
[tool.coverage.run]
source = ["src"]
omit = [
    "tests/*",
    "*/venv/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

### Running Coverage

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html

# Generate coverage report
coverage html
```

## Best Practices Summary

1. **Write Descriptive Tests**: Use clear, descriptive names and docstrings
1. **Keep Tests Focused**: One test should verify one behavior
1. **Use Fixtures Wisely**: Leverage pytest fixtures for setup/teardown
1. **Mock Appropriately**: Use mocks to isolate units under test
1. **Assert Clearly**: Use descriptive assertions with helpful messages
1. **Maintain Isolation**: Ensure tests don't interfere with each other
1. **Monitor Performance**: Include performance tests where appropriate
1. **Track Coverage**: Maintain high code coverage standards

## Common Anti-Patterns to Avoid

1. **Testing Implementation Details**: Test behavior, not internal implementation
1. **Over-Mocking**: Don't mock everything - test real interactions where possible
1. **Brittle Tests**: Tests that break with every code change
1. **Slow Tests**: Keep unit tests fast, mark slow tests appropriately
1. **Inconsistent Naming**: Follow consistent naming conventions
1. **Missing Documentation**: Document complex test scenarios
1. **Hardcoded Values**: Use fixtures and factories instead of hardcoded data
1. **Ignoring Coverage**: Don't ignore low coverage areas without justification
