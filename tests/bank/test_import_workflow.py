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
