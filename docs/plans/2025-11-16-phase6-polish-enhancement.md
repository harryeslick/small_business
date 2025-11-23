# Phase 6: Polish & Enhancement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Polish the application with data validation improvements, backup/restore functionality, Git integration for version control, and performance optimization.

**Architecture:** Implement comprehensive data validation across all workflows, create backup/restore utilities, integrate Git for automatic versioning of data changes, add data integrity checks, and optimize transaction queries for large datasets.

**Tech Stack:** Python 3.13+, GitPython (Git integration), Pydantic validation

---

## Task 1: Enhanced Data Validation

**Files:**
- Create: `src/small_business/validation/__init__.py`
- Create: `src/small_business/validation/validators.py`
- Test: `tests/validation/test_validators.py`

**Step 1: Write the failing test**

Create `tests/validation/test_validators.py`:

```python
"""Test data validation utilities."""

from datetime import date
from decimal import Decimal

from small_business.models import Invoice, Job, JobStatus, LineItem, Quote, QuoteStatus
from small_business.validation.validators import (
	validate_quote_can_convert_to_job,
	validate_job_can_create_invoice,
	validate_invoice_payment,
	ValidationError,
)


def test_validate_quote_can_convert_to_job():
	"""Test validating quote can be converted to job."""
	# Valid: accepted quote
	quote_accepted = Quote(
		quote_id="Q-001",
		client_id="C-001",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		status=QuoteStatus.ACCEPTED,
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)

	validate_quote_can_convert_to_job(quote_accepted)  # Should not raise

	# Invalid: draft quote
	quote_draft = Quote(
		quote_id="Q-002",
		client_id="C-001",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		status=QuoteStatus.DRAFT,
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)

	try:
		validate_quote_can_convert_to_job(quote_draft)
		assert False, "Should raise ValidationError"
	except ValidationError as e:
		assert "not accepted" in str(e).lower()


def test_validate_job_can_create_invoice():
	"""Test validating job can create invoice."""
	# Valid: completed job
	job_completed = Job(
		job_id="J-001",
		client_id="C-001",
		date_accepted=date(2025, 11, 16),
		status=JobStatus.COMPLETED,
	)

	validate_job_can_create_invoice(job_completed)  # Should not raise

	# Invalid: scheduled job
	job_scheduled = Job(
		job_id="J-002",
		client_id="C-001",
		date_accepted=date(2025, 11, 16),
		status=JobStatus.SCHEDULED,
	)

	try:
		validate_job_can_create_invoice(job_scheduled)
		assert False, "Should raise ValidationError"
	except ValidationError as e:
		assert "not completed" in str(e).lower()


def test_validate_invoice_payment():
	"""Test validating invoice payment."""
	invoice = Invoice(
		invoice_id="INV-001",
		client_id="C-001",
		date_issued=date(2025, 11, 16),
		date_due=date(2025, 12, 16),
		line_items=[LineItem(description="Service", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)

	# Valid: payment equals total
	validate_invoice_payment(invoice, Decimal("110.00"))  # 100 + 10 GST

	# Invalid: payment exceeds total
	try:
		validate_invoice_payment(invoice, Decimal("200.00"))
		assert False, "Should raise ValidationError"
	except ValidationError as e:
		assert "exceeds" in str(e).lower()

	# Invalid: negative payment
	try:
		validate_invoice_payment(invoice, Decimal("-10.00"))
		assert False, "Should raise ValidationError"
	except ValidationError as e:
		assert "negative" in str(e).lower()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/validation/test_validators.py::test_validate_quote_can_convert_to_job -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'small_business.validation'"

**Step 3: Write minimal implementation**

Create `src/small_business/validation/__init__.py`:

```python
"""Data validation utilities."""

from .validators import (
	ValidationError,
	validate_invoice_payment,
	validate_job_can_create_invoice,
	validate_quote_can_convert_to_job,
)

__all__ = [
	"ValidationError",
	"validate_quote_can_convert_to_job",
	"validate_job_can_create_invoice",
	"validate_invoice_payment",
]
```

Create `src/small_business/validation/validators.py`:

```python
"""Data validation functions."""

from decimal import Decimal

from small_business.models import Invoice, Job, JobStatus, Quote, QuoteStatus


