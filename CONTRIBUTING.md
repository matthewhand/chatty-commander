# Contributing

## Documentation linting

Ensure documentation stays consistent and links remain valid by running the
following checks before pushing your changes:

```bash
uv sync --all-groups
uv run pydocstyle src
uv run doc8 README.md docs
uv run pytest --check-links README.md docs -q
```

These commands verify docstring style, lint the Markdown documentation, and test
that all referenced links resolve correctly.

