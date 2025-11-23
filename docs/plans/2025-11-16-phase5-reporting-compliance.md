# Phase 5: Reporting & Compliance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build financial reporting system with Profit & Loss, Balance Sheet, Cash Flow, and BAS/GST compliance reports.

**Architecture:** Implement report calculators that query transactions and generate financial statements, create BAS/GST report generator for Australian tax compliance, build ledger queries for account balances, and implement export functionality for CSV/PDF formats.

**Tech Stack:** Python 3.13+, Pydantic (models), Pandas (data analysis), ReportLab (PDF generation)

---

## Task 1: Ledger Query Engine

**Files:**
- Create: `src/small_business/reports/__init__.py`
- Create: `src/small_business/reports/ledger.py`
- Test: `tests/reports/test_ledger.py`

**Step 1: Write the failing test**

Create `tests/reports/test_ledger.py`:

```python
"""Test ledger query engine."""

from datetime import date
from decimal import Decimal

from small_business.models import Account, AccountType, JournalEntry, Transaction
from small_business.reports.ledger import calculate_account_balance, get_account_transactions
from small_business.storage.transaction_store import save_transaction


def test_calculate_account_balance(tmp_path):
	"""Test calculating account balance from transactions."""
	data_dir = tmp_path / "data"

	# Save transactions affecting an expense account
	txn1 = Transaction(
		date=date(2025, 11, 15),
		description="Office supplies",
		entries=[
			JournalEntry(account_code="EXP-SUPPLIES", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)

	txn2 = Transaction(
		date=date(2025, 11, 16),
		description="More supplies",
		entries=[
			JournalEntry(account_code="EXP-SUPPLIES", debit=Decimal("50.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("50.00")),
		],
	)

	save_transaction(txn1, data_dir)
	save_transaction(txn2, data_dir)

	# Calculate balance
	balance = calculate_account_balance("EXP-SUPPLIES", data_dir, date(2025, 11, 16))

	# Expense accounts increase with debits
	assert balance == Decimal("150.00")


def test_calculate_bank_account_balance(tmp_path):
	"""Test calculating bank account balance."""
	data_dir = tmp_path / "data"

	# Starting balance transaction
	txn1 = Transaction(
		date=date(2025, 11, 1),
		description="Opening balance",
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("1000.00"), credit=Decimal("0")),
			JournalEntry(account_code="EQUITY", debit=Decimal("0"), credit=Decimal("1000.00")),
		],
	)

	# Expense (reduces bank balance)
	txn2 = Transaction(
		date=date(2025, 11, 15),
		description="Expense",
		entries=[
			JournalEntry(account_code="EXP-SUPPLIES", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)

	# Income (increases bank balance)
	txn3 = Transaction(
		date=date(2025, 11, 16),
		description="Income",
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("500.00"), credit=Decimal("0")),
			JournalEntry(account_code="INC-SALES", debit=Decimal("0"), credit=Decimal("500.00")),
		],
	)

	save_transaction(txn1, data_dir)
	save_transaction(txn2, data_dir)
	save_transaction(txn3, data_dir)

	balance = calculate_account_balance("BANK-CHQ", data_dir, date(2025, 11, 16))

	# Bank: 1000 (opening) - 100 (expense) + 500 (income) = 1400
	assert balance == Decimal("1400.00")


def test_get_account_transactions(tmp_path):
	"""Test getting all transactions for an account."""
	data_dir = tmp_path / "data"

	txn1 = Transaction(
		date=date(2025, 11, 15),
		description="Transaction 1",
		entries=[
			JournalEntry(account_code="EXP-TEST", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)

	txn2 = Transaction(
		date=date(2025, 11, 16),
		description="Transaction 2",
		entries=[
			JournalEntry(account_code="EXP-OTHER", debit=Decimal("50.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("50.00")),
		],
	)

	save_transaction(txn1, data_dir)
	save_transaction(txn2, data_dir)

	# Get transactions for EXP-TEST
	transactions = get_account_transactions("EXP-TEST", data_dir, date(2025, 11, 16))

	assert len(transactions) == 1
	assert transactions[0].description == "Transaction 1"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/reports/test_ledger.py::test_calculate_account_balance -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'small_business.reports'"

**Step 3: Write minimal implementation**

Create `src/small_business/reports/__init__.py`:

```python
"""Financial reporting and analytics."""

from .ledger import calculate_account_balance, get_account_transactions

