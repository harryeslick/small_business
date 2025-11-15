"""Test duplicate detection."""

from datetime import date
from decimal import Decimal

from small_business.bank.duplicate import generate_transaction_hash, is_duplicate
from small_business.bank.models import BankTransaction, ImportedBankStatement


def test_generate_transaction_hash_same():
	"""Test identical transactions generate same hash."""
	txn1 = BankTransaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		debit=Decimal("45.50"),
		credit=Decimal("0"),
		balance=Decimal("954.50"),
	)

	txn2 = BankTransaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		debit=Decimal("45.50"),
		credit=Decimal("0"),
		balance=Decimal("1000.00"),  # Different balance
	)

	# Same hash despite different balance
	assert generate_transaction_hash(txn1) == generate_transaction_hash(txn2)


def test_generate_transaction_hash_different():
	"""Test different transactions generate different hashes."""
	txn1 = BankTransaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		debit=Decimal("45.50"),
		credit=Decimal("0"),
	)

	txn2 = BankTransaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		debit=Decimal("45.51"),  # Different amount
		credit=Decimal("0"),
	)

	assert generate_transaction_hash(txn1) != generate_transaction_hash(txn2)


def test_is_duplicate():
	"""Test duplicate detection in existing statements."""
	existing = [
		ImportedBankStatement(
			bank_name="Test",
			account_name="Test",
			transactions=[
				BankTransaction(
					date=date(2025, 11, 1),
					description="WOOLWORTHS",
					debit=Decimal("50.00"),
					credit=Decimal("0"),
				),
				BankTransaction(
					date=date(2025, 11, 2),
					description="COLES",
					debit=Decimal("30.00"),
					credit=Decimal("0"),
				),
			],
		)
	]

	# Duplicate transaction
	dup = BankTransaction(
		date=date(2025, 11, 1),
		description="WOOLWORTHS",
		debit=Decimal("50.00"),
		credit=Decimal("0"),
	)

	# New transaction
	new = BankTransaction(
		date=date(2025, 11, 3),
		description="ALDI",
		debit=Decimal("20.00"),
		credit=Decimal("0"),
	)

	assert is_duplicate(dup, existing)
	assert not is_duplicate(new, existing)
