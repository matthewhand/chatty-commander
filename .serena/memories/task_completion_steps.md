# Steps to Complete a Task

## Before Starting

1. Understand the task requirements
1. Check existing code and tests
1. Plan the implementation

## During Development

1. Write code following style guidelines
1. Add/update tests as needed
1. Run tests frequently: `make test`
1. Check linting: `make lint`
1. Format code: `make format-fix`

## Before Committing

1. Run full test suite: `make test`
1. Check coverage: `make test-cov`
1. Lint code: `make lint`
1. Format code: `make format`
1. Type check: `make type-check`
1. Security check: `make security-check`
1. Run pre-commit hooks: `make pre-commit`

## After Changes

1. Update documentation if needed
1. Update README if features changed
1. Test integration if applicable
1. Run smoke tests: `make gate`

## Guidelines

- Tests must pass before commit
- Code must be linted and formatted
- Coverage should not decrease
- No security issues introduced
- Documentation kept current
- Use `make` targets for consistency