__all__ = ["calculate_account_balance", "get_account_transactions"]
```

Create `src/small_business/reports/ledger.py`:

```python
"""Ledger queries for account balances and transactions."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.models import Transaction
from small_business.storage.transaction_store import load_transactions


def calculate_account_balance(
	account_code: str,
	data_dir: Path,
	as_of_date: date,
) -> Decimal:
	"""Calculate account balance as of a specific date.

	Args:
		account_code: Account code to calculate balance for
		data_dir: Data directory
		as_of_date: Calculate balance up to this date

	Returns:
		Account balance (debits - credits for asset/expense accounts,
		                  credits - debits for liability/income/equity accounts)
	"""
	transactions = load_transactions(data_dir, as_of_date)

	total_debits = Decimal("0")
	total_credits = Decimal("0")

	for txn in transactions:
		# Only include transactions up to as_of_date
		if txn.date <= as_of_date:
			for entry in txn.entries:
				if entry.account_code == account_code:
					total_debits += entry.debit
					total_credits += entry.credit

	# For most accounts, balance = debits - credits
	# (This is correct for assets and expenses)
	# For liabilities, income, and equity: balance = credits - debits
	# However, we return the raw debit balance here and let reports
	# interpret based on account type
	return total_debits - total_credits


def get_account_transactions(
	account_code: str,
	data_dir: Path,
	as_of_date: date,
) -> list[Transaction]:
	"""Get all transactions affecting an account.

	Args:
		account_code: Account code to query
		data_dir: Data directory
		as_of_date: Get transactions up to this date

	Returns:
		List of transactions affecting the account
	"""
	all_transactions = load_transactions(data_dir, as_of_date)

	# Filter transactions that have entries for this account
	account_transactions = []
	for txn in all_transactions:
		if txn.date <= as_of_date:
			for entry in txn.entries:
				if entry.account_code == account_code:
					account_transactions.append(txn)
					break  # Only add transaction once

	return account_transactions
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/reports/test_ledger.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/reports/ tests/reports/
git commit -m "feat: add ledger query engine

Implement account balance calculations and transaction queries
for generating financial reports from double-entry transactions.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Profit & Loss Report

**Files:**
- Create: `src/small_business/reports/profit_loss.py`
- Test: `tests/reports/test_profit_loss.py`

**Step 1: Write the failing test**

Create `tests/reports/test_profit_loss.py`:

```python
"""Test Profit & Loss report."""

from datetime import date
from decimal import Decimal

from small_business.models import Account, AccountType, ChartOfAccounts, JournalEntry, Transaction
from small_business.reports.profit_loss import generate_profit_loss_report
from small_business.storage.transaction_store import save_transaction


def test_generate_profit_loss_report(tmp_path):
	"""Test generating P&L report."""
	data_dir = tmp_path / "data"

	# Create chart of accounts
	chart = ChartOfAccounts(
		accounts=[
			Account(code="INC-SALES", name="Sales", account_type=AccountType.INCOME),
			Account(code="INC-OTHER", name="Other Income", account_type=AccountType.INCOME),
			Account(code="EXP-SUPPLIES", name="Supplies", account_type=AccountType.EXPENSE),
			Account(code="EXP-RENT", name="Rent", account_type=AccountType.EXPENSE),
			Account(code="BANK-CHQ", name="Bank", account_type=AccountType.ASSET),
		]
	)

	# Save transactions
	# Income: $1000
	txn1 = Transaction(
		date=date(2025, 11, 15),
		description="Sales",
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("1000.00"), credit=Decimal("0")),
			JournalEntry(account_code="INC-SALES", debit=Decimal("0"), credit=Decimal("1000.00")),
		],
	)

	# Expense: $300
	txn2 = Transaction(
		date=date(2025, 11, 16),
		description="Supplies",
		entries=[
			JournalEntry(account_code="EXP-SUPPLIES", debit=Decimal("300.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("300.00")),
		],
	)

	# Expense: $500
	txn3 = Transaction(
		date=date(2025, 11, 17),
		description="Rent",
		entries=[
			JournalEntry(account_code="EXP-RENT", debit=Decimal("500.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("500.00")),
		],
	)

	save_transaction(txn1, data_dir)
	save_transaction(txn2, data_dir)
	save_transaction(txn3, data_dir)

	# Generate P&L report
	report = generate_profit_loss_report(
		chart=chart,
		data_dir=data_dir,
		start_date=date(2025, 11, 1),
		end_date=date(2025, 11, 30),
	)

	# Check totals
	assert report["total_income"] == Decimal("1000.00")
	assert report["total_expenses"] == Decimal("800.00")
	assert report["net_profit"] == Decimal("200.00")

	# Check breakdown
	assert len(report["income"]) == 1
	assert report["income"]["INC-SALES"]["balance"] == Decimal("1000.00")

	assert len(report["expenses"]) == 2
	assert report["expenses"]["EXP-SUPPLIES"]["balance"] == Decimal("300.00")
	assert report["expenses"]["EXP-RENT"]["balance"] == Decimal("500.00")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/reports/test_profit_loss.py::test_generate_profit_loss_report -v`

Expected: FAIL with "ImportError: cannot import name 'generate_profit_loss_report'"

**Step 3: Write minimal implementation**

Create `src/small_business/reports/profit_loss.py`:

```python
"""Profit & Loss (P&L) report generation."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.models import AccountType, ChartOfAccounts
from small_business.reports.ledger import calculate_account_balance
from small_business.storage.transaction_store import load_transactions


