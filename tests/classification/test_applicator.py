"""Test classification applicator."""

from datetime import date
from decimal import Decimal

from small_business.classification.applicator import apply_classification
from small_business.classification.models import ClassificationRule, RuleMatch
from small_business.models.transaction import JournalEntry, Transaction


def test_apply_classification_expense():
	"""Test applying classification to expense transaction."""
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

	match = RuleMatch(
		rule=ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		),
		confidence=1.0,
		matched_text="WOOLWORTHS",
	)

	updated = apply_classification(txn, match)

	# Check account code was updated
	assert len(updated.entries) == 2
	expense_entry = next(e for e in updated.entries if e.debit > 0)
	assert expense_entry.account_code == "EXP-GRO"

	# Bank entry should remain unchanged
	bank_entry = next(e for e in updated.entries if e.credit > 0)
	assert bank_entry.account_code == "BANK-CHQ"


def test_apply_classification_income():
	"""Test applying classification to income transaction."""
	txn = Transaction(
		date=date(2025, 11, 15),
		description="PAYMENT RECEIVED",
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("500.00"), credit=Decimal("0")),
			JournalEntry(
				account_code="INC-UNCLASSIFIED", debit=Decimal("0"), credit=Decimal("500.00")
			),
		],
	)

	match = RuleMatch(
		rule=ClassificationRule(
			pattern=r"PAYMENT",
			account_code="INC-SALES",
			description="Sales",
			gst_inclusive=True,
		),
		confidence=1.0,
		matched_text="PAYMENT",
	)

	updated = apply_classification(txn, match)

	# Check account code was updated
	income_entry = next(e for e in updated.entries if e.credit > 0)
	assert income_entry.account_code == "INC-SALES"

	# Bank entry should remain unchanged
	bank_entry = next(e for e in updated.entries if e.debit > 0)
	assert bank_entry.account_code == "BANK-CHQ"


def test_apply_classification_preserves_original():
	"""Test applying classification creates new transaction (doesn't modify original)."""
	original = Transaction(
		date=date(2025, 11, 15),
		description="WOOLWORTHS 1234",
		entries=[
			JournalEntry(
				account_code="EXP-UNCLASSIFIED", debit=Decimal("45.50"), credit=Decimal("0")
			),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("45.50")),
		],
	)

	match = RuleMatch(
		rule=ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		),
		confidence=1.0,
		matched_text="WOOLWORTHS",
	)

	updated = apply_classification(original, match)

	# Original should be unchanged
	assert original.entries[0].account_code == "EXP-UNCLASSIFIED"

	# Updated should have new account code
	assert updated.entries[0].account_code == "EXP-GRO"

	# Should be different objects
	assert original is not updated
