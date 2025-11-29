# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## `small_business`. An Accounts Management System for Small Business. 

This package is designed to be a simple tool for assisting with management of invoicing and account management for small business in Australia. The package is designed for a simple sole trader business, with low account complexity. The software should be easy to manage and make business management simpler, not more complex.

## Design Philosophy

The package should be simple and lightweight and portable. The software is designed to run locally on a single machine.

**Core Principles:**
- All datafiles stored as plain text formats: CSV, JSON, YAML
- UNIX style plain text configuration
- Software is stateless, with account state determined via an Event-Sourcing pattern from event logs stored in plain text and loaded at startup
- Written in Python 3.13+ using a terminal TUI user interface
- Prioritize simplicity and usability over feature complexity


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
  models/               # Phase 1: Pydantic models (Client, Quote, Job, Invoice, Account, Transaction)
docs/                   # MkDocs documentation
  notebooks/            # Jupyter notebooks for examples (executed in docs)
  api_docs/            # API reference documentation
  plans/               # Design documents for each phase
tests/                  # pytest test suite
  models/              # Tests for Pydantic models
```

### Key Technologies
- **uv**: Package and dependency management (replaces pip/poetry)
- **Pydantic**: Data validation and modeling (Phase 1 foundation)
- **pytest**: Testing framework with code coverage
- **MkDocs Material**: Documentation with mkdocs-jupyter for executable notebooks

### Documentation
MkDocs is configured to execute Jupyter notebooks during build (via mkdocs-jupyter plugin). Python files in `docs/notebooks/` are treated as notebooks and executed when building documentation.

## Development Notes

### General
- Use absolute imports (configured in pytest with `pythonpath = ["src"]`)
- Version is managed in `src/small_business/__init__.py` via hatchling
- Pre-commit excludes `dev.py` and `docs/*.py` files from checks
- Tests should have short docstrings describing what is being tested

### Phase 1: Data Models (Current)
The project uses Pydantic models for all core entities. Key design patterns:

- **Decimal for money**: All monetary values use `Decimal` for precision
- **String IDs for relationships**: Simple string IDs (not nested objects) for serialization
- **Computed fields**: Automatic calculations for totals, GST, financial year using `@computed_field`
- **Model validators**: Data integrity validation (e.g., balanced transactions, account hierarchy)
- **Double-entry accounting**: Transaction model enforces debits = credits

See `docs/plans/2025-11-15-phase1-datastructures-design.md` for complete architecture details.

## API Design Principles

These principles guide the design of all modules and should be applied consistently across the codebase.

### 1. Auto-Lookup Dependencies
High-level functions should automatically load required dependencies using `data_dir` rather than requiring callers to pass everything explicitly.

**Pattern:**
```python
# Good - auto-loads dependencies
generate_quote_document(quote, output_path, data_dir)

# Avoid - requires caller to load everything
client = load_client(quote.client_id, data_dir)
settings = load_settings(data_dir)
generate_quote_document(quote, client, settings, output_path)
```

**Rationale:** Reduces boilerplate, centralizes loading logic, makes APIs easier to use correctly.

### 2. Sensible Defaults for Optional Parameters
Optional parameters should default to the most common use case rather than requiring explicit values.

**Pattern:**
```python
# Good - defaults to latest version (most common)
load_quote(quote_id, data_dir, version=None)

# Avoid - always requiring version even when latest is wanted
load_quote(quote_id, data_dir, version=get_latest_version(quote_id))
```

**Rationale:** Reduces cognitive load, makes common cases simple while keeping advanced cases possible.

### 3. Human-Readable Identifiers Where Appropriate
Use business-meaningful identifiers for entities that have natural unique keys.

**Pattern:**
```python
# Good - business name is naturally unique and meaningful
client_id = "Woolworths"

# Avoid - generated ID is opaque and meaningless
client_id = "C-20251116-001"
```

**When to use:**
- **Human-readable IDs**: Entities with natural unique keys (client business names)
- **Generated IDs**: Entities needing audit trails or without natural keys (quotes, jobs, invoices)

**Rationale:** Improves debuggability, makes data more understandable, reduces need for lookups.

### 4. Case-Insensitive Lookups for User-Provided IDs
When IDs are user-provided strings (like business names), implement case-insensitive matching.

**Pattern:**
```python
# Normalize for comparison
normalized_id = client_id.lower()
for client in clients:
    if client.client_id.lower() == normalized_id:
        return client
```

**Rationale:** More forgiving for user input, prevents duplicate records due to case differences.

### 5. Template-Based Document Generation
Use template systems (like Jinja2) for document generation rather than programmatic assembly.

**Pattern:**
```python
# Good - use templates
doc = DocxTemplate(template_path)
doc.render(context)

# Avoid - programmatic assembly
doc = Document()
doc.add_heading("Quote")
doc.add_paragraph(f"Date: {quote.date}")
# ... many more doc.add_* calls
```

**Rationale:** Separates presentation from logic, enables non-developers to modify layouts, easier to test.

### 6. Settings-Based Configuration
Store configurable values in the Settings model rather than hard-coding or requiring as function arguments.

**Pattern:**
```python
# Good - configured in Settings
settings = load_settings(data_dir)
template_path = settings.quote_template_path

# Avoid - hard-coded paths
template_path = "templates/quote.docx"

# Avoid - requiring as parameter everywhere
def generate_quote(quote, template_path, output_path): ...
```

**Rationale:** Centralizes configuration, enables customization without code changes, reduces parameter sprawl.

### 7. Structured Data with Computed Display Fields
For complex data like addresses, store both structured fields (for validation/formatting) and computed display fields.

**Pattern:**
```python
class Client(BaseModel):
    # Structured fields
    street_address: str | None
    suburb: str | None
    state: str | None
    postcode: str | None

    # Computed display field
    formatted_address: str | None
```

**Rationale:** Structured fields enable validation and flexible formatting; display fields provide convenience.

## Applying These Principles

When implementing new features:

1. **Check for auto-lookup opportunities** - Can the function load its own dependencies?
2. **Consider sensible defaults** - What's the most common use case?
3. **Evaluate ID strategies** - Natural unique key or generated ID?
4. **Plan for user input** - Should lookups be case-insensitive?
5. **Separate presentation from logic** - Use templates for documents/reports
6. **Centralize configuration** - Settings model vs. hard-coding vs. parameters
7. **Balance structure and display** - Store structured data with computed display fields

See `docs/plans/2025-11-23-phase4-revisions-design.md` for detailed examples of these principles in practice.