def generate_profit_loss_report(
	chart: ChartOfAccounts,
	data_dir: Path,
	start_date: date,
	end_date: date,
) -> dict:
	"""Generate Profit & Loss report.

	Args:
		chart: Chart of accounts
		data_dir: Data directory
		start_date: Report start date
		end_date: Report end date

	Returns:
		Dictionary with income, expenses, and net profit
	"""
	# Load transactions in date range
	transactions = load_transactions(data_dir, end_date)
	transactions = [t for t in transactions if start_date <= t.date <= end_date]

	# Calculate income by account
	income_accounts = {}
	total_income = Decimal("0")

	for account in chart.accounts:
		if account.account_type == AccountType.INCOME:
			# For income accounts, credits increase balance
			balance = Decimal("0")
			for txn in transactions:
				for entry in txn.entries:
					if entry.account_code == account.code:
						balance += entry.credit - entry.debit

			if balance > 0:
				income_accounts[account.code] = {
					"name": account.name,
					"balance": balance,
				}
				total_income += balance

	# Calculate expenses by account
	expense_accounts = {}
	total_expenses = Decimal("0")

	for account in chart.accounts:
		if account.account_type == AccountType.EXPENSE:
			# For expense accounts, debits increase balance
			balance = Decimal("0")
			for txn in transactions:
				for entry in txn.entries:
					if entry.account_code == account.code:
						balance += entry.debit - entry.credit

			if balance > 0:
				expense_accounts[account.code] = {
					"name": account.name,
					"balance": balance,
				}
				total_expenses += balance

	# Calculate net profit
	net_profit = total_income - total_expenses

	return {
		"start_date": start_date,
		"end_date": end_date,
		"income": income_accounts,
		"total_income": total_income,
		"expenses": expense_accounts,
		"total_expenses": total_expenses,
		"net_profit": net_profit,
	}
```

Update `src/small_business/reports/__init__.py` to add export.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/reports/test_profit_loss.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/reports/profit_loss.py tests/reports/test_profit_loss.py src/small_business/reports/__init__.py
git commit -m "feat: add Profit & Loss report generator

Implement P&L report with income/expense breakdown and net
profit calculation for specified date ranges.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Balance Sheet Report

**Files:**
- Create: `src/small_business/reports/balance_sheet.py`
- Test: `tests/reports/test_balance_sheet.py`

**Step 1: Write the failing test**

Create `tests/reports/test_balance_sheet.py`:

```python
"""Test Balance Sheet report."""

from datetime import date
from decimal import Decimal

from small_business.models import Account, AccountType, ChartOfAccounts, JournalEntry, Transaction
from small_business.reports.balance_sheet import generate_balance_sheet
from small_business.storage.transaction_store import save_transaction


