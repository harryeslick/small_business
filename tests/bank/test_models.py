"""Test bank import models."""

from datetime import date
from decimal import Decimal

from small_business.bank.models import BankTransaction, ImportedBankStatement


def test_bank_transaction_debit():
	"""Test bank transaction with debit amount."""
	txn = BankTransaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		debit=Decimal("45.50"),
		credit=Decimal("0"),
		balance=Decimal("1000.00"),
	)
	assert txn.amount == Decimal("-45.50")
	assert txn.is_debit is True


def test_bank_transaction_credit():
	"""Test bank transaction with credit amount."""
	txn = BankTransaction(
		date=date(2025, 11, 15),
		description="PAYMENT RECEIVED",
		debit=Decimal("0"),
		credit=Decimal("100.00"),
		balance=Decimal("1100.00"),
	)
	assert txn.amount == Decimal("100.00")
	assert txn.is_debit is False


def test_imported_statement():
	"""Test imported bank statement with transactions."""
	stmt = ImportedBankStatement(
		bank_name="commonwealth",
		account_name="Business Cheque",
		import_date=date(2025, 11, 15),
		transactions=[
			BankTransaction(
				date=date(2025, 11, 1),
				description="Opening balance",
				debit=Decimal("0"),
				credit=Decimal("0"),
				balance=Decimal("1000.00"),
			),
			BankTransaction(
				date=date(2025, 11, 10),
				description="WOOLWORTHS",
				debit=Decimal("50.00"),
				credit=Decimal("0"),
				balance=Decimal("950.00"),
			),
		],
	)
	assert stmt.bank_name == "commonwealth"
	assert len(stmt.transactions) == 2


def test_bank_transaction_with_line_number():
	"""Test bank transaction can track CSV line number for traceability."""
	txn = BankTransaction(
		date=date(2025, 11, 15),
		description="PAYMENT RECEIVED",
		debit=Decimal("0"),
		credit=Decimal("100.00"),
		balance=Decimal("1100.00"),
		line_number=42,
	)
	assert txn.line_number == 42


def test_bank_transaction_without_line_number_defaults_to_none():
	"""Test bank transaction without line number defaults to None."""
	txn = BankTransaction(
		date=date(2025, 11, 15),
		description="PAYMENT RECEIVED",
		debit=Decimal("0"),
		credit=Decimal("100.00"),
	)
	assert txn.line_number is None
