# Phase 2: Bank Imports and Transaction Management Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement bank CSV import, transaction creation, and plain-text storage for the accounting system.

**Architecture:** Build CSV/OFX parsing with configurable bank formats, create transaction records with double-entry validation, implement plain-text storage in financial-year-based directories, and add duplicate detection.

**Tech Stack:** Python 3.13+, Pydantic (Phase 1 models), Pandas (CSV processing), YAML (bank format config)

---

## Task 1: Bank Format Configuration Model

**Files:**
- Modify: `src/small_business/models/config.py:29` (add BankFormat and BankFormats models)
- Test: `tests/models/test_config.py`

**Step 1: Write the failing test**

Create `tests/models/test_config.py` if it doesn't exist, or add to existing file:

```python
"""Test configuration models."""

from small_business.models.config import BankFormat, BankFormats


def test_bank_format_valid():
	"""Test valid bank format configuration."""
	config = BankFormat(
		name="commonwealth",
		date_column="Date",
		description_column="Description",
		debit_column="Debit",
		credit_column="Credit",
		balance_column="Balance",
		date_format="%d/%m/%Y",
	)
	assert config.name == "commonwealth"
	assert config.date_format == "%d/%m/%Y"


def test_bank_formats_multiple():
	"""Test bank formats collection with multiple banks."""
	formats = BankFormats(
		formats=[
			BankFormat(
				name="commonwealth",
				date_column="Date",
				description_column="Description",
				debit_column="Debit",
				credit_column="Credit",
				balance_column="Balance",
				date_format="%d/%m/%Y",
			),
			BankFormat(
				name="westpac",
				date_column="Transaction Date",
				description_column="Narration",
				debit_column="Debit Amount",
				credit_column="Credit Amount",
				balance_column="Balance",
				date_format="%d-%m-%Y",
			),
		]
	)
	assert len(formats.formats) == 2
	comm = formats.get_format("commonwealth")
	assert comm.date_column == "Date"


def test_bank_formats_get_format_not_found():
	"""Test getting non-existent bank format raises KeyError."""
	formats = BankFormats(formats=[])
	try:
		formats.get_format("nonexistent")
		assert False, "Should raise KeyError"
	except KeyError as e:
		assert "nonexistent" in str(e)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/models/test_config.py::test_bank_format_valid -v`

Expected: FAIL with "ImportError: cannot import name 'BankFormat'"

**Step 3: Write minimal implementation**

Add to `src/small_business/models/config.py`:

```python
class BankFormat(BaseModel):
	"""Configuration for a specific bank's CSV format."""

	name: str = Field(min_length=1)
	date_column: str = Field(min_length=1)
	description_column: str = Field(min_length=1)
	debit_column: str | None = None
	credit_column: str | None = None
	amount_column: str | None = None  # For single amount column (positive/negative)
	balance_column: str | None = None
	date_format: str = "%Y-%m-%d"


class BankFormats(BaseModel):
	"""Collection of bank format configurations."""

	formats: list[BankFormat] = Field(default_factory=list)

	def get_format(self, name: str) -> BankFormat:
		"""Get bank format by name."""
		for fmt in self.formats:
			if fmt.name == name:
				return fmt
		raise KeyError(f"Bank format not found: {name}")
```

Update `src/small_business/models/__init__.py` to export:

```python
from .config import Settings, BankFormat, BankFormats

__all__ = [
	# ... existing exports ...
	"BankFormat",
	"BankFormats",
]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/models/test_config.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add tests/models/test_config.py src/small_business/models/config.py src/small_business/models/__init__.py
git commit -m "feat: add bank format configuration models

Add BankFormat and BankFormats Pydantic models for configurable
bank CSV import formats. Supports debit/credit columns or single
amount column for different bank statement formats.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Bank Transaction Import Data Model

**Files:**
- Create: `src/small_business/bank/__init__.py`
- Create: `src/small_business/bank/models.py`
- Test: `tests/bank/test_models.py`

**Step 1: Write the failing test**

Create `tests/bank/test_models.py`:

```python
"""Test bank import models."""

from datetime import date
from decimal import Decimal

from small_business.bank.models import BankTransaction, ImportedBankStatement


def test_bank_transaction_debit():
	"""Test bank transaction with debit amount."""
	txn = BankTransaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		debit=Decimal("45.50"),
		credit=Decimal("0"),
		balance=Decimal("1000.00"),
	)
	assert txn.amount == Decimal("-45.50")
	assert txn.is_debit is True


def test_bank_transaction_credit():
	"""Test bank transaction with credit amount."""
	txn = BankTransaction(
		date=date(2025, 11, 15),
		description="PAYMENT RECEIVED",
		debit=Decimal("0"),
		credit=Decimal("100.00"),
		balance=Decimal("1100.00"),
	)
	assert txn.amount == Decimal("100.00")
	assert txn.is_debit is False


def test_imported_statement():
	"""Test imported bank statement with transactions."""
	stmt = ImportedBankStatement(
		bank_name="commonwealth",
		account_name="Business Cheque",
		import_date=date(2025, 11, 15),
		transactions=[
			BankTransaction(
				date=date(2025, 11, 1),
				description="Opening balance",
				debit=Decimal("0"),
				credit=Decimal("0"),
				balance=Decimal("1000.00"),
			),
			BankTransaction(
				date=date(2025, 11, 10),
				description="WOOLWORTHS",
				debit=Decimal("50.00"),
				credit=Decimal("0"),
				balance=Decimal("950.00"),
			),
		],
	)
	assert stmt.bank_name == "commonwealth"
	assert len(stmt.transactions) == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/bank/test_models.py::test_bank_transaction_debit -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'small_business.bank'"

**Step 3: Write minimal implementation**

Create `src/small_business/bank/__init__.py`:

