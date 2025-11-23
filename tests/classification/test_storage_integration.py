"""Test integration between classification and storage systems."""

from datetime import date
from decimal import Decimal
from pathlib import Path


from small_business.classification.models import ClassificationRule
from small_business.classification.storage_integration import (
	classify_and_save,
	load_and_classify_unclassified,
)
from small_business.models.transaction import JournalEntry, Transaction
from small_business.storage import load_transactions, save_transaction


def test_classify_and_save(tmp_path: Path):
	"""Test classifying and saving transaction to storage."""
	# Setup storage directory
	data_dir = tmp_path / "data"
	rules_file = tmp_path / "rules.yaml"

	# Create unclassified transaction
	txn = Transaction(
		transaction_id="TXN-001",
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		entries=[
			JournalEntry(
				account_code="EXP-UNCLASSIFIED", debit=Decimal("45.50"), credit=Decimal("0")
			),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("45.50")),
		],
	)

	rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		)
	]

	# Classify and save
	result = classify_and_save(
		txn,
		rules,
		rules_file,
		data_dir,
		auto_accept_threshold=1.0,
	)

	assert result.decision.value == "accepted"
	assert result.classified_transaction is not None

	# Verify transaction was saved to storage
	loaded_txns = load_transactions(data_dir, txn.date)
	assert len(loaded_txns) == 1
	assert loaded_txns[0].transaction_id == "TXN-001"
	assert loaded_txns[0].entries[0].account_code == "EXP-GRO"


def test_load_and_classify_unclassified(tmp_path: Path):
	"""Test loading unclassified transactions and classifying them."""
	data_dir = tmp_path / "data"
	rules_file = tmp_path / "rules.yaml"

	# Save unclassified transactions
	txn1 = Transaction(
		transaction_id="TXN-001",
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		entries=[
			JournalEntry(
				account_code="EXP-UNCLASSIFIED", debit=Decimal("45.50"), credit=Decimal("0")
			),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("45.50")),
		],
	)

	txn2 = Transaction(
		transaction_id="TXN-002",
		date=date(2025, 11, 16),
		description="COLES 5678",
		entries=[
			JournalEntry(
				account_code="EXP-UNCLASSIFIED", debit=Decimal("32.00"), credit=Decimal("0")
			),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("32.00")),
		],
	)

	txn3 = Transaction(
		transaction_id="TXN-003",
		date=date(2025, 11, 17),
		description="PAYMENT RECEIVED",
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("500.00"), credit=Decimal("0")),
			JournalEntry(account_code="INC-SALES", debit=Decimal("0"), credit=Decimal("500.00")),
		],
	)

	save_transaction(txn1, data_dir)
	save_transaction(txn2, data_dir)
	save_transaction(txn3, data_dir)

	rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		)
	]

	# Load and classify (use any date in FY 2025-26)
	results = load_and_classify_unclassified(
		data_dir,
		txn1.date,
		rules,
		rules_file,
		auto_accept_threshold=1.0,
	)

	# Should find 2 unclassified transactions
	assert len(results) == 2
	assert "TXN-001" in results
	assert "TXN-002" in results
	assert "TXN-003" not in results  # Already classified (INC-SALES)

	# TXN-001 should be auto-accepted
	assert results["TXN-001"].decision.value == "accepted"

	# TXN-002 should be pending (no matching rule)
	assert results["TXN-002"].decision.value == "pending"

	# Verify TXN-001 was updated in storage
	loaded_txns = load_transactions(data_dir, txn1.date)
	txn_001 = next(t for t in loaded_txns if t.transaction_id == "TXN-001")
	assert txn_001.entries[0].account_code == "EXP-GRO"

	# Verify TXN-002 remains unclassified
	txn_002 = next(t for t in loaded_txns if t.transaction_id == "TXN-002")
	assert txn_002.entries[0].account_code == "EXP-UNCLASSIFIED"
