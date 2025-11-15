# Phase 1: Data Structures Design

**Date:** 2025-11-15
**Status:** Approved
**Phase:** Foundation (Phase 1)

## Overview

Phase 1 establishes the core Pydantic models for the small business management system. These models provide type-safe, validated data structures with pragmatic validation - enough to ensure data integrity without over-engineering business logic.

## Design Principles

- **Decimal for money**: All monetary values use `Decimal` for precision in financial calculations
- **ID strings for relationships**: Simple string IDs (not nested objects) for serialization and plain-text storage
- **Hybrid flat hierarchy**: Chart of accounts stored as flat list with utility methods for tree operations
- **Computed fields**: Automatic calculations for totals, GST, and financial year
- **Pragmatic validation**: Data integrity (types, constraints) without complex business logic
- **Enums for status**: Type-safe workflow state tracking

## Foundation Utilities

### Financial Year Calculation

```python
# src/small_business/models/utils.py
from datetime import date

def get_financial_year(d: date) -> str:
    """Calculate financial year (July-June) from a date.

    Example: 2025-11-15 -> "2025-26"
             2025-06-30 -> "2024-25"
    """
    if d.month >= 7:
        return f"{d.year}-{str(d.year + 1)[-2:]}"
    else:
        return f"{d.year - 1}-{str(d.year)[-2:]}"
```

### ID Generation

```python
def generate_quote_id() -> str:
    """Generate quote ID: Q-YYYYMMDD-001"""
    # Implementation uses date + counter logic

def generate_job_id() -> str:
    """Generate job ID: J-YYYYMMDD-001"""

def generate_invoice_id() -> str:
    """Generate invoice ID: INV-YYYYMMDD-001"""

def generate_transaction_id() -> str:
    """Generate transaction ID: TXN-YYYYMMDD-001"""

def generate_client_id() -> str:
    """Generate client ID: C-YYYYMMDD-001"""
```

**Design Note:** ID generation uses `default_factory` in Pydantic fields, but accepts override for importing existing data or testing.

## Enums

### Status Types

```python
# src/small_business/models/enums.py
from enum import Enum

class QuoteStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"

class JobStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    INVOICED = "invoiced"

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class AccountType(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    INCOME = "income"
    EXPENSE = "expense"
```

**Design Note:** Inheriting from both `str` and `Enum` enables clean JSON serialization while maintaining type safety.

## Core Entity Models

### Client

```python
# src/small_business/models/client.py
from pydantic import BaseModel, Field, EmailStr
from .utils import generate_client_id

class Client(BaseModel):
    """Client/customer information."""

    client_id: str = Field(default_factory=generate_client_id)
    name: str = Field(min_length=1)
    email: EmailStr | None = None
    phone: str | None = None
    abn: str | None = None  # Australian Business Number
    notes: str = ""
```

**Design Note:** Minimal fields for Phase 1. Can extend with address fields in Phase 4 when implementing document generation.

### LineItem

```python
# src/small_business/models/line_item.py
from decimal import Decimal
from pydantic import BaseModel, Field, computed_field

class LineItem(BaseModel):
    """Line item for quotes and invoices."""

    description: str = Field(min_length=1)
    quantity: Decimal = Field(gt=0, decimal_places=2)
    unit_price: Decimal = Field(ge=0, decimal_places=2)
    gst_inclusive: bool = True

    @computed_field
    @property
    def subtotal(self) -> Decimal:
        """Calculate subtotal (quantity × unit_price)."""
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))

    @computed_field
    @property
    def gst_amount(self) -> Decimal:
        """Calculate GST amount (1/11 if inclusive, 10% if exclusive)."""
        if self.gst_inclusive:
            # GST = subtotal × 1/11
            return (self.subtotal / Decimal("11")).quantize(Decimal("0.01"))
        else:
            # GST = subtotal × 10%
            return (self.subtotal * Decimal("0.10")).quantize(Decimal("0.01"))

    @computed_field
    @property
    def total(self) -> Decimal:
        """Calculate total (subtotal + GST if exclusive, subtotal if inclusive)."""
        if self.gst_inclusive:
            return self.subtotal
        else:
            return (self.subtotal + self.gst_amount).quantize(Decimal("0.01"))
```

