# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Small business account and job management system built with Python 3.13+. This is an early-stage project with minimal implementation currently.

## Development Commands

### Environment Setup
```bash
# Setup virtual environment and install dependencies
uv sync

# Install pre-commit hooks
pre-commit install-hooks
```

### Testing
```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Run a single test file
uv run pytest tests/path/to/test_file.py

# Run a specific test function
uv run pytest tests/path/to/test_file.py::test_function_name
```

### Code Quality
```bash
# Run ruff linter
uv run ruff check .

# Run ruff linter with auto-fix
uv run ruff check --fix .

# Run ruff formatter
uv run ruff format .

# Run all pre-commit hooks manually
pre-commit run --all-files
```

### Documentation
```bash
# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build

# Deploy documentation to GitHub Pages
mkdocs gh-deploy
```

## Code Style & Formatting

- **Line length**: 100 characters
- **Indentation**: Tabs (width 4)
- **Quote style**: Double quotes
- **Python version**: 3.13+
- **Linter/Formatter**: ruff (replaces black, flake8, isort)

## Architecture & Structure

### Project Layout
```
src/small_business/     # Main package source code
docs/                   # MkDocs documentation
  notebooks/            # Jupyter notebooks for examples (executed in docs)
  api_docs/            # API reference documentation
tests/                  # pytest test suite (not yet created)
```

### Key Technologies
- **uv**: Package and dependency management (replaces pip/poetry)
- **pytest**: Testing framework with code coverage
- **MkDocs Material**: Documentation with mkdocs-jupyter for executable notebooks
- **pre-commit**: Code quality enforcement with ruff and codespell

### Documentation
MkDocs is configured to execute Jupyter notebooks during build (via mkdocs-jupyter plugin). Python files in `docs/notebooks/` are treated as notebooks and executed when building documentation.

## Development Notes

- Use absolute imports (configured in pytest with `pythonpath = ["src"]`)
- Version is managed in `src/small_business/__init__.py` via hatchling
- Pre-commit excludes `dev.py` and `docs/*.py` files from checks
- Tests should have short docstrings describing what is being tested
