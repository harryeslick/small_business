"""Integration test for complete bank import workflow."""

import tempfile
from datetime import date
from pathlib import Path

from small_business.bank import import_bank_statement
from small_business.models import get_financial_year
from small_business.models.config import BankFormat
from small_business.storage import StorageRegistry


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
		storage = StorageRegistry(data_dir)
		fy = get_financial_year(date(2025, 11, 15))
		transactions = storage.get_all_transactions(financial_year=fy)
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
		storage = StorageRegistry(data_dir)
		fy = get_financial_year(date(2025, 11, 15))
		transactions = storage.get_all_transactions(financial_year=fy)
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
		storage = StorageRegistry(data_dir)
		fy_2024_25_txns = storage.get_all_transactions(financial_year="2024-25")
		fy_2025_26_txns = storage.get_all_transactions(financial_year="2025-26")

		assert len(fy_2024_25_txns) == 1
		assert len(fy_2025_26_txns) == 1

		assert fy_2024_25_txns[0].financial_year == "2024-25"
		assert fy_2025_26_txns[0].financial_year == "2025-26"

	finally:
		csv_path.unlink()
