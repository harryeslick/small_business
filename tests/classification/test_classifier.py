"""Test transaction classifier."""

from datetime import date
from decimal import Decimal

from small_business.classification.classifier import classify_batch, classify_transaction
from small_business.classification.models import ClassificationRule
from small_business.models.transaction import JournalEntry, Transaction


def test_classify_transaction_match():
	"""Test classifying transaction with matching rule."""
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

	rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS|COLES",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		)
	]

	match = classify_transaction(txn, rules)
	assert match is not None
	assert match.rule.account_code == "EXP-GRO"
	assert match.confidence == 1.0


def test_classify_transaction_no_match():
	"""Test classifying transaction with no matching rule."""
	txn = Transaction(
		date=date(2025, 11, 15),
		description="UNKNOWN MERCHANT",
		entries=[
			JournalEntry(
				account_code="EXP-UNCLASSIFIED", debit=Decimal("45.50"), credit=Decimal("0")
			),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("45.50")),
		],
	)

	rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		)
	]

	match = classify_transaction(txn, rules)
	assert match is None


def test_classify_batch():
	"""Test classifying batch of transactions."""
	transactions = [
		Transaction(
			transaction_id="TXN-001",
			date=date(2025, 11, 15),
			description="WOOLWORTHS 1234",
			entries=[
				JournalEntry(
					account_code="EXP-UNCLASSIFIED", debit=Decimal("45.50"), credit=Decimal("0")
				),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("45.50")),
			],
		),
		Transaction(
			transaction_id="TXN-002",
			date=date(2025, 11, 16),
			description="QANTAS FLIGHT",
			entries=[
				JournalEntry(
					account_code="EXP-UNCLASSIFIED", debit=Decimal("280.00"), credit=Decimal("0")
				),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("280.00")),
			],
		),
		Transaction(
			transaction_id="TXN-003",
			date=date(2025, 11, 17),
			description="UNKNOWN MERCHANT",
			entries=[
				JournalEntry(
					account_code="EXP-UNCLASSIFIED", debit=Decimal("50.00"), credit=Decimal("0")
				),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("50.00")),
			],
		),
	]

	rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		),
		ClassificationRule(
			pattern=r"QANTAS",
			account_code="EXP-TRV-FLT",
			description="Flights",
			gst_inclusive=True,
		),
	]

	results = classify_batch(transactions, rules)

	assert len(results) == 3
	assert results["TXN-001"] is not None
	assert results["TXN-001"].rule.account_code == "EXP-GRO"
	assert results["TXN-002"] is not None
	assert results["TXN-002"].rule.account_code == "EXP-TRV-FLT"
	assert results["TXN-003"] is None
