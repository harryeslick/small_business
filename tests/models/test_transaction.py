"""Tests for Transaction and JournalEntry models."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from small_business.models.transaction import JournalEntry, Transaction


def test_journal_entry_debit():
	"""Test creating a debit entry."""
	entry = JournalEntry(account_code="BANK", debit=Decimal("100.00"), credit=Decimal("0"))
	assert entry.account_code == "BANK"
	assert entry.debit == Decimal("100.00")
	assert entry.credit == Decimal("0")


def test_journal_entry_credit():
	"""Test creating a credit entry."""
	entry = JournalEntry(account_code="INC", debit=Decimal("0"), credit=Decimal("100.00"))
	assert entry.credit == Decimal("100.00")
	assert entry.debit == Decimal("0")


def test_journal_entry_cannot_have_both_debit_and_credit():
	"""Test that entry cannot have both debit and credit."""
	with pytest.raises(ValidationError) as exc_info:
		JournalEntry(account_code="BANK", debit=Decimal("100.00"), credit=Decimal("50.00"))
	assert "both debit and credit" in str(exc_info.value)


def test_journal_entry_must_have_debit_or_credit():
	"""Test that entry must have either debit or credit."""
	with pytest.raises(ValidationError) as exc_info:
		JournalEntry(account_code="BANK", debit=Decimal("0"), credit=Decimal("0"))
	assert "either debit or credit" in str(exc_info.value)


def test_transaction_simple_double_entry():
	"""Test creating a balanced transaction."""
	transaction = Transaction(
		transaction_id="TXN-20251115-001",
		date=date(2025, 11, 15),
		description="Payment received",
		entries=[
			JournalEntry(account_code="BANK", debit=Decimal("100.00")),
			JournalEntry(account_code="INC", credit=Decimal("100.00")),
		],
	)
	assert len(transaction.entries) == 2
	assert transaction.amount == Decimal("100.00")
	assert transaction.financial_year == "2025-26"


def test_transaction_must_balance():
	"""Test that transaction debits must equal credits."""
	with pytest.raises(ValidationError) as exc_info:
		Transaction(
			transaction_id="TXN-20251115-002",
			date=date(2025, 11, 15),
			description="Unbalanced",
			entries=[
				JournalEntry(account_code="BANK", debit=Decimal("100.00")),
				JournalEntry(account_code="INC", credit=Decimal("50.00")),
			],
		)
	assert "not balanced" in str(exc_info.value)


def test_transaction_complex_split():
	"""Test transaction with multiple entries (split transaction)."""
	transaction = Transaction(
		transaction_id="TXN-20251115-003",
		date=date(2025, 11, 15),
		description="Expense split",
		entries=[
			JournalEntry(account_code="EXP-TRV", debit=Decimal("60.00")),
			JournalEntry(account_code="EXP-MAT", debit=Decimal("40.00")),
			JournalEntry(account_code="BANK", credit=Decimal("100.00")),
		],
	)
	assert len(transaction.entries) == 3
	assert transaction.amount == Decimal("100.00")


def test_transaction_auto_generates_id():
	"""Test transaction ID auto-generation."""
	transaction = Transaction(
		date=date(2025, 11, 15),
		description="Test",
		entries=[
			JournalEntry(account_code="BANK", debit=Decimal("100.00")),
			JournalEntry(account_code="INC", credit=Decimal("100.00")),
		],
	)
	assert transaction.transaction_id.startswith("TXN-")


def test_transaction_must_have_minimum_two_entries():
	"""Test that transaction requires at least 2 entries."""
	with pytest.raises(ValidationError) as exc_info:
		Transaction(
			date=date(2025, 11, 15),
			description="Invalid",
			entries=[JournalEntry(account_code="BANK", debit=Decimal("100.00"))],
		)
	assert "entries" in str(exc_info.value)


def test_transaction_with_receipt():
	"""Test transaction with receipt path."""
	transaction = Transaction(
		date=date(2025, 11, 15),
		description="Purchase with receipt",
		receipt_path="receipts/2025-26/2025-11-15_EXP-MAT_Supplies_100.00.pdf",
		entries=[
			JournalEntry(account_code="EXP-MAT", debit=Decimal("100.00")),
			JournalEntry(account_code="BANK", credit=Decimal("100.00")),
		],
	)
	assert transaction.receipt_path.endswith(".pdf")