```python
"""Bank import functionality."""

from .models import BankTransaction, ImportedBankStatement

__all__ = ["BankTransaction", "ImportedBankStatement"]
```

Create `src/small_business/bank/models.py`:

```python
"""Bank import data models."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, computed_field


class BankTransaction(BaseModel):
	"""Single bank transaction from CSV import."""

	date: date
	description: str = Field(min_length=1)
	debit: Decimal = Field(ge=0, decimal_places=2)
	credit: Decimal = Field(ge=0, decimal_places=2)
	balance: Decimal | None = Field(default=None, decimal_places=2)

	@computed_field
	@property
	def amount(self) -> Decimal:
		"""Net amount (credit - debit)."""
		return (self.credit - self.debit).quantize(Decimal("0.01"))

	@computed_field
	@property
	def is_debit(self) -> bool:
		"""True if transaction is a debit (outgoing)."""
		return self.debit > 0


class ImportedBankStatement(BaseModel):
	"""Collection of imported bank transactions."""

	bank_name: str = Field(min_length=1)
	account_name: str = Field(min_length=1)
	import_date: date = Field(default_factory=date.today)
	transactions: list[BankTransaction] = Field(default_factory=list)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/bank/test_models.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/bank/ tests/bank/
git commit -m "feat: add bank transaction import models

Add BankTransaction and ImportedBankStatement models for
representing imported bank data before conversion to accounting
transactions.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: CSV Parser with Bank Format Support

**Files:**
- Create: `src/small_business/bank/parser.py`
- Test: `tests/bank/test_parser.py`

**Step 1: Write the failing test**

Create `tests/bank/test_parser.py`:

```python
"""Test CSV parser."""

import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.bank.parser import parse_csv
from small_business.models.config import BankFormat


def test_parse_csv_debit_credit_columns():
	"""Test parsing CSV with separate debit/credit columns (Bankwest format)."""
	# Create temporary CSV file (simplified Bankwest format)
	csv_content = """Transaction Date,Narration,Debit,Credit,Balance
01/11/2025,Opening Balance,,,1000.00
10/11/2025,WOOLWORTHS 1234,45.50,,954.50
15/11/2025,PAYMENT RECEIVED,,100.00,1054.50
"""
	with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
		f.write(csv_content)
		csv_path = Path(f.name)

	try:
		bank_format = BankFormat(
			name="bankwest",
			date_column="Transaction Date",
			description_column="Narration",
			debit_column="Debit",
			credit_column="Credit",
			balance_column="Balance",
			date_format="%d/%m/%Y",
		)

		statement = parse_csv(csv_path, bank_format, "Test Bank", "Business Account")

		assert statement.bank_name == "Test Bank"
		assert statement.account_name == "Business Account"
		assert len(statement.transactions) == 3

		# Check opening balance
		assert statement.transactions[0].description == "Opening Balance"
		assert statement.transactions[0].balance == Decimal("1000.00")

		# Check debit
		assert statement.transactions[1].description == "WOOLWORTHS 1234"
		assert statement.transactions[1].debit == Decimal("45.50")
		assert statement.transactions[1].amount == Decimal("-45.50")

		# Check credit
		assert statement.transactions[2].description == "PAYMENT RECEIVED"
		assert statement.transactions[2].credit == Decimal("100.00")
		assert statement.transactions[2].amount == Decimal("100.00")

	finally:
		csv_path.unlink()