def test_generate_balance_sheet(tmp_path):
	"""Test generating balance sheet."""
	data_dir = tmp_path / "data"

	chart = ChartOfAccounts(
		accounts=[
			Account(code="BANK-CHQ", name="Bank Cheque", account_type=AccountType.ASSET),
			Account(code="ASSET-EQUIP", name="Equipment", account_type=AccountType.ASSET),
			Account(code="LIAB-LOAN", name="Business Loan", account_type=AccountType.LIABILITY),
			Account(code="EQUITY", name="Owner's Equity", account_type=AccountType.EQUITY),
		]
	)

	# Opening equity
	txn1 = Transaction(
		date=date(2025, 11, 1),
		description="Opening balance",
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("10000.00"), credit=Decimal("0")),
			JournalEntry(account_code="EQUITY", debit=Decimal("0"), credit=Decimal("10000.00")),
		],
	)

	# Purchase equipment
	txn2 = Transaction(
		date=date(2025, 11, 15),
		description="Equipment purchase",
		entries=[
			JournalEntry(account_code="ASSET-EQUIP", debit=Decimal("5000.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("5000.00")),
		],
	)

	# Business loan
	txn3 = Transaction(
		date=date(2025, 11, 20),
		description="Business loan",
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("3000.00"), credit=Decimal("0")),
			JournalEntry(account_code="LIAB-LOAN", debit=Decimal("0"), credit=Decimal("3000.00")),
		],
	)

	save_transaction(txn1, data_dir)
	save_transaction(txn2, data_dir)
	save_transaction(txn3, data_dir)

	# Generate balance sheet
	report = generate_balance_sheet(
		chart=chart,
		data_dir=data_dir,
		as_of_date=date(2025, 11, 30),
	)

	# Check assets: Bank (10000 - 5000 + 3000) + Equipment (5000) = 13000
	assert report["total_assets"] == Decimal("13000.00")
	assert report["assets"]["BANK-CHQ"]["balance"] == Decimal("8000.00")
	assert report["assets"]["ASSET-EQUIP"]["balance"] == Decimal("5000.00")

	# Check liabilities: Loan = 3000
	assert report["total_liabilities"] == Decimal("3000.00")

	# Check equity: 10000
	assert report["total_equity"] == Decimal("10000.00")

	# Accounting equation: Assets = Liabilities + Equity
	assert report["total_assets"] == report["total_liabilities"] + report["total_equity"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/reports/test_balance_sheet.py::test_generate_balance_sheet -v`

Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `src/small_business/reports/balance_sheet.py`:

```python
"""Balance Sheet report generation."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.models import AccountType, ChartOfAccounts
from small_business.storage.transaction_store import load_transactions


def generate_balance_sheet(
	chart: ChartOfAccounts,
	data_dir: Path,
	as_of_date: date,
) -> dict:
	"""Generate Balance Sheet report.

	Args:
		chart: Chart of accounts
		data_dir: Data directory
		as_of_date: Report as of this date

	Returns:
		Dictionary with assets, liabilities, and equity
	"""
	transactions = load_transactions(data_dir, as_of_date)
	transactions = [t for t in transactions if t.date <= as_of_date]

	# Calculate assets
	asset_accounts = {}
	total_assets = Decimal("0")

	for account in chart.accounts:
		if account.account_type == AccountType.ASSET:
			# For assets, debits increase balance
			balance = Decimal("0")
			for txn in transactions:
				for entry in txn.entries:
					if entry.account_code == account.code:
						balance += entry.debit - entry.credit

			if balance != 0:
				asset_accounts[account.code] = {
					"name": account.name,
					"balance": balance,
				}
				total_assets += balance

	# Calculate liabilities
	liability_accounts = {}
	total_liabilities = Decimal("0")

	for account in chart.accounts:
		if account.account_type == AccountType.LIABILITY:
			# For liabilities, credits increase balance
			balance = Decimal("0")
			for txn in transactions:
				for entry in txn.entries:
					if entry.account_code == account.code:
						balance += entry.credit - entry.debit

			if balance != 0:
				liability_accounts[account.code] = {
					"name": account.name,
					"balance": balance,
				}
				total_liabilities += balance

	# Calculate equity
	equity_accounts = {}
	total_equity = Decimal("0")

	for account in chart.accounts:
		if account.account_type == AccountType.EQUITY:
			# For equity, credits increase balance
			balance = Decimal("0")
			for txn in transactions:
				for entry in txn.entries:
					if entry.account_code == account.code:
						balance += entry.credit - entry.debit

			if balance != 0:
				equity_accounts[account.code] = {
					"name": account.name,
					"balance": balance,
				}
				total_equity += balance

	return {
		"as_of_date": as_of_date,
		"assets": asset_accounts,
		"total_assets": total_assets,
		"liabilities": liability_accounts,
		"total_liabilities": total_liabilities,
		"equity": equity_accounts,
		"total_equity": total_equity,
	}
```

Update `src/small_business/reports/__init__.py` to add export.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/reports/test_balance_sheet.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/reports/balance_sheet.py tests/reports/test_balance_sheet.py src/small_business/reports/__init__.py
git commit -m "feat: add Balance Sheet report generator

Implement balance sheet with assets, liabilities, and equity
breakdown. Verifies accounting equation balances.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: BAS/GST Report

**Files:**
- Create: `src/small_business/reports/bas_gst.py`
- Test: `tests/reports/test_bas_gst.py`

**Step 1: Write the failing test**

Create `tests/reports/test_bas_gst.py`:

```python
"""Test BAS/GST report."""

from datetime import date
from decimal import Decimal

from small_business.models import JournalEntry, Transaction
from small_business.reports.bas_gst import generate_bas_report
from small_business.storage.transaction_store import save_transaction


def test_generate_bas_report(tmp_path):
	"""Test generating BAS/GST report."""
	data_dir = tmp_path / "data"

	# GST collected (on sales) - GST inclusive $110 includes $10 GST
	txn1 = Transaction(
		date=date(2025, 11, 15),
		description="Sales",
		gst_inclusive=True,
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("110.00"), credit=Decimal("0")),
			JournalEntry(account_code="INC-SALES", debit=Decimal("0"), credit=Decimal("110.00")),
		],
	)

	# GST paid (on expenses) - GST inclusive $55 includes $5 GST
	txn2 = Transaction(
		date=date(2025, 11, 16),
		description="Supplies",
		gst_inclusive=True,
		entries=[
			JournalEntry(account_code="EXP-SUPPLIES", debit=Decimal("55.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("55.00")),
		],
	)

	# Another sale
	txn3 = Transaction(
		date=date(2025, 11, 20),
		description="More sales",
		gst_inclusive=True,
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("220.00"), credit=Decimal("0")),
			JournalEntry(account_code="INC-SALES", debit=Decimal("0"), credit=Decimal("220.00")),
		],
	)

	save_transaction(txn1, data_dir)
	save_transaction(txn2, data_dir)
	save_transaction(txn3, data_dir)

	# Generate BAS report
	report = generate_bas_report(
		data_dir=data_dir,
		start_date=date(2025, 11, 1),
		end_date=date(2025, 11, 30),
	)

	# Total sales: $110 + $220 = $330
	assert report["total_sales"] == Decimal("330.00")

	# GST on sales: 330 × 1/11 = $30
	assert report["gst_on_sales"] == Decimal("30.00")

	# Total purchases: $55
	assert report["total_purchases"] == Decimal("55.00")

	# GST on purchases: 55 × 1/11 = $5
	assert report["gst_on_purchases"] == Decimal("5.00")

	# Net GST: $30 - $5 = $25 (owed to ATO)
	assert report["net_gst"] == Decimal("25.00")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/reports/test_bas_gst.py::test_generate_bas_report -v`

Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `src/small_business/reports/bas_gst.py`:

```python
"""BAS/GST report generation for Australian tax compliance."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.storage.transaction_store import load_transactions


def calculate_gst_component(amount: Decimal, gst_inclusive: bool) -> Decimal:
	"""Calculate GST component of an amount.

	Args:
		amount: Total amount
		gst_inclusive: Whether amount includes GST

	Returns:
		GST component (1/11 if inclusive, 10% if exclusive)
	"""
	if gst_inclusive:
		# GST = amount × 1/11
		return (amount / Decimal("11")).quantize(Decimal("0.01"))
	else:
		# GST = amount × 10%
		return (amount * Decimal("0.10")).quantize(Decimal("0.01"))


def generate_bas_report(
	data_dir: Path,
	start_date: date,
	end_date: date,
) -> dict:
	"""Generate BAS/GST report.

	Args:
		data_dir: Data directory
		start_date: Report start date
		end_date: Report end date

	Returns:
		Dictionary with GST collected, paid, and net amount
	"""
	transactions = load_transactions(data_dir, end_date)
	transactions = [t for t in transactions if start_date <= t.date <= end_date]

	total_sales = Decimal("0")
	total_purchases = Decimal("0")
	gst_on_sales = Decimal("0")
	gst_on_purchases = Decimal("0")

	for txn in transactions:
		# Determine if transaction is income or expense
		# Income: has credit to income account
		# Expense: has debit to expense account

		is_income = any(
			entry.account_code.startswith("INC") and entry.credit > 0 for entry in txn.entries
		)
		is_expense = any(
			entry.account_code.startswith("EXP") and entry.debit > 0 for entry in txn.entries
		)

		if is_income:
			# Calculate sales amount and GST
			for entry in txn.entries:
				if entry.account_code.startswith("INC"):
					amount = entry.credit
					total_sales += amount
					if txn.gst_inclusive:
						gst_on_sales += calculate_gst_component(amount, True)

		elif is_expense:
			# Calculate purchase amount and GST
			for entry in txn.entries:
				if entry.account_code.startswith("EXP"):
					amount = entry.debit
					total_purchases += amount
					if txn.gst_inclusive:
						gst_on_purchases += calculate_gst_component(amount, True)

	# Net GST = GST collected - GST paid
	net_gst = gst_on_sales - gst_on_purchases

	return {
		"start_date": start_date,
		"end_date": end_date,
		"total_sales": total_sales,
		"gst_on_sales": gst_on_sales,
		"total_purchases": total_purchases,
		"gst_on_purchases": gst_on_purchases,
		"net_gst": net_gst,
	}
```

Update `src/small_business/reports/__init__.py` to add export.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/reports/test_bas_gst.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/reports/bas_gst.py tests/reports/test_bas_gst.py src/small_business/reports/__init__.py
git commit -m "feat: add BAS/GST report generator

Implement Australian BAS report with GST collected, GST paid,
and net GST calculation for quarterly/monthly reporting.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: Report Export to CSV

**Files:**
- Create: `src/small_business/reports/export.py`
- Test: `tests/reports/test_export.py`

**Step 1: Write the failing test**

Create `tests/reports/test_export.py`:

```python
"""Test report export functionality."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd

from small_business.reports.export import export_profit_loss_csv, export_balance_sheet_csv, export_bas_csv


def test_export_profit_loss_csv(tmp_path):
	"""Test exporting P&L to CSV."""
	report = {
		"start_date": date(2025, 11, 1),
		"end_date": date(2025, 11, 30),
		"income": {
			"INC-SALES": {"name": "Sales", "balance": Decimal("1000.00")},
		},
		"total_income": Decimal("1000.00"),
		"expenses": {
			"EXP-RENT": {"name": "Rent", "balance": Decimal("500.00")},
			"EXP-SUPPLIES": {"name": "Supplies", "balance": Decimal("300.00")},
		},
		"total_expenses": Decimal("800.00"),
		"net_profit": Decimal("200.00"),
	}

	output_file = tmp_path / "pl_report.csv"
	export_profit_loss_csv(report, output_file)

	assert output_file.exists()

	# Read and verify CSV
	df = pd.read_csv(output_file)
	assert len(df) > 0
	assert "Account" in df.columns
	assert "Amount" in df.columns


def test_export_balance_sheet_csv(tmp_path):
	"""Test exporting balance sheet to CSV."""
	report = {
		"as_of_date": date(2025, 11, 30),
		"assets": {
			"BANK-CHQ": {"name": "Bank", "balance": Decimal("8000.00")},
		},
		"total_assets": Decimal("8000.00"),
		"liabilities": {
			"LIAB-LOAN": {"name": "Loan", "balance": Decimal("3000.00")},
		},
		"total_liabilities": Decimal("3000.00"),
		"equity": {
			"EQUITY": {"name": "Equity", "balance": Decimal("5000.00")},
		},
		"total_equity": Decimal("5000.00"),
	}

	output_file = tmp_path / "bs_report.csv"
	export_balance_sheet_csv(report, output_file)

	assert output_file.exists()


def test_export_bas_csv(tmp_path):
	"""Test exporting BAS report to CSV."""
	report = {
		"start_date": date(2025, 11, 1),
		"end_date": date(2025, 11, 30),
		"total_sales": Decimal("330.00"),
		"gst_on_sales": Decimal("30.00"),
		"total_purchases": Decimal("55.00"),
		"gst_on_purchases": Decimal("5.00"),
		"net_gst": Decimal("25.00"),
	}

	output_file = tmp_path / "bas_report.csv"
	export_bas_csv(report, output_file)

	assert output_file.exists()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/reports/test_export.py::test_export_profit_loss_csv -v`

Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `src/small_business/reports/export.py`:

```python
"""Report export functionality to CSV and PDF."""

from pathlib import Path

import pandas as pd


def export_profit_loss_csv(report: dict, output_file: Path) -> None:
	"""Export Profit & Loss report to CSV.

	Args:
		report: P&L report dictionary
		output_file: Path to save CSV file
	"""
	rows = []

	# Income section
	rows.append({"Category": "INCOME", "Account": "", "Amount": ""})
	for code, data in report["income"].items():
		rows.append({"Category": "Income", "Account": data["name"], "Amount": float(data["balance"])})

	rows.append({"Category": "", "Account": "Total Income", "Amount": float(report["total_income"])})
	rows.append({"Category": "", "Account": "", "Amount": ""})

	# Expenses section
	rows.append({"Category": "EXPENSES", "Account": "", "Amount": ""})
	for code, data in report["expenses"].items():
		rows.append(
			{"Category": "Expense", "Account": data["name"], "Amount": float(data["balance"])}
		)

	rows.append(
		{"Category": "", "Account": "Total Expenses", "Amount": float(report["total_expenses"])}
	)
	rows.append({"Category": "", "Account": "", "Amount": ""})

	# Net profit
	rows.append({"Category": "", "Account": "NET PROFIT", "Amount": float(report["net_profit"])})

	df = pd.DataFrame(rows)
	df.to_csv(output_file, index=False)


def export_balance_sheet_csv(report: dict, output_file: Path) -> None:
	"""Export Balance Sheet to CSV.

	Args:
		report: Balance sheet report dictionary
		output_file: Path to save CSV file
	"""
	rows = []

	# Assets
	rows.append({"Category": "ASSETS", "Account": "", "Amount": ""})
	for code, data in report["assets"].items():
		rows.append({"Category": "Asset", "Account": data["name"], "Amount": float(data["balance"])})

	rows.append({"Category": "", "Account": "Total Assets", "Amount": float(report["total_assets"])})
	rows.append({"Category": "", "Account": "", "Amount": ""})

	# Liabilities
	rows.append({"Category": "LIABILITIES", "Account": "", "Amount": ""})
	for code, data in report["liabilities"].items():
		rows.append(
			{"Category": "Liability", "Account": data["name"], "Amount": float(data["balance"])}
		)

	rows.append(
		{"Category": "", "Account": "Total Liabilities", "Amount": float(report["total_liabilities"])}
	)
	rows.append({"Category": "", "Account": "", "Amount": ""})

	# Equity
	rows.append({"Category": "EQUITY", "Account": "", "Amount": ""})
	for code, data in report["equity"].items():
		rows.append({"Category": "Equity", "Account": data["name"], "Amount": float(data["balance"])})

	rows.append({"Category": "", "Account": "Total Equity", "Amount": float(report["total_equity"])})

	df = pd.DataFrame(rows)
	df.to_csv(output_file, index=False)


def export_bas_csv(report: dict, output_file: Path) -> None:
	"""Export BAS/GST report to CSV.

	Args:
		report: BAS report dictionary
		output_file: Path to save CSV file
	"""
	rows = [
		{"Item": "Total Sales (GST Inclusive)", "Amount": float(report["total_sales"])},
		{"Item": "GST on Sales", "Amount": float(report["gst_on_sales"])},
		{"Item": "", "Amount": ""},
		{"Item": "Total Purchases (GST Inclusive)", "Amount": float(report["total_purchases"])},
		{"Item": "GST on Purchases", "Amount": float(report["gst_on_purchases"])},
		{"Item": "", "Amount": ""},
		{"Item": "NET GST (Owed to/from ATO)", "Amount": float(report["net_gst"])},
	]

	df = pd.DataFrame(rows)
	df.to_csv(output_file, index=False)
```

Update `src/small_business/reports/__init__.py` to add exports.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/reports/test_export.py -v`

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/small_business/reports/export.py tests/reports/test_export.py src/small_business/reports/__init__.py
git commit -m "feat: add report CSV export functionality

Implement CSV export for P&L, Balance Sheet, and BAS reports
using Pandas for easy data analysis and archiving.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: Integration Test

**Files:**
- Create: `tests/integration/test_reporting_integration.py`

**Step 1: Write integration test**

Create `tests/integration/test_reporting_integration.py`:

```python
"""End-to-end integration test for reporting."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.models import Account, AccountType, ChartOfAccounts, JournalEntry, Transaction
from small_business.reports.balance_sheet import generate_balance_sheet
from small_business.reports.bas_gst import generate_bas_report
from small_business.reports.export import export_balance_sheet_csv, export_bas_csv, export_profit_loss_csv
from small_business.reports.profit_loss import generate_profit_loss_report
from small_business.storage.transaction_store import save_transaction


def test_complete_reporting_workflow(tmp_path):
	"""Test complete reporting workflow with all report types."""
	data_dir = tmp_path / "data"
	reports_dir = tmp_path / "reports"
	reports_dir.mkdir()

	# Create chart of accounts
	chart = ChartOfAccounts(
		accounts=[
			Account(code="BANK-CHQ", name="Bank Cheque Account", account_type=AccountType.ASSET),
			Account(code="INC-SALES", name="Sales Revenue", account_type=AccountType.INCOME),
			Account(code="EXP-RENT", name="Rent", account_type=AccountType.EXPENSE),
			Account(code="EXP-SUPPLIES", name="Supplies", account_type=AccountType.EXPENSE),
			Account(code="EQUITY", name="Owner's Equity", account_type=AccountType.EQUITY),
		]
	)

	# Save transactions for November 2025
	transactions = [
		# Opening balance
		Transaction(
			date=date(2025, 11, 1),
			description="Opening balance",
			entries=[
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("10000.00"), credit=Decimal("0")),
				JournalEntry(account_code="EQUITY", debit=Decimal("0"), credit=Decimal("10000.00")),
			],
		),
		# Sales with GST
		Transaction(
			date=date(2025, 11, 15),
			description="Sales invoice",
			gst_inclusive=True,
			entries=[
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("1100.00"), credit=Decimal("0")),
				JournalEntry(account_code="INC-SALES", debit=Decimal("0"), credit=Decimal("1100.00")),
			],
		),
		# Rent expense with GST
		Transaction(
			date=date(2025, 11, 16),
			description="Monthly rent",
			gst_inclusive=True,
			entries=[
				JournalEntry(account_code="EXP-RENT", debit=Decimal("550.00"), credit=Decimal("0")),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("550.00")),
			],
		),
		# Supplies expense with GST
		Transaction(
			date=date(2025, 11, 20),
			description="Office supplies",
			gst_inclusive=True,
			entries=[
				JournalEntry(account_code="EXP-SUPPLIES", debit=Decimal("220.00"), credit=Decimal("0")),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("220.00")),
			],
		),
	]

	for txn in transactions:
		save_transaction(txn, data_dir)

	# Generate P&L report
	pl_report = generate_profit_loss_report(
		chart=chart,
		data_dir=data_dir,
		start_date=date(2025, 11, 1),
		end_date=date(2025, 11, 30),
	)

	# Verify P&L
	assert pl_report["total_income"] == Decimal("1100.00")
	assert pl_report["total_expenses"] == Decimal("770.00")  # 550 + 220
	assert pl_report["net_profit"] == Decimal("330.00")

	# Export P&L to CSV
	pl_csv = reports_dir / "profit_loss.csv"
	export_profit_loss_csv(pl_report, pl_csv)
	assert pl_csv.exists()

	# Generate Balance Sheet
	bs_report = generate_balance_sheet(
		chart=chart,
		data_dir=data_dir,
		as_of_date=date(2025, 11, 30),
	)

	# Verify Balance Sheet
	# Bank: 10000 + 1100 - 550 - 220 = 10330
	assert bs_report["total_assets"] == Decimal("10330.00")
	assert bs_report["total_equity"] == Decimal("10000.00")

	# Export Balance Sheet to CSV
	bs_csv = reports_dir / "balance_sheet.csv"
	export_balance_sheet_csv(bs_report, bs_csv)
	assert bs_csv.exists()

	# Generate BAS report
	bas_report = generate_bas_report(
		data_dir=data_dir,
		start_date=date(2025, 11, 1),
		end_date=date(2025, 11, 30),
	)

	# Verify BAS
	# Sales: 1100, GST = 1100 × 1/11 = 100
	assert bas_report["gst_on_sales"] == Decimal("100.00")

	# Purchases: 550 + 220 = 770, GST = 770 × 1/11 = 70
	assert bas_report["gst_on_purchases"] == Decimal("70.00")

	# Net GST: 100 - 70 = 30 (owed to ATO)
	assert bas_report["net_gst"] == Decimal("30.00")

	# Export BAS to CSV
	bas_csv = reports_dir / "bas_report.csv"
	export_bas_csv(bas_report, bas_csv)
	assert bas_csv.exists()

	# Verify all reports generated
	assert len(list(reports_dir.glob("*.csv"))) == 3
