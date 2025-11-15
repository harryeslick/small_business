"""Test transaction storage."""

from datetime import date
from decimal import Decimal

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