**Design Note:**
- `@computed_field` properties serialize to JSON automatically
- `.quantize(Decimal("0.01"))` ensures 2 decimal places for currency
- Handles both GST-inclusive and GST-exclusive pricing

### Quote

```python
# src/small_business/models/quote.py
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, computed_field
from .enums import QuoteStatus
from .line_item import LineItem
from .utils import generate_quote_id, get_financial_year

class Quote(BaseModel):
    """Quote/proposal for client work."""

    quote_id: str = Field(default_factory=generate_quote_id)
    client_id: str
    date_created: date = Field(default_factory=date.today)
    date_valid_until: date
    status: QuoteStatus = QuoteStatus.DRAFT
    line_items: list[LineItem] = Field(min_length=1)
    terms_and_conditions: str = ""
    version: int = 1
    notes: str = ""

    @computed_field
    @property
    def financial_year(self) -> str:
        """Financial year based on date_created."""
        return get_financial_year(self.date_created)

    @computed_field
    @property
    def subtotal(self) -> Decimal:
        """Sum of all line item subtotals."""
        return sum(item.subtotal for item in self.line_items).quantize(Decimal("0.01"))

    @computed_field
    @property
    def gst_amount(self) -> Decimal:
        """Sum of all line item GST amounts."""
        return sum(item.gst_amount for item in self.line_items).quantize(Decimal("0.01"))

    @computed_field
    @property
    def total(self) -> Decimal:
        """Total quote amount."""
        return sum(item.total for item in self.line_items).quantize(Decimal("0.01"))
```

**Design Note:** Totals automatically calculated from line items. Handles mixed GST-inclusive and exclusive items correctly.

### Job

```python
# src/small_business/models/job.py
from datetime import date
from pydantic import BaseModel, Field, computed_field
from .enums import JobStatus
from .utils import generate_job_id, get_financial_year

class Job(BaseModel):
    """Job/work tracking from accepted quote."""

    job_id: str = Field(default_factory=generate_job_id)
    quote_id: str | None = None  # Reference to parent quote
    client_id: str
    date_accepted: date
    scheduled_date: date | None = None
    status: JobStatus = JobStatus.SCHEDULED
    actual_costs: list[str] = Field(default_factory=list)  # List of transaction_ids
    notes: str = ""
    calendar_event_id: str | None = None  # Link to .ics event

    @computed_field
    @property
    def financial_year(self) -> str:
        """Financial year based on date_accepted."""
        return get_financial_year(self.date_accepted)
```

**Design Note:**
- `quote_id` optional (allows jobs without formal quotes)
- `actual_costs` tracks transaction IDs for expense linking

### Invoice

```python
# src/small_business/models/invoice.py
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, computed_field
from .enums import InvoiceStatus
from .line_item import LineItem
from .utils import generate_invoice_id, get_financial_year

class Invoice(BaseModel):
    """Invoice for completed work."""

    invoice_id: str = Field(default_factory=generate_invoice_id)
    job_id: str | None = None  # Reference to parent job
    client_id: str
    date_issued: date = Field(default_factory=date.today)
    date_due: date
    status: InvoiceStatus = InvoiceStatus.DRAFT
    payment_date: date | None = None
    payment_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    payment_reference: str = ""
    line_items: list[LineItem] = Field(min_length=1)
    version: int = 1
    notes: str = ""

    @computed_field
    @property
    def financial_year(self) -> str:
        """Financial year based on date_issued."""
        return get_financial_year(self.date_issued)

    @computed_field
    @property
    def subtotal(self) -> Decimal:
        """Sum of all line item subtotals."""
        return sum(item.subtotal for item in self.line_items).quantize(Decimal("0.01"))

    @computed_field
    @property
    def gst_amount(self) -> Decimal:
        """Sum of all line item GST amounts."""
        return sum(item.gst_amount for item in self.line_items).quantize(Decimal("0.01"))

    @computed_field
    @property
    def total(self) -> Decimal:
        """Total invoice amount."""
        return sum(item.total for item in self.line_items).quantize(Decimal("0.01"))
```

