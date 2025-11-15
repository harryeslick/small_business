"""Test CSV parser."""

import tempfile
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
