"""Transaction classification logic."""

from small_business.classification.matcher import find_best_match
from small_business.classification.models import ClassificationRule, RuleMatch
from small_business.models.transaction import Transaction


def classify_transaction(
	transaction: Transaction,
	rules: list[ClassificationRule],
) -> RuleMatch | None:
	"""Classify a transaction using classification rules.

	Args:
		transaction: Transaction to classify
		rules: List of classification rules

	Returns:
		RuleMatch if a rule matches, None otherwise
	"""
	return find_best_match(transaction.description, rules)


def classify_batch(
	transactions: list[Transaction],
	rules: list[ClassificationRule],
) -> dict[str, RuleMatch | None]:
	"""Classify a batch of transactions.

	Args:
		transactions: List of transactions to classify
		rules: List of classification rules

	Returns:
		Dictionary mapping transaction_id to RuleMatch (or None if no match)
	"""
	results = {}

	for txn in transactions:
		match = classify_transaction(txn, rules)
		results[txn.transaction_id] = match

	return results