class ValidationError(Exception):
	"""Raised when validation fails."""

	pass


def validate_quote_can_convert_to_job(quote: Quote) -> None:
	"""Validate that a quote can be converted to a job.

	Args:
		quote: Quote to validate

	Raises:
		ValidationError: If quote cannot be converted
	"""
	if quote.status != QuoteStatus.ACCEPTED:
		raise ValidationError(f"Quote {quote.quote_id} is not accepted (status: {quote.status})")

	if not quote.line_items:
		raise ValidationError(f"Quote {quote.quote_id} has no line items")


def validate_job_can_create_invoice(job: Job) -> None:
	"""Validate that a job can create an invoice.

	Args:
		job: Job to validate

	Raises:
		ValidationError: If job cannot create invoice
	"""
	if job.status != JobStatus.COMPLETED:
		raise ValidationError(f"Job {job.job_id} is not completed (status: {job.status})")


def validate_invoice_payment(invoice: Invoice, payment_amount: Decimal) -> None:
	"""Validate invoice payment amount.

	Args:
		invoice: Invoice to validate payment for
		payment_amount: Payment amount to validate

	Raises:
		ValidationError: If payment amount is invalid
	"""
	if payment_amount < Decimal("0"):
		raise ValidationError("Payment amount cannot be negative")

	if payment_amount > invoice.total:
		raise ValidationError(
			f"Payment amount ${payment_amount} exceeds invoice total ${invoice.total}"
		)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/validation/test_validators.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/validation/ tests/validation/
git commit -m "feat: add enhanced data validation

Implement validation functions for workflow transitions
(quote→job→invoice) and payment validation with clear
error messages.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Data Integrity Checks

**Files:**
- Create: `src/small_business/validation/integrity.py`
- Test: `tests/validation/test_integrity.py`

**Step 1: Write the failing test**

Create `tests/validation/test_integrity.py`:

```python
"""Test data integrity checks."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.models import JournalEntry, Transaction
from small_business.storage.transaction_store import save_transaction
from small_business.validation.integrity import (
	check_transactions_balanced,
	find_orphaned_references,
	verify_data_integrity,
)


def test_check_transactions_balanced(tmp_path):
	"""Test checking all transactions are balanced."""
	data_dir = tmp_path / "data"

	# Balanced transaction
	txn1 = Transaction(
		date=date(2025, 11, 15),
		description="Balanced",
		entries=[
			JournalEntry(account_code="EXP-TEST", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)
	save_transaction(txn1, data_dir)

	result = check_transactions_balanced(data_dir, date(2025, 11, 15))
	assert result["balanced"] is True
	assert len(result["unbalanced_transactions"]) == 0


def test_find_orphaned_references(tmp_path):
	"""Test finding orphaned job/invoice references."""
	from small_business.models import Invoice, Job, LineItem
	from small_business.storage.invoice_store import save_invoice
	from small_business.storage.job_store import save_job

	data_dir = tmp_path / "data"

	# Job with non-existent quote reference
	job = Job(
		job_id="J-001",
		quote_id="Q-NONEXISTENT",  # Orphaned reference
		client_id="C-001",
		date_accepted=date(2025, 11, 16),
	)
	save_job(job, data_dir)

	# Invoice with non-existent job reference
	invoice = Invoice(
		invoice_id="INV-001",
		job_id="J-NONEXISTENT",  # Orphaned reference
		client_id="C-001",
		date_issued=date(2025, 11, 16),
		date_due=date(2025, 12, 16),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)
	save_invoice(invoice, data_dir)

	orphans = find_orphaned_references(data_dir, date(2025, 11, 16))

	assert len(orphans["jobs_with_missing_quotes"]) == 1
	assert len(orphans["invoices_with_missing_jobs"]) == 1


def test_verify_data_integrity(tmp_path):
	"""Test complete data integrity verification."""
	data_dir = tmp_path / "data"

	# Save a balanced transaction
	txn = Transaction(
		date=date(2025, 11, 15),
		description="Test",
		entries=[
			JournalEntry(account_code="EXP-TEST", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)
	save_transaction(txn, data_dir)

	result = verify_data_integrity(data_dir, date(2025, 11, 15))

	assert result["transactions_balanced"] is True
	assert result["total_checks"] >= 2  # At least transactions and references
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/validation/test_integrity.py::test_check_transactions_balanced -v`

Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `src/small_business/validation/integrity.py`:

