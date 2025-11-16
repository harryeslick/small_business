# Welcome to small_business

Small business account and job management system built with Python 3.13+.

## Features

### Phase 1: Data Models ✅
Core Pydantic models for accounting, invoicing, and job management:
- Client, Quote, Job, Invoice with line items
- Double-entry accounting with automatic validation
- GST calculations and financial year utilities

### Phase 2: Bank Imports ✅
Import and store bank transactions:
- CSV import with configurable column mapping
- JSONL storage organized by financial year
- Transaction deduplication by ID

### Phase 3: Expense Classification ✅
Automated transaction categorization:
- Regex pattern-based classification rules
- Priority-based conflict resolution
- Auto-learning from user classifications
- YAML rule storage with JSONL integration

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/small_business.git
cd small_business

# Setup environment
uv sync

# Install pre-commit hooks
pre-commit install-hooks
```

### Usage Guides

- **[Bank Import](usage/bank-import.md)**: Import bank transactions from CSV
- **[Expense Classification](usage/expense-classification.md)**: Automated transaction categorization

## Documentation

- **Usage Guides**: Step-by-step instructions for common tasks
- **API Reference**: Detailed API documentation (auto-generated)
- **Design Plans**: Implementation plans for each development phase
