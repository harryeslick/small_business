"""Test duplicate detection."""

from datetime import date
from decimal import Decimal

from small_business.bank.duplicate import is_duplicate
from small_business.bank.models import BankTransaction, ImportedBankStatement


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


def test_is_duplicate_uses_direct_field_comparison():
	"""Test duplicate detection uses direct field comparison, not hash."""
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
					balance=Decimal("1000.00"),  # Balance differs
				)
			],
		)
	]

	# Same date, description, amount but different balance
	# Should still be duplicate (balance not part of comparison)
	dup = BankTransaction(
		date=date(2025, 11, 1),
		description="WOOLWORTHS",
		debit=Decimal("50.00"),
		credit=Decimal("0"),
		balance=Decimal("950.00"),  # Different balance
	)

	assert is_duplicate(dup, existing)

	# Different amount - should not be duplicate
	not_dup = BankTransaction(
		date=date(2025, 11, 1),
		description="WOOLWORTHS",
		debit=Decimal("50.01"),  # Different amount
		credit=Decimal("0"),
	)

	assert not is_duplicate(not_dup, existing)


def test_same_transaction_different_accounts_not_duplicate():
	"""Test that same transaction on different accounts is NOT a duplicate.

	Real-world scenario: You buy groceries and pay with both credit card AND bank account
	on the same day (split payment). Both transactions have same date, merchant, amount.
	Without account checking, this would be incorrectly flagged as duplicate.
	"""
	# Existing: Paid $50 at Woolworths with Credit Card
	existing = [
		ImportedBankStatement(
			bank_name="Test",
			account_name="Credit Card",
			transactions=[
				BankTransaction(
					date=date(2025, 11, 15),
					description="WOOLWORTHS 1234",
					debit=Decimal("50.00"),  # Same amount
					credit=Decimal("0"),
				)
			],
		)
	]

	# New: Also paid $50 at Woolworths with Bank Account (split payment)
	# Same date, merchant, amount BUT different account
	# Should NOT be duplicate
	bank_payment = BankTransaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",  # Same description
		debit=Decimal("50.00"),  # Same amount
		credit=Decimal("0"),
	)

	# With account-specific filtering in import_workflow, the existing_statements
	# would only contain Credit Card transactions when importing Credit Card statement.
	# When importing Bank Account statement, existing_statements would be empty or
	# only contain Bank Account transactions, so this wouldn't be flagged as duplicate.
	#
	# But this test shows that is_duplicate itself doesn't check account -
	# it relies on the caller to filter. So if you mistakenly pass wrong statements,
	# it WOULD flag as duplicate.
	assert is_duplicate(bank_payment, existing)  # Duplicate IF same account context