```python
"""Data integrity checking functions."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.storage.invoice_store import load_invoices
from small_business.storage.job_store import load_jobs
from small_business.storage.quote_store import load_quotes
from small_business.storage.transaction_store import load_transactions


def check_transactions_balanced(data_dir: Path, as_of_date: date) -> dict:
	"""Check that all transactions are balanced.

	Args:
		data_dir: Data directory
		as_of_date: Check transactions up to this date

	Returns:
		Dictionary with balanced status and list of unbalanced transactions
	"""
	transactions = load_transactions(data_dir, as_of_date)

	unbalanced = []
	for txn in transactions:
		total_debits = sum(entry.debit for entry in txn.entries)
		total_credits = sum(entry.credit for entry in txn.entries)

		if total_debits != total_credits:
			unbalanced.append(
				{
					"transaction_id": txn.transaction_id,
					"date": txn.date,
					"description": txn.description,
					"debits": total_debits,
					"credits": total_credits,
					"difference": total_debits - total_credits,
				}
			)

	return {"balanced": len(unbalanced) == 0, "unbalanced_transactions": unbalanced}


def find_orphaned_references(data_dir: Path, as_of_date: date) -> dict:
	"""Find orphaned references (jobs without quotes, invoices without jobs).

	Args:
		data_dir: Data directory
		as_of_date: Check data up to this date

	Returns:
		Dictionary with lists of orphaned references
	"""
	quotes = load_quotes(data_dir, as_of_date)
	jobs = load_jobs(data_dir, as_of_date)
	invoices = load_invoices(data_dir, as_of_date)

	quote_ids = {q.quote_id for q in quotes}
	job_ids = {j.job_id for j in jobs}

	# Find jobs with missing quote references
	jobs_with_missing_quotes = []
	for job in jobs:
		if job.quote_id and job.quote_id not in quote_ids:
			jobs_with_missing_quotes.append(
				{"job_id": job.job_id, "missing_quote_id": job.quote_id}
			)

	# Find invoices with missing job references
	invoices_with_missing_jobs = []
	for invoice in invoices:
		if invoice.job_id and invoice.job_id not in job_ids:
			invoices_with_missing_jobs.append(
				{"invoice_id": invoice.invoice_id, "missing_job_id": invoice.job_id}
			)

	return {
		"jobs_with_missing_quotes": jobs_with_missing_quotes,
		"invoices_with_missing_jobs": invoices_with_missing_jobs,
	}


def verify_data_integrity(data_dir: Path, as_of_date: date) -> dict:
	"""Run all data integrity checks.

	Args:
		data_dir: Data directory
		as_of_date: Check data up to this date

	Returns:
		Dictionary with results of all integrity checks
	"""
	results = {}

	# Check transactions balanced
	balance_check = check_transactions_balanced(data_dir, as_of_date)
	results["transactions_balanced"] = balance_check["balanced"]
	results["unbalanced_transactions"] = balance_check["unbalanced_transactions"]

	# Check for orphaned references
	orphans = find_orphaned_references(data_dir, as_of_date)
	results["orphaned_references"] = orphans

	# Count total checks run
	results["total_checks"] = 2

	# Overall status
	results["all_checks_passed"] = (
		results["transactions_balanced"] and len(orphans["jobs_with_missing_quotes"]) == 0 and len(orphans["invoices_with_missing_jobs"]) == 0
	)

	return results
```

Update `src/small_business/validation/__init__.py` to add exports.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/validation/test_integrity.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/validation/integrity.py tests/validation/test_integrity.py src/small_business/validation/__init__.py
git commit -m "feat: add data integrity checks

Implement comprehensive integrity checks for balanced
transactions and orphaned references with detailed reporting.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Git Integration for Data Versioning

**Files:**
- Create: `src/small_business/backup/__init__.py`
- Create: `src/small_business/backup/git_integration.py`
- Test: `tests/backup/test_git_integration.py`

**Step 1: Write the failing test**

Create `tests/backup/test_git_integration.py`:

