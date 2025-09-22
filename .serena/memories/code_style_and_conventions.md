# Code Style and Conventions

## Python Version

- Target: Python 3.11+
- Minimum: Python 3.11

## Linting and Formatting

- **Linter**: ruff with rules: E, W, F, I, B, C4, UP
- **Formatter**: black with line length 88
- **Type Checker**: mypy with strict settings
- **Security**: bandit for security linting

## Ruff Configuration

- select: E, W, F, I, B, C4, UP
- ignore: E501, B008, C901
- per-file-ignores: **init**.py (F401), tests/\*_/_ (B011)

## Black Configuration

- line-length: 88
- target-version: py311
- include: .py files

## MyPy Configuration

- python_version: 3.11
- strict mode enabled
- warn on unused configs
- disallow untyped defs

## Naming Conventions

- Classes: PascalCase
- Functions/Methods: snake_case
- Constants: UPPER_SNAKE_CASE
- Variables: snake_case
- Modules: snake_case

## Code Structure

- Use type hints everywhere
- Docstrings for all public functions/classes
- Prefer dataclasses over dicts
- Use pathlib for file paths
- Async/await for I/O operations
- Context managers for resources

## Import Organization

- Standard library first
- Third-party second
- Local imports last
- One import per line
- Absolute imports preferred

## Error Handling

- Use specific exceptions
- Avoid bare except clauses
- Use context managers
- Log errors appropriately

## Testing

- pytest framework
- test\_\*.py files
- test\_\* functions
- 85%+ coverage target
- Mock external dependencies

## Documentation

- Google-style docstrings
- Document public APIs
- Type hints as documentation

## Performance

- Async for I/O operations
- Profile before optimizing
- Appropriate data structures
- Cache expensive operations

## Security

- Validate inputs
- Parameterized queries
- Sanitize outputs
- Least privilege principle

## Git Workflow

- Feature branches
- Descriptive commits
- Pre-commit hooks
- Tests must pass
