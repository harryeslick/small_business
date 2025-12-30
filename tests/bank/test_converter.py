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


def test_convert_with_import_metadata():
	"""Test converting bank transaction preserves import traceability metadata."""
	bank_txn = BankTransaction(
		date=date(2025, 11, 15),
		description="PAYMENT RECEIVED",
		debit=Decimal("0"),
		credit=Decimal("100.00"),
		line_number=42,
	)

	txn = convert_to_transaction(
		bank_txn,
		bank_account_code="BANK-CHQ",
		import_file="statement_nov_2025.csv",
		import_date=date(2025, 12, 7),
	)

	# Should include import metadata
	assert txn.import_source == "bank_import"
	assert txn.import_file == "statement_nov_2025.csv"
	assert txn.import_date == date(2025, 12, 7)
	assert txn.import_line_number == 42

	# Composite key for duplicate detection (transparent, not hashed - 4 fields)
	assert txn.import_match_date == date(2025, 11, 15)
	assert txn.import_match_description == "PAYMENT RECEIVED"
	assert txn.import_match_amount == Decimal("100.00")
	assert txn.import_match_account == "BANK-CHQ"


def test_convert_without_import_metadata():
	"""Test converting without metadata results in None values."""
	bank_txn = BankTransaction(
		date=date(2025, 11, 15),
		description="PAYMENT RECEIVED",
		debit=Decimal("0"),
		credit=Decimal("100.00"),
	)

	txn = convert_to_transaction(
		bank_txn,
		bank_account_code="BANK-CHQ",
	)

	# Should have no import metadata
	assert txn.import_source is None
	assert txn.import_file is None
	assert txn.import_date is None
	assert txn.import_line_number is None
	# Composite key fields also None (4 fields)
	assert txn.import_match_date is None
	assert txn.import_match_description is None
	assert txn.import_match_amount is None
	assert txn.import_match_account is None
