"""Classification workflow orchestration."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from small_business.classification.applicator import apply_classification
from small_business.classification.classifier import classify_transaction
from small_business.classification.learner import learn_rule
from small_business.classification.models import ClassificationRule, RuleMatch
from small_business.classification.rule_store import load_rules, save_rules
from small_business.models.transaction import Transaction


class AcceptanceDecision(str, Enum):
	"""Decision on classification acceptance."""

	ACCEPTED = "accepted"  # Auto-accepted or user accepted suggested classification
	REJECTED = "rejected"  # User rejected and provided alternative
	MANUAL = "manual"  # No suggestion, user classified manually
	PENDING = "pending"  # Awaiting user decision


@dataclass
class ClassificationResult:
	"""Result of classification workflow."""

	transaction: Transaction  # Original transaction
	classified_transaction: Transaction | None  # Transaction with updated account code
	match: RuleMatch | None  # Matched rule (if any)
	decision: AcceptanceDecision
	learned_rule: ClassificationRule | None  # Rule learned from this classification


def classify_and_review(
	transaction: Transaction,
	rules: list[ClassificationRule],
	auto_accept_threshold: float = 1.0,
	user_accepted: bool | None = None,
	user_classification: tuple[str, str, bool] | None = None,
) -> ClassificationResult:
	"""Classify a transaction and handle user review.

	Args:
		transaction: Transaction to classify
		rules: List of classification rules
		auto_accept_threshold: Confidence threshold for auto-acceptance
		user_accepted: Whether user accepted the suggested classification (None = pending)
		user_classification: Tuple of (account_code, description, gst_inclusive) for manual classification

	Returns:
		ClassificationResult with decision and learned rule if applicable
	"""
	# Try to match against existing rules
	match = classify_transaction(transaction, rules)

	# Case 1: No match, user provides manual classification
	if match is None and user_classification:
		account_code, description, gst_inclusive = user_classification
		classified_txn = Transaction(
			transaction_id=transaction.transaction_id,
			date=transaction.date,
			description=transaction.description,
			entries=[
				entry.model_copy(update={"account_code": account_code})
				if "UNCLASSIFIED" in entry.account_code
				else entry
				for entry in transaction.entries
			],
		)
		learned = learn_rule(transaction, account_code, description, gst_inclusive)
		return ClassificationResult(
			transaction=transaction,
			classified_transaction=classified_txn,
			match=None,
			decision=AcceptanceDecision.MANUAL,
			learned_rule=learned,
		)

	# Case 2: No match, awaiting user input
	if match is None:
		return ClassificationResult(
			transaction=transaction,
			classified_transaction=None,
			match=None,
			decision=AcceptanceDecision.PENDING,
			learned_rule=None,
		)

	# Case 3: Match found, check confidence for auto-accept
	classified_txn = apply_classification(transaction, match)

	if match.confidence >= auto_accept_threshold:
		# Auto-accept high confidence matches
		return ClassificationResult(
			transaction=transaction,
			classified_transaction=classified_txn,
			match=match,
			decision=AcceptanceDecision.ACCEPTED,
			learned_rule=None,  # No learning needed
		)

	# Case 4: Match found but below threshold, user decision needed
	if user_accepted is None:
		# Awaiting user decision
		return ClassificationResult(
			transaction=transaction,
			classified_transaction=classified_txn,
			match=match,
			decision=AcceptanceDecision.PENDING,
			learned_rule=None,
		)

	# Case 5: User accepted the suggestion
	if user_accepted:
		learned = learn_rule(
			transaction,
			match.rule.account_code,
			match.rule.description,
			match.rule.gst_inclusive,
		)
		return ClassificationResult(
			transaction=transaction,
			classified_transaction=classified_txn,
			match=match,
			decision=AcceptanceDecision.ACCEPTED,
			learned_rule=learned,
		)

	# Case 6: User rejected and provided alternative
	if user_classification:
		account_code, description, gst_inclusive = user_classification
		classified_txn = Transaction(
			transaction_id=transaction.transaction_id,
			date=transaction.date,
			description=transaction.description,
			entries=[
				entry.model_copy(update={"account_code": account_code})
				if "UNCLASSIFIED" in entry.account_code
				else entry
				for entry in transaction.entries
			],
		)
		learned = learn_rule(transaction, account_code, description, gst_inclusive)
		return ClassificationResult(
			transaction=transaction,
			classified_transaction=classified_txn,
			match=match,
			decision=AcceptanceDecision.REJECTED,
			learned_rule=learned,
		)

	# Should not reach here
	return ClassificationResult(
		transaction=transaction,
		classified_transaction=classified_txn,
		match=match,
		decision=AcceptanceDecision.PENDING,
		learned_rule=None,
	)


def process_unclassified_transactions(
	transactions: list[Transaction],
	rules: list[ClassificationRule],
	rules_file: Path,
	auto_accept_threshold: float = 1.0,
) -> dict[str, ClassificationResult]:
	"""Process a batch of unclassified transactions.

	Auto-accepts high-confidence matches and returns pending decisions for review.

	Args:
		transactions: List of transactions to classify
		rules: Current classification rules
		rules_file: Path to rules file (for saving learned rules)
		auto_accept_threshold: Confidence threshold for auto-acceptance

	Returns:
		Dictionary mapping transaction_id to ClassificationResult
	"""
	results = {}
	learned_rules = []

	for txn in transactions:
		result = classify_and_review(txn, rules, auto_accept_threshold)
		results[txn.transaction_id] = result

		# Collect learned rules from auto-accepted classifications
		if result.learned_rule:
			learned_rules.append(result.learned_rule)

	# Save learned rules if any
	if learned_rules:
		all_rules = rules + learned_rules
		save_rules(all_rules, rules_file)

	return results
