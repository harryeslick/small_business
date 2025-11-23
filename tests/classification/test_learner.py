"""Test rule learning from user classifications."""

from datetime import date
from decimal import Decimal

from small_business.classification.learner import learn_rule
from small_business.models.transaction import JournalEntry, Transaction


def test_learn_rule_from_merchant():
	"""Test learning classification rule from merchant transaction."""
	txn = Transaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234 PERTH",
		entries=[
			JournalEntry(
				account_code="EXP-UNCLASSIFIED", debit=Decimal("45.50"), credit=Decimal("0")
			),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("45.50")),
		],
	)

	rule = learn_rule(
		transaction=txn,
		account_code="EXP-GRO",
		description="Groceries",
		gst_inclusive=True,
	)

	# Should extract merchant name as pattern
	assert rule.pattern == r"WOOLWORTHS"
	assert rule.account_code == "EXP-GRO"
	assert rule.description == "Groceries"
	assert rule.gst_inclusive is True
	assert rule.priority == 0


def test_learn_rule_with_numbers():
	"""Test learning rule extracts text without numbers."""
	txn = Transaction(
		date=date(2025, 11, 15),
		description="COLES 5678 SUPERMARKET",
		entries=[
			JournalEntry(
				account_code="EXP-UNCLASSIFIED", debit=Decimal("32.00"), credit=Decimal("0")
			),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("32.00")),
		],
	)

	rule = learn_rule(
		transaction=txn,
		account_code="EXP-GRO",
		description="Groceries",
		gst_inclusive=True,
	)

	# Should extract "COLES" without the store number
	assert rule.pattern == r"COLES"


def test_learn_rule_multiple_words():
	"""Test learning rule from multi-word merchant."""
	txn = Transaction(
		date=date(2025, 11, 15),
		description="BUNNINGS WAREHOUSE PERTH",
		entries=[
			JournalEntry(
				account_code="EXP-UNCLASSIFIED", debit=Decimal("125.00"), credit=Decimal("0")
			),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("125.00")),
		],
	)

	rule = learn_rule(
		transaction=txn,
		account_code="EXP-SUP",
		description="Supplies",
		gst_inclusive=True,
	)

	# Should extract "BUNNINGS WAREHOUSE"
	assert rule.pattern == r"BUNNINGS WAREHOUSE"


def test_learn_rule_with_priority():
	"""Test learning rule with custom priority."""
	txn = Transaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		entries=[
			JournalEntry(
				account_code="EXP-UNCLASSIFIED", debit=Decimal("45.50"), credit=Decimal("0")
			),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("45.50")),
		],
	)

	rule = learn_rule(
		transaction=txn,
		account_code="EXP-GRO",
		description="Groceries",
		gst_inclusive=True,
		priority=10,
	)

	assert rule.priority == 10
