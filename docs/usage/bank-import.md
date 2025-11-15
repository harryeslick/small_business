# Bank Import Guide

Phase 2 implements bank CSV import with duplicate detection and automatic conversion to accounting transactions.

## Quick Start

```python
from pathlib import Path
from small_business.bank import import_bank_statement
from small_business.models.config import BankFormat

# Define bank format
bank_format = BankFormat(
    name="commonwealth",
    date_column="Date",
    description_column="Description",
    debit_column="Debit",
    credit_column="Credit",
    balance_column="Balance",
    date_format="%d/%m/%Y",
)

# Import statement
result = import_bank_statement(
    csv_path=Path("statement.csv"),
    bank_format=bank_format,
    bank_name="Commonwealth Bank",
    account_name="Business Cheque",
    bank_account_code="BANK-CHQ",
    data_dir=Path("data"),
)

print(f"Imported: {result['imported']}, Duplicates: {result['duplicates']}")
```

## Bank Format Configuration

### Debit/Credit Columns

For banks that separate debits and credits (e.g., Bankwest):

```python
BankFormat(
    name="bankwest",
    date_column="Transaction Date",
    description_column="Narration",
    debit_column="Debit",
    credit_column="Credit",
    balance_column="Balance",
    date_format="%d/%m/%Y",
)
```

Commonwealth Bank example:

```python
BankFormat(
    name="commonwealth",
    date_column="Date",
    description_column="Description",
    debit_column="Debit",
    credit_column="Credit",
    balance_column="Balance",
    date_format="%d/%m/%Y",
)
```

### Single Amount Column

For banks using positive/negative amounts:

```python
BankFormat(
    name="westpac",
    date_column="Transaction Date",
    description_column="Narration",
    amount_column="Amount",  # Positive = credit, Negative = debit
    balance_column="Balance",
    date_format="%d-%m-%Y",
)
```

## Storage Structure

Transactions are stored in financial-year-based directories:

```
data/
├── 2024-25/
│   └── transactions.jsonl
├── 2025-26/
│   └── transactions.jsonl
```

Each transaction is stored as a JSON line with double-entry journal entries.

## Duplicate Detection

Duplicates are detected using a hash of:
- Transaction date
- Description
- Amount

Balance is **not** included in the hash, allowing re-imports of overlapping statements.

## Default Account Codes

Unclassified transactions use:
- **Expenses** (debits): `EXP-UNCLASSIFIED`
- **Income** (credits): `INC-UNCLASSIFIED`

Classification will be implemented in Phase 3.