**Design Note:** Similar to Quote but adds payment tracking fields. `job_id` optional for direct invoicing without jobs.

## Accounting Models

### Account & Chart of Accounts

```python
# src/small_business/models/account.py
from pydantic import BaseModel, Field, model_validator
from .enums import AccountType

class Account(BaseModel):
    """Individual account in the chart of accounts."""

    code: str = Field(pattern=r"^[A-Z0-9\-]+$")  # e.g., "EXP-TRV-FLT"
    name: str = Field(min_length=1)
    account_type: AccountType
    parent_code: str | None = None
    description: str = ""


class ChartOfAccounts(BaseModel):
    """Complete chart of accounts with hierarchy utilities."""

    accounts: list[Account]

    @model_validator(mode='after')
    def validate_structure(self):
        """Validate account hierarchy rules."""
        codes = {acc.code for acc in self.accounts}

        # Check all parent_codes exist
        for account in self.accounts:
            if account.parent_code and account.parent_code not in codes:
                raise ValueError(f"Parent '{account.parent_code}' not found for '{account.code}'")

        # Check max 2-level hierarchy
        for account in self.accounts:
            if account.parent_code:
                parent = self.get_account(account.parent_code)
                if parent.parent_code is not None:
                    raise ValueError(f"Max 2-level hierarchy exceeded: '{account.code}'")

        return self

    def get_account(self, code: str) -> Account:
        """Get account by code."""
        for account in self.accounts:
            if account.code == code:
                return account
        raise KeyError(f"Account not found: {code}")

    def get_children(self, parent_code: str) -> list[Account]:
        """Get all child accounts of a parent."""
        return [acc for acc in self.accounts if acc.parent_code == parent_code]

    def get_root_accounts(self) -> list[Account]:
        """Get all top-level accounts (no parent)."""
        return [acc for acc in self.accounts if acc.parent_code is None]
```

**Design Note:**
- Flat list storage (easy JSON serialization)
- Validates parent existence and enforces 2-level max hierarchy
- Helper methods for querying hierarchy without building tree structures

### Transaction & Journal Entry

```python
# src/small_business/models/transaction.py
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator, computed_field
from .utils import generate_transaction_id, get_financial_year

class JournalEntry(BaseModel):
    """Individual journal entry (debit or credit)."""

    account_code: str
    debit: Decimal = Field(default=Decimal(0), ge=0, decimal_places=2)
    credit: Decimal = Field(default=Decimal(0), ge=0, decimal_places=2)

    @model_validator(mode='after')
    def check_debit_or_credit(self):
        """Ensure exactly one of debit or credit is non-zero."""
        if self.debit > 0 and self.credit > 0:
            raise ValueError("Entry cannot have both debit and credit")
        if self.debit == 0 and self.credit == 0:
            raise ValueError("Entry must have either debit or credit")
        return self


class Transaction(BaseModel):
    """Transaction with double-entry journal entries."""

    transaction_id: str = Field(default_factory=generate_transaction_id)
    date: date = Field(default_factory=date.today)
    description: str = Field(min_length=1)
    entries: list[JournalEntry] = Field(min_length=2)
    receipt_path: str | None = None  # Path to receipt file
    gst_inclusive: bool = False
    notes: str = ""

    @computed_field
    @property
    def financial_year(self) -> str:
        """Financial year based on transaction date."""
        return get_financial_year(self.date)

    @model_validator(mode='after')
    def check_balanced(self):
        """Ensure total debits equal total credits."""
        total_debits = sum(entry.debit for entry in self.entries)
        total_credits = sum(entry.credit for entry in self.entries)

        if total_debits != total_credits:
            raise ValueError(
                f"Transaction not balanced: debits={total_debits}, credits={total_credits}"
            )

        return self

    @computed_field
    @property
    def amount(self) -> Decimal:
        """Transaction amount (total debits or credits)."""
        return sum(entry.debit for entry in self.entries).quantize(Decimal("0.01"))
```