```python
"""Test Git integration for data versioning."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.backup.git_integration import (
	init_git_repo,
	commit_data_changes,
	get_commit_history,
)
from small_business.models import JournalEntry, Transaction
from small_business.storage.transaction_store import save_transaction


def test_init_git_repo(tmp_path):
	"""Test initializing Git repository."""
	data_dir = tmp_path / "data"
	data_dir.mkdir()

	init_git_repo(data_dir)

	# Check .git directory exists
	assert (data_dir / ".git").exists()


def test_commit_data_changes(tmp_path):
	"""Test committing data changes to Git."""
	data_dir = tmp_path / "data"
	data_dir.mkdir()

	# Initialize Git
	init_git_repo(data_dir)

	# Save a transaction
	txn = Transaction(
		date=date(2025, 11, 15),
		description="Test transaction",
		entries=[
			JournalEntry(account_code="EXP-TEST", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)
	save_transaction(txn, data_dir)

	# Commit changes
	commit_hash = commit_data_changes(data_dir, "Add test transaction")

	assert commit_hash is not None
	assert len(commit_hash) > 0


def test_get_commit_history(tmp_path):
	"""Test getting commit history."""
	data_dir = tmp_path / "data"
	data_dir.mkdir()

	# Initialize and make commits
	init_git_repo(data_dir)

	txn1 = Transaction(
		date=date(2025, 11, 15),
		description="Transaction 1",
		entries=[
			JournalEntry(account_code="EXP-TEST", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)
	save_transaction(txn1, data_dir)
	commit_data_changes(data_dir, "Add transaction 1")

	txn2 = Transaction(
		date=date(2025, 11, 16),
		description="Transaction 2",
		entries=[
			JournalEntry(account_code="EXP-TEST", debit=Decimal("50.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("50.00")),
		],
	)
	save_transaction(txn2, data_dir)
	commit_data_changes(data_dir, "Add transaction 2")

	# Get history
	history = get_commit_history(data_dir, limit=10)

	assert len(history) >= 2  # At least our 2 commits (might have initial commit)
	assert "Add transaction 2" in [h["message"] for h in history]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/backup/test_git_integration.py::test_init_git_repo -v`

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `src/small_business/backup/__init__.py`:

```python
"""Backup and version control functionality."""

from .git_integration import commit_data_changes, get_commit_history, init_git_repo

__all__ = ["init_git_repo", "commit_data_changes", "get_commit_history"]
```

Create `src/small_business/backup/git_integration.py`:

```python
"""Git integration for automatic data versioning."""

from pathlib import Path

import git


def init_git_repo(data_dir: Path) -> None:
	"""Initialize Git repository in data directory.

	Args:
		data_dir: Data directory to initialize Git in
	"""
	git_dir = data_dir / ".git"

	if git_dir.exists():
		return  # Already initialized

	repo = git.Repo.init(data_dir)

	# Create .gitignore to avoid ignoring data files
	gitignore = data_dir / ".gitignore"
	if not gitignore.exists():
		gitignore.write_text("# Git is used for data versioning, not ignoring\n")

	# Initial commit
	repo.index.add([".gitignore"])
	repo.index.commit("Initial commit - setup data versioning")


def commit_data_changes(data_dir: Path, message: str) -> str | None:
	"""Commit all data changes to Git.

	Args:
		data_dir: Data directory with Git repo
		message: Commit message

	Returns:
		Commit hash, or None if no changes
	"""
	repo = git.Repo(data_dir)

	# Add all changes
	repo.git.add(A=True)

	# Check if there are changes to commit
	if not repo.is_dirty() and not repo.untracked_files:
		return None  # No changes

	# Commit
	commit = repo.index.commit(message)
	return commit.hexsha


def get_commit_history(data_dir: Path, limit: int = 20) -> list[dict]:
	"""Get commit history.

	Args:
		data_dir: Data directory with Git repo
		limit: Maximum number of commits to return

	Returns:
		List of commit dictionaries with hash, message, date, author
	"""
	repo = git.Repo(data_dir)

	commits = []
	for commit in repo.iter_commits(max_count=limit):
		commits.append(
			{
				"hash": commit.hexsha,
				"short_hash": commit.hexsha[:7],
				"message": commit.message.strip(),
				"date": commit.committed_datetime,
				"author": commit.author.name,
			}
		)

	return commits
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/backup/test_git_integration.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/backup/ tests/backup/
git commit -m "feat: add Git integration for data versioning

Implement automatic Git commits for data changes with
commit history retrieval for audit trail and recovery.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: Backup and Restore Utilities

**Files:**
- Create: `src/small_business/backup/backup_restore.py`
- Test: `tests/backup/test_backup_restore.py`

**Step 1: Write the failing test**

Create `tests/backup/test_backup_restore.py`:

```python
"""Test backup and restore functionality."""

