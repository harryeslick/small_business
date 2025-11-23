"""Test classification workflow orchestration."""

from datetime import date
from decimal import Decimal
from pathlib import Path


from small_business.classification.models import ClassificationRule
from small_business.classification.workflow import (
	AcceptanceDecision,
	classify_and_review,
	process_unclassified_transactions,
)
from small_business.models.transaction import JournalEntry, Transaction


def test_classify_and_review_auto_accept():
	"""Test automatic acceptance of high-confidence classifications."""
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

	rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		)
	]

	# Auto-accept confidence threshold = 1.0
	result = classify_and_review(txn, rules, auto_accept_threshold=1.0)

	assert result.decision == AcceptanceDecision.ACCEPTED
	assert result.classified_transaction is not None
	assert result.classified_transaction.entries[0].account_code == "EXP-GRO"
	assert result.match is not None
	assert result.learned_rule is None  # No learning needed for auto-accept


def test_classify_and_review_manual_accept():
	"""Test manual acceptance adds learned rule."""
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

	rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		)
	]

	# Manual acceptance (user confirmed)
	result = classify_and_review(
		txn,
		rules,
		auto_accept_threshold=1.1,
		user_accepted=True,  # Higher than confidence
	)

	assert result.decision == AcceptanceDecision.ACCEPTED
	assert result.classified_transaction is not None
	assert result.learned_rule is not None
	assert result.learned_rule.pattern == r"WOOLWORTHS"


def test_classify_and_review_rejected():
	"""Test rejection of classification."""
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

	rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		)
	]

	# User rejected
	result = classify_and_review(
		txn,
		rules,
		auto_accept_threshold=1.1,
		user_accepted=False,
		user_classification=("EXP-OTH", "Other expense", True),
	)

	assert result.decision == AcceptanceDecision.REJECTED
	assert result.classified_transaction is not None
	assert result.classified_transaction.entries[0].account_code == "EXP-OTH"
	assert result.learned_rule is not None
	assert result.learned_rule.account_code == "EXP-OTH"


def test_classify_and_review_no_match():
	"""Test manual classification when no rule matches."""
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

	rules = []

	# Manual classification
	result = classify_and_review(
		txn, rules, auto_accept_threshold=1.0, user_classification=("EXP-OTH", "Other", True)
	)

	assert result.decision == AcceptanceDecision.MANUAL
	assert result.classified_transaction is not None
	assert result.classified_transaction.entries[0].account_code == "EXP-OTH"
	assert result.match is None
	assert result.learned_rule is not None
	assert result.learned_rule.pattern == r"UNKNOWN MERCHANT"


def test_process_unclassified_transactions(tmp_path: Path):
	"""Test batch processing of unclassified transactions."""
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
			description="COLES 5678",
			entries=[
				JournalEntry(
					account_code="EXP-UNCLASSIFIED", debit=Decimal("32.00"), credit=Decimal("0")
				),
				JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("32.00")),
			],
		),
	]

	rules = [
		ClassificationRule(
			pattern=r"WOOLWORTHS",
			account_code="EXP-GRO",
			description="Groceries",
			gst_inclusive=True,
		)
	]

	rules_file = tmp_path / "rules.yaml"

	# Process with auto-accept
	results = process_unclassified_transactions(
		transactions, rules, rules_file, auto_accept_threshold=1.0
	)

	assert len(results) == 2
	assert results["TXN-001"].decision == AcceptanceDecision.ACCEPTED
	assert results["TXN-002"].decision == AcceptanceDecision.PENDING  # No match
