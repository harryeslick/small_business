"""Test bank import workflow orchestrator."""

import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.bank.import_workflow import import_bank_statement
from small_business.models import get_financial_year
from small_business.models.config import BankFormat
from small_business.storage import StorageRegistry


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
		storage = StorageRegistry(data_dir)
		fy = get_financial_year(date(2025, 11, 15))
		transactions = storage.get_all_transactions(financial_year=fy)
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
		storage = StorageRegistry(data_dir)
		fy = get_financial_year(date(2025, 11, 10))
		transactions = storage.get_all_transactions(financial_year=fy)
		assert len(transactions) == 1

	finally:
		csv_path.unlink()


def test_import_preserves_traceability_metadata(tmp_path):
	"""Test that full import workflow preserves traceability metadata."""
	# Create test CSV
	csv_content = """Date,Description,Debit,Credit,Balance
10/11/2025,WOOLWORTHS 1234,45.50,,954.50
15/11/2025,PAYMENT RECEIVED,,100.00,1054.50
"""
	csv_filename = "test_statement_nov2025.csv"
	csv_path = tmp_path / csv_filename
	csv_path.write_text(csv_content)

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

	assert result["imported"] == 2

	# Verify transactions have traceability metadata
	storage = StorageRegistry(data_dir)
	fy = get_financial_year(date(2025, 11, 15))
	transactions = storage.get_all_transactions(financial_year=fy)

	# Check first transaction
	txn1 = transactions[0]
	assert txn1.import_source == "bank_import"
	assert txn1.import_file == csv_filename
	assert txn1.import_date == date.today()
	assert txn1.import_line_number == 2  # First data row after header
	# Composite key fields (transparent, not hashed - 4 fields including account)
	assert txn1.import_match_date == date(2025, 11, 10)
	assert txn1.import_match_description == "WOOLWORTHS 1234"
	assert txn1.import_match_amount == Decimal("-45.50")
	assert txn1.import_match_account == "BANK-CHQ"

	# Check second transaction
	txn2 = transactions[1]
	assert txn2.import_source == "bank_import"
	assert txn2.import_file == csv_filename
	assert txn2.import_line_number == 3  # Second data row
	assert txn2.import_match_date == date(2025, 11, 15)
	assert txn2.import_match_description == "PAYMENT RECEIVED"
	assert txn2.import_match_amount == Decimal("100.00")
	assert txn2.import_match_account == "BANK-CHQ"


def test_import_same_transaction_different_accounts_not_duplicate(tmp_path):
	"""Test that same transaction on different accounts doesn't get flagged as duplicate.
	
	Real-world scenario: $100 transfer between Cheque and Savings accounts.
	Both CSVs show the same transaction (different perspective).
	Should import BOTH, not flag second as duplicate.
	"""
	# First: Import from Cheque account (money out)
	cheque_csv = """Date,Description,Debit,Credit,Balance
15/11/2025,Transfer to Savings,100.00,,900.00
"""
	cheque_path = tmp_path / "cheque.csv"
	cheque_path.write_text(cheque_csv)

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

	# Import cheque statement
	result1 = import_bank_statement(
		csv_path=cheque_path,
		bank_format=bank_format,
		bank_name="Test Bank",
		account_name="Business Cheque",
		bank_account_code="BANK-CHQ",  # Cheque account
		data_dir=data_dir,
	)

	assert result1["imported"] == 1
	assert result1["duplicates"] == 0

	# Second: Import from Savings account (money in) - SAME transaction
	savings_csv = """Date,Description,Debit,Credit,Balance
15/11/2025,Transfer to Savings,,100.00,1100.00
"""
	savings_path = tmp_path / "savings.csv"
	savings_path.write_text(savings_csv)

	# Import savings statement - should NOT flag as duplicate
	result2 = import_bank_statement(
		csv_path=savings_path,
		bank_format=bank_format,
		bank_name="Test Bank",
		account_name="Business Savings",
		bank_account_code="BANK-SAV",  # Different account code
		data_dir=data_dir,
	)

	# Should import successfully, not be flagged as duplicate
	assert result2["imported"] == 1
	assert result2["duplicates"] == 0

	# Verify both transactions exist with correct account codes
	storage = StorageRegistry(data_dir)
	fy = get_financial_year(date(2025, 11, 15))
	transactions = storage.get_all_transactions(financial_year=fy)

	assert len(transactions) == 2

	# Check both have correct account match fields
	chq_txn = [t for t in transactions if t.import_match_account == "BANK-CHQ"][0]
	assert chq_txn.import_match_account == "BANK-CHQ"
	assert chq_txn.import_match_amount == Decimal("-100.00")  # Money out

	sav_txn = [t for t in transactions if t.import_match_account == "BANK-SAV"][0]
	assert sav_txn.import_match_account == "BANK-SAV"
	assert sav_txn.import_match_amount == Decimal("100.00")  # Money in