import shutil
from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.backup.backup_restore import create_backup, list_backups, restore_backup
from small_business.models import JournalEntry, Transaction
from small_business.storage.transaction_store import load_transactions, save_transaction


def test_create_backup(tmp_path):
	"""Test creating backup."""
	data_dir = tmp_path / "data"
	backup_dir = tmp_path / "backups"

	# Create some data
	txn = Transaction(
		date=date(2025, 11, 15),
		description="Test",
		entries=[
			JournalEntry(account_code="EXP-TEST", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)
	save_transaction(txn, data_dir)

	# Create backup
	backup_path = create_backup(data_dir, backup_dir)

	assert backup_path.exists()
	assert backup_path.suffix == ".zip"


def test_list_backups(tmp_path):
	"""Test listing backups."""
	data_dir = tmp_path / "data"
	backup_dir = tmp_path / "backups"

	# Create data
	txn = Transaction(
		date=date(2025, 11, 15),
		description="Test",
		entries=[
			JournalEntry(account_code="EXP-TEST", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)
	save_transaction(txn, data_dir)

	# Create backups
	create_backup(data_dir, backup_dir)
	create_backup(data_dir, backup_dir)

	# List backups
	backups = list_backups(backup_dir)

	assert len(backups) >= 2


def test_restore_backup(tmp_path):
	"""Test restoring from backup."""
	data_dir = tmp_path / "data"
	backup_dir = tmp_path / "backups"
	restore_dir = tmp_path / "restored"

	# Create and save transaction
	txn = Transaction(
		transaction_id="TXN-TEST-001",
		date=date(2025, 11, 15),
		description="Original transaction",
		entries=[
			JournalEntry(account_code="EXP-TEST", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)
	save_transaction(txn, data_dir)

	# Create backup
	backup_path = create_backup(data_dir, backup_dir)

	# Restore to new directory
	restore_backup(backup_path, restore_dir)

	# Verify restored data
	restored_txns = load_transactions(restore_dir, date(2025, 11, 15))
	assert len(restored_txns) == 1
	assert restored_txns[0].transaction_id == "TXN-TEST-001"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/backup/test_backup_restore.py::test_create_backup -v`

Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `src/small_business/backup/backup_restore.py`:

```python
"""Backup and restore functionality."""

import shutil
import zipfile
from datetime import datetime
from pathlib import Path


def create_backup(data_dir: Path, backup_dir: Path) -> Path:
	"""Create a backup of the data directory.

	Args:
		data_dir: Data directory to backup
		backup_dir: Where to save backups

	Returns:
		Path to created backup file
	"""
	backup_dir.mkdir(parents=True, exist_ok=True)

	# Generate backup filename with timestamp
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	backup_name = f"backup_{timestamp}.zip"
	backup_path = backup_dir / backup_name

	# Create zip archive
	with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
		# Walk through data directory and add all files
		for file_path in data_dir.rglob("*"):
			if file_path.is_file() and ".git" not in file_path.parts:
				# Add file to zip with relative path
				arcname = file_path.relative_to(data_dir)
				zipf.write(file_path, arcname)

	return backup_path


def list_backups(backup_dir: Path) -> list[dict]:
	"""List all available backups.

	Args:
		backup_dir: Directory containing backups

	Returns:
		List of backup info dictionaries
	"""
	if not backup_dir.exists():
		return []

	backups = []
	for backup_file in sorted(backup_dir.glob("backup_*.zip"), reverse=True):
		stat = backup_file.stat()
		backups.append(
			{
				"path": backup_file,
				"name": backup_file.name,
				"size": stat.st_size,
				"created": datetime.fromtimestamp(stat.st_mtime),
			}
		)

	return backups


def restore_backup(backup_path: Path, restore_dir: Path) -> None:
	"""Restore data from a backup.

	Args:
		backup_path: Path to backup zip file
		restore_dir: Directory to restore data to
	"""
	# Create restore directory
	restore_dir.mkdir(parents=True, exist_ok=True)

	# Extract backup
	with zipfile.ZipFile(backup_path, "r") as zipf:
		zipf.extractall(restore_dir)
```

Update `src/small_business/backup/__init__.py` to add exports.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/backup/test_backup_restore.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/backup/backup_restore.py tests/backup/test_backup_restore.py src/small_business/backup/__init__.py
git commit -m "feat: add backup and restore utilities

Implement zip-based backup creation, listing, and restore
functionality for data protection and recovery.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: Performance Optimization

**Files:**
- Create: `src/small_business/performance/__init__.py`
- Create: `src/small_business/performance/caching.py`
- Test: `tests/performance/test_caching.py`

**Step 1: Write the failing test**

Create `tests/performance/test_caching.py`:

```python
"""Test performance optimization utilities."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.models import JournalEntry, Transaction
from small_business.performance.caching import TransactionCache
from small_business.storage.transaction_store import save_transaction


def test_transaction_cache(tmp_path):
	"""Test transaction caching for performance."""
	data_dir = tmp_path / "data"

	# Create transactions
	for i in range(10):
		txn = Transaction(
			date=date(2025, 11, i + 1),
			description=f"Transaction {i}",
			entries=[
				JournalEntry(account_code="EXP-TEST", debit=Decimal("100.00"), credit=Decimal("0")),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
			],
		)
		save_transaction(txn, data_dir)

	# Use cache
	cache = TransactionCache(data_dir)

	# First load (should cache)
	txns1 = cache.get_transactions(date(2025, 11, 15))
	assert len(txns1) == 10

	# Second load (should use cache)
	txns2 = cache.get_transactions(date(2025, 11, 15))
	assert len(txns2) == 10
	assert txns1 == txns2

	# Invalidate cache
	cache.invalidate()

	# Next load should re-read
	txns3 = cache.get_transactions(date(2025, 11, 15))
	assert len(txns3) == 10
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/performance/test_caching.py::test_transaction_cache -v`

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `src/small_business/performance/__init__.py`:

```python
"""Performance optimization utilities."""

from .caching import TransactionCache

__all__ = ["TransactionCache"]
```

Create `src/small_business/performance/caching.py`:

```python
"""Caching utilities for performance optimization."""

from datetime import date
from pathlib import Path

from small_business.models import Transaction
from small_business.storage.transaction_store import load_transactions


class TransactionCache:
	"""Cache for transaction data to improve query performance."""

	def __init__(self, data_dir: Path):
		"""Initialize transaction cache.

		Args:
			data_dir: Data directory
		"""
		self.data_dir = data_dir
		self._cache: dict[str, list[Transaction]] = {}

	def get_transactions(self, as_of_date: date) -> list[Transaction]:
		"""Get transactions with caching.

		Args:
			as_of_date: Date to load transactions for

		Returns:
			List of transactions
		"""
		# Generate cache key from financial year
		from small_business.models.utils import get_financial_year

		cache_key = get_financial_year(as_of_date)

		# Check cache
		if cache_key in self._cache:
			return self._cache[cache_key]

		# Load from storage
		transactions = load_transactions(self.data_dir, as_of_date)

		# Cache result
		self._cache[cache_key] = transactions

		return transactions

	def invalidate(self, financial_year: str | None = None) -> None:
		"""Invalidate cache.

		Args:
			financial_year: Specific year to invalidate, or None for all
		"""
		if financial_year:
			self._cache.pop(financial_year, None)
		else:
			self._cache.clear()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/performance/test_caching.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/performance/ tests/performance/
git commit -m "feat: add performance caching

Implement transaction caching by financial year to improve
query performance for large datasets.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: Integration Test

**Files:**
- Create: `tests/integration/test_polish_integration.py`

**Step 1: Write integration test**

Create `tests/integration/test_polish_integration.py`:

```python
"""Integration test for polish and enhancement features."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.backup.backup_restore import create_backup, restore_backup
from small_business.backup.git_integration import commit_data_changes, init_git_repo
from small_business.models import JournalEntry, Transaction
from small_business.performance.caching import TransactionCache
from small_business.storage.transaction_store import load_transactions, save_transaction
from small_business.validation.integrity import verify_data_integrity
from small_business.validation.validators import ValidationError, validate_invoice_payment
from small_business.models import Invoice, LineItem


def test_complete_polish_workflow(tmp_path):
	"""Test complete workflow with all polish features."""
	data_dir = tmp_path / "data"
	backup_dir = tmp_path / "backups"

	# Initialize Git for versioning
	init_git_repo(data_dir)

	# Create and save transactions
	txn1 = Transaction(
		date=date(2025, 11, 15),
		description="Office supplies",
		entries=[
			JournalEntry(account_code="EXP-SUPPLIES", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)
	save_transaction(txn1, data_dir)

	# Commit to Git
	commit_hash1 = commit_data_changes(data_dir, "Add office supplies transaction")
	assert commit_hash1 is not None

	# Add another transaction
	txn2 = Transaction(
		date=date(2025, 11, 16),
		description="Sales income",
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("500.00"), credit=Decimal("0")),
			JournalEntry(account_code="INC-SALES", debit=Decimal("0"), credit=Decimal("500.00")),
		],
	)
	save_transaction(txn2, data_dir)

	commit_hash2 = commit_data_changes(data_dir, "Add sales transaction")
	assert commit_hash2 is not None

	# Verify data integrity
	integrity_result = verify_data_integrity(data_dir, date(2025, 11, 16))
	assert integrity_result["transactions_balanced"] is True
	assert integrity_result["all_checks_passed"] is True

	# Test validation
	invoice = Invoice(
		invoice_id="INV-001",
		client_id="C-001",
		date_issued=date(2025, 11, 16),
		date_due=date(2025, 12, 16),
		line_items=[LineItem(description="Service", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)

	# Valid payment
	validate_invoice_payment(invoice, Decimal("110.00"))  # Should not raise

	# Invalid payment
	try:
		validate_invoice_payment(invoice, Decimal("200.00"))
		assert False, "Should raise ValidationError"
	except ValidationError:
		pass

	# Create backup
	backup_path = create_backup(data_dir, backup_dir)
	assert backup_path.exists()

	# Test caching
	cache = TransactionCache(data_dir)
	cached_txns = cache.get_transactions(date(2025, 11, 16))
	assert len(cached_txns) == 2

	# Load again (should use cache)
	cached_txns2 = cache.get_transactions(date(2025, 11, 16))
	assert cached_txns == cached_txns2

	# Restore from backup to verify backup works
	restore_dir = tmp_path / "restored"
	restore_backup(backup_path, restore_dir)

	restored_txns = load_transactions(restore_dir, date(2025, 11, 16))
	assert len(restored_txns) == 2
```

**Step 2: Run integration test**

Run: `uv run pytest tests/integration/test_polish_integration.py -v`

Expected: PASS

**Step 3: Commit**

```bash
git add tests/integration/test_polish_integration.py
git commit -m "test: add polish features integration tests

Add end-to-end test covering validation, Git versioning,
backup/restore, and performance caching.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Summary

Phase 6 implementation delivers:

✅ **Enhanced data validation** - Workflow transition validation with clear errors
✅ **Data integrity checks** - Transaction balancing and orphaned reference detection
✅ **Git integration** - Automatic versioning of data changes with commit history
✅ **Backup/restore** - Zip-based backup creation and restore functionality
✅ **Performance caching** - Transaction caching for improved query performance
✅ **Integration tests** - End-to-end validation of all polish features

**Result:** A polished, production-ready small business management system with robust data protection, validation, and performance optimization.

---

## Verification Checklist

Before marking Phase 6 complete, verify:

- [ ] All tests pass: `uv run pytest`
- [ ] Code quality: `uv run ruff check .`
- [ ] Formatting: `uv run ruff format .`
- [ ] Documentation builds: `mkdocs build`
- [ ] Manual test: Create backup and restore
- [ ] Verify Git commits are created for data changes
- [ ] Check integrity checks detect issues correctly
- [ ] Test caching improves performance on large datasets
- [ ] Verify all validation errors provide helpful messages