```

**Step 2: Run integration test**

Run: `uv run pytest tests/integration/test_reporting_integration.py -v`

Expected: PASS

**Step 3: Commit**

```bash
git add tests/integration/test_reporting_integration.py
git commit -m "test: add reporting integration tests

Add end-to-end test covering P&L, Balance Sheet, and BAS
report generation with CSV export verification.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Summary

Phase 5 implementation delivers:

✅ **Ledger query engine** - Account balance and transaction queries
✅ **Profit & Loss report** - Income/expense breakdown with net profit
✅ **Balance Sheet** - Assets, liabilities, equity with accounting equation verification
✅ **BAS/GST report** - Australian tax compliance with GST calculations
✅ **CSV export** - Export all reports to CSV for analysis
✅ **Integration tests** - End-to-end reporting workflow validation

**Next Phase:** Phase 6 will implement polish and enhancements including data validation improvements, backup/restore, and performance optimization.

---

## Verification Checklist

Before marking Phase 5 complete, verify:

- [ ] All tests pass: `uv run pytest`
- [ ] Code quality: `uv run ruff check .`
- [ ] Formatting: `uv run ruff format .`
- [ ] Documentation builds: `mkdocs build`
- [ ] Manual test: Generate all report types
- [ ] Verify GST calculations are correct (1/11 formula)
- [ ] Check CSV exports open correctly in spreadsheet software
- [ ] Verify accounting equation balances (Assets = Liabilities + Equity)