**Design Note:**
- JournalEntry ensures only debit OR credit (not both, not neither)
- Transaction validates debits = credits at model level
- Supports complex splits (more than 2 entries)
- `receipt_path` links to stored receipt files

## Configuration

### Settings

```python
# src/small_business/models/config.py
from decimal import Decimal
from pydantic import BaseModel, Field

class Settings(BaseModel):
    """Application settings and constants."""

    # Tax settings
    gst_rate: Decimal = Field(default=Decimal("0.10"), ge=0, le=1, decimal_places=2)

    # Financial year settings
    financial_year_start_month: int = Field(default=7, ge=1, le=12)  # July

    # Currency and formatting
    currency: str = "AUD"
    date_format: str = "%Y-%m-%d"

    # Business details (for document generation later)
    business_name: str = ""
    business_abn: str = ""
    business_email: str = ""
    business_phone: str = ""
    business_address: str = ""

    # File paths (relative to data directory)
    data_directory: str = "data"
```

**Design Note:**
- Minimal config for Phase 1
- Business details included for future document generation
- Complex config (bank formats) deferred to Phase 2

## Module Organization

### File Structure

```
src/small_business/
├── __init__.py
└── models/
    ├── __init__.py          # Export all public models
    ├── enums.py             # All enum types
    ├── utils.py             # ID generation, financial year calc
    ├── config.py            # Settings model
    ├── client.py            # Client model
    ├── line_item.py         # LineItem model
    ├── quote.py             # Quote model
    ├── job.py               # Job model
    ├── invoice.py           # Invoice model
    ├── account.py           # Account, ChartOfAccounts models
    └── transaction.py       # Transaction, JournalEntry models
```

### Public API

```python
# src/small_business/models/__init__.py
"""Phase 1: Core Pydantic models for small business management."""

from .enums import QuoteStatus, JobStatus, InvoiceStatus, AccountType
from .config import Settings
from .client import Client
from .line_item import LineItem
from .quote import Quote
from .job import Job
from .invoice import Invoice
from .account import Account, ChartOfAccounts
from .transaction import Transaction, JournalEntry
from .utils import get_financial_year

__all__ = [
    # Enums
    "QuoteStatus",
    "JobStatus",
    "InvoiceStatus",
    "AccountType",
    # Models
    "Settings",
    "Client",
    "LineItem",
    "Quote",
    "Job",
    "Invoice",
    "Account",
    "ChartOfAccounts",
    "Transaction",
    "JournalEntry",
    # Utils
    "get_financial_year",
]
```

**Usage:**
```python
from small_business.models import Quote, LineItem, QuoteStatus
```

## Testing Strategy

Each model requires tests for:

1. **Valid construction** - Test with all required fields
2. **Validation failures** - Test constraints (e.g., unbalanced transactions, invalid hierarchy)
3. **Computed properties** - Test totals, GST calculations, financial year
4. **Serialization** - Test to/from JSON with `model_dump()` and `model_validate()`

Example test structure:
```python
def test_quote_totals():
    """Test quote calculates totals correctly from line items."""

def test_transaction_must_balance():
    """Test transaction raises error when debits != credits."""

def test_chart_max_two_levels():
    """Test chart of accounts enforces max 2-level hierarchy."""
```

## Future Phases

These models enable:

- **Phase 2**: Bank imports create `Transaction` objects
- **Phase 3**: Expense classification links transactions to accounts
- **Phase 4**: Document generation uses `Quote`/`Invoice` with `LineItem`
- **Phase 5**: Reports query `Transaction` and calculate from `ChartOfAccounts`

## Summary

Phase 1 delivers a complete, type-safe data foundation with:
- ✅ All core entity models (Client, Quote, Job, Invoice)
- ✅ Double-entry accounting models (Transaction, Account)
- ✅ Automatic calculations (totals, GST, financial year)
- ✅ Validation for data integrity
- ✅ Clean module organization
- ✅ Ready for JSON serialization to plain-text storage

Next step: Implement these models with tests, then proceed to Phase 2 (Bank imports and transaction management).