def test_parse_csv_amount_column():
	"""Test parsing CSV with single amount column (positive/negative)."""
	csv_content = """Date,Description,Amount,Balance
01/11/2025,Opening Balance,0.00,1000.00
10/11/2025,WOOLWORTHS 1234,-45.50,954.50
15/11/2025,PAYMENT RECEIVED,100.00,1054.50
"""
	with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
		f.write(csv_content)
		csv_path = Path(f.name)

	try:
		bank_format = BankFormat(
			name="test_bank",
			date_column="Date",
			description_column="Description",
			amount_column="Amount",
			balance_column="Balance",
			date_format="%d/%m/%Y",
		)

		statement = parse_csv(csv_path, bank_format, "Test Bank", "Business Account")

		assert len(statement.transactions) == 3
		assert statement.transactions[1].debit == Decimal("45.50")
		assert statement.transactions[2].credit == Decimal("100.00")

	finally:
		csv_path.unlink()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/bank/test_parser.py::test_parse_csv_debit_credit_columns -v`

Expected: FAIL with "ImportError: cannot import name 'parse_csv'"

**Step 3: Write minimal implementation**

Create `src/small_business/bank/parser.py`:

```python
"""CSV parsing for bank statements."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd

from small_business.bank.models import BankTransaction, ImportedBankStatement
from small_business.models.config import BankFormat


def parse_csv(
	csv_path: Path,
	bank_format: BankFormat,
	bank_name: str,
	account_name: str,
) -> ImportedBankStatement:
	"""Parse bank CSV file using provided format configuration.

	Args:
		csv_path: Path to CSV file
		bank_format: Bank format configuration
		bank_name: Name of the bank
		account_name: Name of the account

	Returns:
		ImportedBankStatement with parsed transactions
	"""
	# Read CSV
	df = pd.read_csv(csv_path)

	# Parse transactions
	transactions = []
	for _, row in df.iterrows():
		# Parse date
		date_str = str(row[bank_format.date_column])
		txn_date = datetime.strptime(date_str, bank_format.date_format).date()

		# Parse description
		description = str(row[bank_format.description_column])

		# Parse amounts
		if bank_format.amount_column:
			# Single amount column (positive = credit, negative = debit)
			amount_str = str(row[bank_format.amount_column])
			if amount_str in ("", "nan"):
				amount = Decimal("0")
			else:
				amount = Decimal(amount_str)

			if amount >= 0:
				debit = Decimal("0")
				credit = amount
			else:
				debit = -amount
				credit = Decimal("0")
		else:
			# Separate debit/credit columns
			debit_str = str(row[bank_format.debit_column]) if bank_format.debit_column else ""
			credit_str = (
				str(row[bank_format.credit_column]) if bank_format.credit_column else ""
			)

			debit = Decimal("0") if debit_str in ("", "nan") else Decimal(debit_str)
			credit = Decimal("0") if credit_str in ("", "nan") else Decimal(credit_str)

		# Parse balance (optional)
		balance = None
		if bank_format.balance_column:
			balance_str = str(row[bank_format.balance_column])
			balance = None if balance_str in ("", "nan") else Decimal(balance_str)

		# Create transaction
		txn = BankTransaction(
			date=txn_date,
			description=description,
			debit=debit,
			credit=credit,
			balance=balance,
		)
		transactions.append(txn)

	return ImportedBankStatement(
		bank_name=bank_name,
		account_name=account_name,
		transactions=transactions,
	)
```

Update `src/small_business/bank/__init__.py`:

```python
"""Bank import functionality."""

from .models import BankTransaction, ImportedBankStatement
from .parser import parse_csv

__all__ = ["BankTransaction", "ImportedBankStatement", "parse_csv"]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/bank/test_parser.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/bank/parser.py tests/bank/test_parser.py src/small_business/bank/__init__.py
git commit -m "feat: add CSV parser with bank format support

Implement parse_csv() function using Pandas to parse bank CSV files
with configurable column mappings. Supports both debit/credit columns
and single amount column formats.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: Transaction Converter (Bank → Accounting)

**Files:**
- Create: `src/small_business/bank/converter.py`
- Test: `tests/bank/test_converter.py`

**Step 1: Write the failing test**

Create `tests/bank/test_converter.py`:

```python
"""Test bank transaction converter."""

from datetime import date
from decimal import Decimal

from small_business.bank.converter import convert_to_transaction
from small_business.bank.models import BankTransaction


def test_convert_debit_transaction():
	"""Test converting bank debit to accounting transaction."""
	bank_txn = BankTransaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		debit=Decimal("45.50"),
		credit=Decimal("0"),
		balance=Decimal("954.50"),
	)

	txn = convert_to_transaction(
		bank_txn,
		bank_account_code="BANK-CHQ",
		expense_account_code="EXP-UNCLASSIFIED",
	)

	assert txn.date == date(2025, 11, 15)
	assert txn.description == "WOOLWORTHS 1234"
	assert len(txn.entries) == 2

	# Find debit and credit entries
	debit_entry = next(e for e in txn.entries if e.debit > 0)
	credit_entry = next(e for e in txn.entries if e.credit > 0)

	# Debit should be expense account (money going out)
	assert debit_entry.account_code == "EXP-UNCLASSIFIED"
	assert debit_entry.debit == Decimal("45.50")

	# Credit should be bank account (money leaving bank)
	assert credit_entry.account_code == "BANK-CHQ"
	assert credit_entry.credit == Decimal("45.50")


def test_convert_credit_transaction():
	"""Test converting bank credit to accounting transaction."""
	bank_txn = BankTransaction(
		date=date(2025, 11, 15),
		description="PAYMENT RECEIVED",
		debit=Decimal("0"),
		credit=Decimal("100.00"),
		balance=Decimal("1100.00"),
	)

	txn = convert_to_transaction(
		bank_txn,
		bank_account_code="BANK-CHQ",
		income_account_code="INC-UNCLASSIFIED",
	)

	assert len(txn.entries) == 2

	# Find debit and credit entries
	debit_entry = next(e for e in txn.entries if e.debit > 0)
	credit_entry = next(e for e in txn.entries if e.credit > 0)

	# Debit should be bank account (money entering bank)
	assert debit_entry.account_code == "BANK-CHQ"
	assert debit_entry.debit == Decimal("100.00")

	# Credit should be income account (money coming in)
	assert credit_entry.account_code == "INC-UNCLASSIFIED"
	assert credit_entry.credit == Decimal("100.00")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/bank/test_converter.py::test_convert_debit_transaction -v`

Expected: FAIL with "ImportError: cannot import name 'convert_to_transaction'"

**Step 3: Write minimal implementation**

Create `src/small_business/bank/converter.py`:

```python
"""Convert bank transactions to accounting transactions."""

from decimal import Decimal

from small_business.bank.models import BankTransaction
from small_business.models.transaction import JournalEntry, Transaction


def convert_to_transaction(
	bank_txn: BankTransaction,
	bank_account_code: str,
	expense_account_code: str = "EXP-UNCLASSIFIED",
	income_account_code: str = "INC-UNCLASSIFIED",
) -> Transaction:
	"""Convert bank transaction to accounting transaction.

	Args:
		bank_txn: Bank transaction to convert
		bank_account_code: Account code for the bank account
		expense_account_code: Default account code for expenses (debits)
		income_account_code: Default account code for income (credits)

	Returns:
		Transaction with double-entry journal entries
	"""
	amount = abs(bank_txn.amount)

	if bank_txn.is_debit:
		# Money leaving bank (expense)
		# Debit expense account, Credit bank account
		entries = [
			JournalEntry(account_code=expense_account_code, debit=amount, credit=Decimal("0")),
			JournalEntry(account_code=bank_account_code, debit=Decimal("0"), credit=amount),
		]
	else:
		# Money entering bank (income)
		# Debit bank account, Credit income account
		entries = [
			JournalEntry(account_code=bank_account_code, debit=amount, credit=Decimal("0")),
			JournalEntry(account_code=income_account_code, debit=Decimal("0"), credit=amount),
		]

	return Transaction(
		date=bank_txn.date,
		description=bank_txn.description,
		entries=entries,
	)
```

Update `src/small_business/bank/__init__.py`:

```python
"""Bank import functionality."""

from .converter import convert_to_transaction
from .models import BankTransaction, ImportedBankStatement
from .parser import parse_csv

__all__ = [
	"BankTransaction",
	"ImportedBankStatement",
	"parse_csv",
	"convert_to_transaction",
]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/bank/test_converter.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/bank/converter.py tests/bank/test_converter.py src/small_business/bank/__init__.py
git commit -m "feat: add bank transaction to accounting converter

Implement convert_to_transaction() to convert bank transactions
to double-entry accounting transactions. Handles debits (expenses)
and credits (income) with proper journal entries.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: Storage Module - Directory Structure

**Files:**
- Create: `src/small_business/storage/__init__.py`
- Create: `src/small_business/storage/paths.py`
- Test: `tests/storage/test_paths.py`

**Step 1: Write the failing test**

Create `tests/storage/test_paths.py`:

```python
"""Test storage path utilities."""

from datetime import date
from pathlib import Path

from small_business.storage.paths import (
	get_financial_year_dir,
	get_transaction_file_path,
	ensure_data_directory,
)


def test_get_financial_year_dir():
	"""Test financial year directory path generation."""
	base = Path("/data")

	# Test date in second half of year (after July)
	path = get_financial_year_dir(base, date(2025, 11, 15))
	assert path == Path("/data/2025-26")

	# Test date in first half of year (before July)
	path = get_financial_year_dir(base, date(2025, 6, 30))
	assert path == Path("/data/2024-25")

	# Test July (start of financial year)
	path = get_financial_year_dir(base, date(2025, 7, 1))
	assert path == Path("/data/2025-26")


def test_get_transaction_file_path():
	"""Test transaction file path generation."""
	base = Path("/data")

	path = get_transaction_file_path(base, date(2025, 11, 15))
	assert path == Path("/data/2025-26/transactions.jsonl")


def test_ensure_data_directory(tmp_path):
	"""Test creating data directory structure."""
	data_dir = tmp_path / "data"

	# Create structure
	ensure_data_directory(data_dir)

	# Check directories exist
	assert (data_dir / "transactions").exists()
	assert (data_dir / "receipts").exists()
	assert (data_dir / "config").exists()
	assert (data_dir / "clients").exists()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/storage/test_paths.py::test_get_financial_year_dir -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'small_business.storage'"

**Step 3: Write minimal implementation**

Create `src/small_business/storage/__init__.py`:

```python
"""Storage and data persistence."""

from .paths import ensure_data_directory, get_financial_year_dir, get_transaction_file_path

__all__ = [
	"ensure_data_directory",
	"get_financial_year_dir",
	"get_transaction_file_path",
]
```

Create `src/small_business/storage/paths.py`:

```python
"""File path utilities for data storage."""

from datetime import date
from pathlib import Path

from small_business.models.utils import get_financial_year


def get_financial_year_dir(base_path: Path, txn_date: date) -> Path:
	"""Get directory path for a financial year.

	Args:
		base_path: Base data directory
		txn_date: Transaction date

	Returns:
		Path to financial year directory (e.g., /data/2025-26)
	"""
	fy = get_financial_year(txn_date)
	return base_path / fy


def get_transaction_file_path(base_path: Path, txn_date: date) -> Path:
	"""Get file path for transaction storage.

	Args:
		base_path: Base data directory
		txn_date: Transaction date

	Returns:
		Path to transaction file (e.g., /data/2025-26/transactions.jsonl)
	"""
	fy_dir = get_financial_year_dir(base_path, txn_date)
	return fy_dir / "transactions.jsonl"


def ensure_data_directory(base_path: Path) -> None:
	"""Create data directory structure if it doesn't exist.

	Creates:
		- transactions/
		- receipts/
		- config/
		- clients/
	"""
	base_path.mkdir(parents=True, exist_ok=True)
	(base_path / "transactions").mkdir(exist_ok=True)
	(base_path / "receipts").mkdir(exist_ok=True)
	(base_path / "config").mkdir(exist_ok=True)
	(base_path / "clients").mkdir(exist_ok=True)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/storage/test_paths.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/storage/ tests/storage/
git commit -m "feat: add storage path utilities

Implement path generation for financial-year-based directory
structure and data directory initialization.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: Transaction Storage (JSONL)

**Files:**
- Create: `src/small_business/storage/transaction_store.py`
- Test: `tests/storage/test_transaction_store.py`

**Step 1: Write the failing test**

Create `tests/storage/test_transaction_store.py`:

```python
"""Test transaction storage."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.models.transaction import JournalEntry, Transaction
from small_business.storage.transaction_store import (
	save_transaction,
	load_transactions,
	transaction_exists,
)


def test_save_and_load_transaction(tmp_path):
	"""Test saving and loading a transaction."""
	data_dir = tmp_path / "data"

	txn = Transaction(
		transaction_id="TXN-20251115-001",
		date=date(2025, 11, 15),
		description="Test transaction",
		entries=[
			JournalEntry(account_code="EXP-TEST", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)

	# Save transaction
	save_transaction(txn, data_dir)

	# Check file exists
	fy_dir = data_dir / "2025-26"
	txn_file = fy_dir / "transactions.jsonl"
	assert txn_file.exists()

	# Load transactions
	loaded = load_transactions(data_dir, date(2025, 11, 15))
	assert len(loaded) == 1
	assert loaded[0].transaction_id == "TXN-20251115-001"
	assert loaded[0].description == "Test transaction"
	assert len(loaded[0].entries) == 2


def test_save_multiple_transactions(tmp_path):
	"""Test saving multiple transactions to same file."""
	data_dir = tmp_path / "data"

	txn1 = Transaction(
		transaction_id="TXN-20251115-001",
		date=date(2025, 11, 15),
		description="Transaction 1",
		entries=[
			JournalEntry(account_code="EXP-TEST", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)

	txn2 = Transaction(
		transaction_id="TXN-20251116-001",
		date=date(2025, 11, 16),
		description="Transaction 2",
		entries=[
			JournalEntry(account_code="EXP-TEST", debit=Decimal("50.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("50.00")),
		],
	)

	save_transaction(txn1, data_dir)
	save_transaction(txn2, data_dir)

	# Load all transactions
	loaded = load_transactions(data_dir, date(2025, 11, 15))
	assert len(loaded) == 2
	assert loaded[0].transaction_id == "TXN-20251115-001"
	assert loaded[1].transaction_id == "TXN-20251116-001"


def test_transaction_exists(tmp_path):
	"""Test checking if transaction already exists."""
	data_dir = tmp_path / "data"

	txn = Transaction(
		transaction_id="TXN-20251115-001",
		date=date(2025, 11, 15),
		description="Test",
		entries=[
			JournalEntry(account_code="EXP-TEST", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)

	# Should not exist initially
	assert not transaction_exists("TXN-20251115-001", data_dir, date(2025, 11, 15))

	# Save and check again
	save_transaction(txn, data_dir)
	assert transaction_exists("TXN-20251115-001", data_dir, date(2025, 11, 15))
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/storage/test_transaction_store.py::test_save_and_load_transaction -v`

Expected: FAIL with "ImportError: cannot import name 'save_transaction'"

**Step 3: Write minimal implementation**

Create `src/small_business/storage/transaction_store.py`:

```python
"""Transaction storage using JSONL format."""

import json
from datetime import date
from pathlib import Path

from small_business.models.transaction import Transaction
from small_business.storage.paths import get_financial_year_dir


def save_transaction(txn: Transaction, data_dir: Path) -> None:
	"""Save transaction to JSONL file.

	Args:
		txn: Transaction to save
		data_dir: Base data directory
	"""
	# Get financial year directory
	fy_dir = get_financial_year_dir(data_dir, txn.date)
	fy_dir.mkdir(parents=True, exist_ok=True)

	# Append to JSONL file
	txn_file = fy_dir / "transactions.jsonl"
	with open(txn_file, "a") as f:
		json_str = txn.model_dump_json()
		f.write(json_str + "\n")


def load_transactions(data_dir: Path, txn_date: date) -> list[Transaction]:
	"""Load all transactions for a financial year.

	Args:
		data_dir: Base data directory
		txn_date: Any date in the financial year to load

	Returns:
		List of transactions
	"""
	fy_dir = get_financial_year_dir(data_dir, txn_date)
	txn_file = fy_dir / "transactions.jsonl"

	if not txn_file.exists():
		return []

	transactions = []
	with open(txn_file) as f:
		for line in f:
			line = line.strip()
			if line:
				data = json.loads(line)
				txn = Transaction.model_validate(data)
				transactions.append(txn)

	return transactions


def transaction_exists(txn_id: str, data_dir: Path, txn_date: date) -> bool:
	"""Check if transaction ID already exists.

	Args:
		txn_id: Transaction ID to check
		data_dir: Base data directory
		txn_date: Date to determine financial year

	Returns:
		True if transaction exists
	"""
	transactions = load_transactions(data_dir, txn_date)
	return any(txn.transaction_id == txn_id for txn in transactions)
```

Update `src/small_business/storage/__init__.py`:

```python
"""Storage and data persistence."""

from .paths import ensure_data_directory, get_financial_year_dir, get_transaction_file_path
from .transaction_store import load_transactions, save_transaction, transaction_exists

__all__ = [
	"ensure_data_directory",
	"get_financial_year_dir",
	"get_transaction_file_path",
	"save_transaction",
	"load_transactions",
	"transaction_exists",
]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/storage/test_transaction_store.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/storage/transaction_store.py tests/storage/test_transaction_store.py src/small_business/storage/__init__.py
git commit -m "feat: add transaction JSONL storage

Implement save/load functionality for transactions using JSONL
format in financial-year-based directories. Includes duplicate
detection via transaction_exists().

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 7: Duplicate Detection

**Files:**
- Create: `src/small_business/bank/duplicate.py`
- Test: `tests/bank/test_duplicate.py`

**Step 1: Write the failing test**

Create `tests/bank/test_duplicate.py`:

```python
"""Test duplicate detection."""

from datetime import date
from decimal import Decimal

from small_business.bank.duplicate import generate_transaction_hash, is_duplicate
from small_business.bank.models import BankTransaction, ImportedBankStatement


def test_generate_transaction_hash_same():
	"""Test identical transactions generate same hash."""
	txn1 = BankTransaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		debit=Decimal("45.50"),
		credit=Decimal("0"),
		balance=Decimal("954.50"),
	)

	txn2 = BankTransaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		debit=Decimal("45.50"),
		credit=Decimal("0"),
		balance=Decimal("1000.00"),  # Different balance
	)

	# Same hash despite different balance
	assert generate_transaction_hash(txn1) == generate_transaction_hash(txn2)


def test_generate_transaction_hash_different():
	"""Test different transactions generate different hashes."""
	txn1 = BankTransaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		debit=Decimal("45.50"),
		credit=Decimal("0"),
	)

	txn2 = BankTransaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		debit=Decimal("45.51"),  # Different amount
		credit=Decimal("0"),
	)

	assert generate_transaction_hash(txn1) != generate_transaction_hash(txn2)


def test_is_duplicate():
	"""Test duplicate detection in existing statements."""
	existing = [
		ImportedBankStatement(
			bank_name="Test",
			account_name="Test",
			transactions=[
				BankTransaction(
					date=date(2025, 11, 1),
					description="WOOLWORTHS",
					debit=Decimal("50.00"),
					credit=Decimal("0"),
				),
				BankTransaction(
					date=date(2025, 11, 2),
					description="COLES",
					debit=Decimal("30.00"),
					credit=Decimal("0"),
				),
			],
		)
	]

	# Duplicate transaction
	dup = BankTransaction(
		date=date(2025, 11, 1),
		description="WOOLWORTHS",
		debit=Decimal("50.00"),
		credit=Decimal("0"),
	)

	# New transaction
	new = BankTransaction(
		date=date(2025, 11, 3),
		description="ALDI",
		debit=Decimal("20.00"),
		credit=Decimal("0"),
	)

	assert is_duplicate(dup, existing)
	assert not is_duplicate(new, existing)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/bank/test_duplicate.py::test_generate_transaction_hash_same -v`

Expected: FAIL with "ImportError: cannot import name 'generate_transaction_hash'"

**Step 3: Write minimal implementation**

Create `src/small_business/bank/duplicate.py`:

```python
"""Duplicate transaction detection."""

import hashlib

from small_business.bank.models import BankTransaction, ImportedBankStatement


def generate_transaction_hash(txn: BankTransaction) -> str:
	"""Generate hash for duplicate detection.

	Hash is based on: date, description, amount (ignores balance).

	Args:
		txn: Bank transaction

	Returns:
		SHA256 hash string
	"""
	# Create hash from date, description, and amount
	hash_input = f"{txn.date.isoformat()}|{txn.description}|{txn.amount}"
	return hashlib.sha256(hash_input.encode()).hexdigest()


def is_duplicate(
	txn: BankTransaction,
	existing_statements: list[ImportedBankStatement],
) -> bool:
	"""Check if transaction is a duplicate.

	Args:
		txn: Transaction to check
		existing_statements: Previously imported statements

	Returns:
		True if transaction already exists
	"""
	txn_hash = generate_transaction_hash(txn)

	for stmt in existing_statements:
		for existing_txn in stmt.transactions:
			if generate_transaction_hash(existing_txn) == txn_hash:
				return True

	return False
```

Update `src/small_business/bank/__init__.py`:

```python
"""Bank import functionality."""

from .converter import convert_to_transaction
from .duplicate import generate_transaction_hash, is_duplicate
from .models import BankTransaction, ImportedBankStatement
from .parser import parse_csv

__all__ = [
	"BankTransaction",
	"ImportedBankStatement",
	"parse_csv",
	"convert_to_transaction",
	"generate_transaction_hash",
	"is_duplicate",
]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/bank/test_duplicate.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/bank/duplicate.py tests/bank/test_duplicate.py src/small_business/bank/__init__.py
git commit -m "feat: add duplicate transaction detection

Implement hash-based duplicate detection using date, description,
and amount. Balance is excluded to match same transaction from
different statement downloads.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 8: Bank Import Workflow Orchestrator

**Files:**
- Create: `src/small_business/bank/import_workflow.py`
- Test: `tests/bank/test_import_workflow.py`

**Step 1: Write the failing test**

Create `tests/bank/test_import_workflow.py`:

```python
"""Test bank import workflow orchestrator."""

import tempfile
from datetime import date
from pathlib import Path

from small_business.bank.import_workflow import import_bank_statement
from small_business.models.config import BankFormat
from small_business.storage.transaction_store import load_transactions


def test_import_bank_statement_full_workflow(tmp_path):
	"""Test complete bank import workflow."""
	# Create test CSV
	csv_content = """Date,Description,Debit,Credit,Balance
01/11/2025,Opening Balance,,,1000.00
10/11/2025,WOOLWORTHS 1234,45.50,,954.50
15/11/2025,PAYMENT RECEIVED,,100.00,1054.50
"""
	with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
		f.write(csv_content)
		csv_path = Path(f.name)

	try:
		data_dir = tmp_path / "data"

		bank_format = BankFormat(
			name="test_bank",
			date_column="Date",
			description_column="Description",
			debit_column="Debit",
			credit_column="Credit",
			balance_column="Balance",
			date_format="%d/%m/%Y",
		)

		# Import statement
		result = import_bank_statement(
			csv_path=csv_path,
			bank_format=bank_format,
			bank_name="Test Bank",
			account_name="Business Cheque",
			bank_account_code="BANK-CHQ",
			data_dir=data_dir,
		)

		assert result["imported"] == 3
		assert result["duplicates"] == 0

		# Verify transactions were saved
		transactions = load_transactions(data_dir, date(2025, 11, 15))
		assert len(transactions) == 3

		# Check first transaction (opening balance)
		assert transactions[0].description == "Opening Balance"

		# Check second transaction (debit)
		assert transactions[1].description == "WOOLWORTHS 1234"
		assert len(transactions[1].entries) == 2

		# Check third transaction (credit)
		assert transactions[2].description == "PAYMENT RECEIVED"

	finally:
		csv_path.unlink()


def test_import_duplicate_detection(tmp_path):
	"""Test duplicate detection during import."""
	csv_content = """Date,Description,Debit,Credit,Balance
10/11/2025,WOOLWORTHS 1234,45.50,,954.50
"""
	with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
		f.write(csv_content)
		csv_path = Path(f.name)

	try:
		data_dir = tmp_path / "data"

		bank_format = BankFormat(
			name="test_bank",
			date_column="Date",
			description_column="Description",
			debit_column="Debit",
			credit_column="Credit",
			balance_column="Balance",
			date_format="%d/%m/%Y",
		)

		# First import
		result1 = import_bank_statement(
			csv_path=csv_path,
			bank_format=bank_format,
			bank_name="Test Bank",
			account_name="Business Cheque",
			bank_account_code="BANK-CHQ",
			data_dir=data_dir,
		)

		assert result1["imported"] == 1
		assert result1["duplicates"] == 0

		# Second import (should detect duplicate)
		result2 = import_bank_statement(
			csv_path=csv_path,
			bank_format=bank_format,
			bank_name="Test Bank",
			account_name="Business Cheque",
			bank_account_code="BANK-CHQ",
			data_dir=data_dir,
		)

		assert result2["imported"] == 0
		assert result2["duplicates"] == 1

		# Should still only have 1 transaction
		transactions = load_transactions(data_dir, date(2025, 11, 10))
		assert len(transactions) == 1

	finally:
		csv_path.unlink()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/bank/test_import_workflow.py::test_import_bank_statement_full_workflow -v`

Expected: FAIL with "ImportError: cannot import name 'import_bank_statement'"

**Step 3: Write minimal implementation**

Create `src/small_business/bank/import_workflow.py`:

```python
"""Bank import workflow orchestration."""

from pathlib import Path

from small_business.bank.converter import convert_to_transaction
from small_business.bank.duplicate import is_duplicate
from small_business.bank.models import ImportedBankStatement
from small_business.bank.parser import parse_csv
from small_business.models.config import BankFormat
from small_business.storage.transaction_store import load_transactions, save_transaction


def import_bank_statement(
	csv_path: Path,
	bank_format: BankFormat,
	bank_name: str,
	account_name: str,
	bank_account_code: str,
	data_dir: Path,
	expense_account_code: str = "EXP-UNCLASSIFIED",
	income_account_code: str = "INC-UNCLASSIFIED",
) -> dict[str, int]:
	"""Import bank statement CSV to accounting transactions.

	Workflow:
	1. Parse CSV using bank format
	2. Check for duplicates
	3. Convert to accounting transactions
	4. Save to storage

	Args:
		csv_path: Path to CSV file
		bank_format: Bank format configuration
		bank_name: Name of bank
		account_name: Name of account
		bank_account_code: Account code for bank account
		data_dir: Data directory for storage
		expense_account_code: Default account for expenses
		income_account_code: Default account for income

	Returns:
		Dictionary with import statistics:
		- imported: Number of new transactions imported
		- duplicates: Number of duplicates skipped
	"""
	# Parse CSV
	statement = parse_csv(csv_path, bank_format, bank_name, account_name)

	# Load existing transactions to check duplicates
	# Get all transactions from the financial year(s) covered by this statement
	existing_statements: list[ImportedBankStatement] = []
	if statement.transactions:
		# We'll check duplicates by loading all transactions from relevant financial years
		# For simplicity, load from the first transaction's date
		first_date = statement.transactions[0].date
		existing_txns = load_transactions(data_dir, first_date)

		# Convert to ImportedBankStatement format for duplicate checking
		if existing_txns:
			# Group by date for statement format (simplified)
			from small_business.bank.models import BankTransaction

			bank_txns = []
			for txn in existing_txns:
				# Reconstruct approximate bank transaction from accounting transaction
				# This is simplified - just need for duplicate detection
				amount = sum(e.debit for e in txn.entries) - sum(e.credit for e in txn.entries)
				bank_txn = BankTransaction(
					date=txn.date,
					description=txn.description,
					debit=abs(amount) if amount < 0 else 0,
					credit=amount if amount > 0 else 0,
				)
				bank_txns.append(bank_txn)

			existing_statements.append(
				ImportedBankStatement(
					bank_name=bank_name,
					account_name=account_name,
					transactions=bank_txns,
				)
			)

	# Import transactions
	imported = 0
	duplicates = 0

	for bank_txn in statement.transactions:
		# Check duplicate
		if is_duplicate(bank_txn, existing_statements):
			duplicates += 1
			continue

		# Convert to accounting transaction
		accounting_txn = convert_to_transaction(
			bank_txn,
			bank_account_code=bank_account_code,
			expense_account_code=expense_account_code,
			income_account_code=income_account_code,
		)

		# Save transaction
		save_transaction(accounting_txn, data_dir)
		imported += 1

	return {"imported": imported, "duplicates": duplicates}
```

Update `src/small_business/bank/__init__.py`:

```python
"""Bank import functionality."""

from .converter import convert_to_transaction
from .duplicate import generate_transaction_hash, is_duplicate
from .import_workflow import import_bank_statement
from .models import BankTransaction, ImportedBankStatement
from .parser import parse_csv

__all__ = [
	"BankTransaction",
	"ImportedBankStatement",
	"parse_csv",
	"convert_to_transaction",
	"generate_transaction_hash",
	"is_duplicate",
	"import_bank_statement",
]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/bank/test_import_workflow.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/bank/import_workflow.py tests/bank/test_import_workflow.py src/small_business/bank/__init__.py
git commit -m "feat: add bank import workflow orchestrator

Implement complete import workflow: parse CSV, detect duplicates,
convert to accounting transactions, and save to storage. Returns
import statistics for reporting.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 9: Update Documentation

**Files:**
- Create: `docs/usage/bank-import.md`
- Modify: `mkdocs.yml` (add navigation entry)

**Step 1: Write documentation**

Create `docs/usage/bank-import.md`:

```markdown
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
```

**Step 2: Update mkdocs.yml**

Add to navigation section in `mkdocs.yml`:

```yaml
nav:
  - Home: index.md
  - Changelog: CHANGELOG.md
  - Usage:
    - Bank Import: usage/bank-import.md
  - API Reference:
    - Hello module: api_docs/hello_world.md
  - Examples:
    - Notebooks:
      - 1. Notebook example: notebooks/example.py
```

**Step 3: Test documentation builds**

Run: `mkdocs build`

Expected: Success with no errors

**Step 4: Commit**

```bash
git add docs/usage/bank-import.md mkdocs.yml
git commit -m "docs: add bank import guide

Document bank import workflow, format configuration, storage
structure, and duplicate detection for Phase 2.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 10: Integration Test

**Files:**
- Create: `tests/integration/test_bank_import_integration.py`

**Step 1: Write integration test**

Create `tests/integration/test_bank_import_integration.py`:

```python
"""Integration test for complete bank import workflow."""

import tempfile
from datetime import date
from pathlib import Path

from small_business.bank import import_bank_statement
from small_business.models.config import BankFormat
from small_business.storage.transaction_store import load_transactions


def test_complete_bank_import_workflow(tmp_path):
	"""Test end-to-end bank import with multiple statements."""
	data_dir = tmp_path / "data"

	bank_format = BankFormat(
		name="test_bank",
		date_column="Date",
		description_column="Description",
		debit_column="Debit",
		credit_column="Credit",
		balance_column="Balance",
		date_format="%d/%m/%Y",
	)

	# First statement (November 2025)
	csv1 = """Date,Description,Debit,Credit,Balance
01/11/2025,Opening Balance,,,1000.00
10/11/2025,WOOLWORTHS 1234,45.50,,954.50
15/11/2025,PAYMENT RECEIVED,,500.00,1454.50
20/11/2025,QANTAS FLIGHT,280.00,,1174.50
"""

	with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
		f.write(csv1)
		csv1_path = Path(f.name)

	try:
		result1 = import_bank_statement(
			csv_path=csv1_path,
			bank_format=bank_format,
			bank_name="Test Bank",
			account_name="Business Cheque",
			bank_account_code="BANK-CHQ",
			data_dir=data_dir,
		)

		assert result1["imported"] == 4
		assert result1["duplicates"] == 0

		# Verify all transactions saved
		transactions = load_transactions(data_dir, date(2025, 11, 15))
		assert len(transactions) == 4

		# Verify double-entry structure
		for txn in transactions:
			assert len(txn.entries) == 2
			total_debit = sum(e.debit for e in txn.entries)
			total_credit = sum(e.credit for e in txn.entries)
			assert total_debit == total_credit

		# Verify financial year
		assert transactions[0].financial_year == "2025-26"

	finally:
		csv1_path.unlink()

	# Second statement (overlapping dates - should detect duplicates)
	csv2 = """Date,Description,Debit,Credit,Balance
15/11/2025,PAYMENT RECEIVED,,500.00,1454.50
20/11/2025,QANTAS FLIGHT,280.00,,1174.50
25/11/2025,TELSTRA PHONE,85.00,,1089.50
"""

	with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
		f.write(csv2)
		csv2_path = Path(f.name)

	try:
		result2 = import_bank_statement(
			csv_path=csv2_path,
			bank_format=bank_format,
			bank_name="Test Bank",
			account_name="Business Cheque",
			bank_account_code="BANK-CHQ",
			data_dir=data_dir,
		)

		# Should import only the new transaction
		assert result2["imported"] == 1
		assert result2["duplicates"] == 2

		# Verify total count
		transactions = load_transactions(data_dir, date(2025, 11, 15))
		assert len(transactions) == 5

	finally:
		csv2_path.unlink()


def test_cross_financial_year_import(tmp_path):
	"""Test importing transactions across financial year boundary."""
	data_dir = tmp_path / "data"

	bank_format = BankFormat(
		name="test_bank",
		date_column="Date",
		description_column="Description",
		debit_column="Debit",
		credit_column="Credit",
		date_format="%d/%m/%Y",
	)

	# Statement spanning financial year boundary (June-July)
	csv = """Date,Description,Debit,Credit
30/06/2025,END OF YEAR,100.00,
01/07/2025,START OF YEAR,150.00,
"""

	with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
		f.write(csv)
		csv_path = Path(f.name)

	try:
		result = import_bank_statement(
			csv_path=csv_path,
			bank_format=bank_format,
			bank_name="Test Bank",
			account_name="Business Cheque",
			bank_account_code="BANK-CHQ",
			data_dir=data_dir,
		)

		assert result["imported"] == 2

		# Check transactions are in correct financial years
		fy_2024_25 = load_transactions(data_dir, date(2025, 6, 30))
		fy_2025_26 = load_transactions(data_dir, date(2025, 7, 1))

		assert len(fy_2024_25) == 1
		assert len(fy_2025_26) == 1

		assert fy_2024_25[0].financial_year == "2024-25"
		assert fy_2025_26[0].financial_year == "2025-26"

	finally:
		csv_path.unlink()
```

**Step 2: Run integration test**

Run: `uv run pytest tests/integration/test_bank_import_integration.py -v`

Expected: PASS (all tests)

**Step 3: Commit**

```bash
git add tests/integration/
git commit -m "test: add bank import integration tests

Add end-to-end integration tests covering complete import workflow,
duplicate detection, and cross-financial-year transactions.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Summary

Phase 2 implementation delivers:

✅ **Bank format configuration** - Flexible CSV parsing for different banks
✅ **CSV parser** - Handles debit/credit and amount column formats
✅ **Transaction converter** - Bank transactions → double-entry accounting
✅ **JSONL storage** - Financial-year-based transaction persistence
✅ **Duplicate detection** - Hash-based deduplication for re-imports
✅ **Import workflow** - Complete orchestration with statistics
✅ **Documentation** - Usage guide for bank imports
✅ **Integration tests** - End-to-end workflow validation

**Next Phase:** Phase 3 will implement expense classification with rules engine and user acceptance workflow.

---

## Verification Checklist

Before marking Phase 2 complete, verify:

- [ ] All tests pass: `uv run pytest`
- [ ] Code quality: `uv run ruff check .`
- [ ] Formatting: `uv run ruff format .`
- [ ] Documentation builds: `mkdocs build`
- [ ] Manual test: Import a real bank CSV file
- [ ] Check storage structure created correctly
- [ ] Verify duplicate detection works across imports
