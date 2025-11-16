"""Integration between classification and storage systems."""

from datetime import date
from pathlib import Path

from small_business.classification.models import ClassificationRule
from small_business.classification.workflow import (
	ClassificationResult,
	classify_and_review,
	process_unclassified_transactions,
)
from small_business.models.transaction import Transaction
from small_business.storage import (
	load_transactions,
	save_transaction,
	transaction_exists,
	update_transaction,
)


def classify_and_save(
	transaction: Transaction,
	rules: list[ClassificationRule],
	rules_file: Path,
	data_dir: Path,
	auto_accept_threshold: float = 1.0,
	user_accepted: bool | None = None,
	user_classification: tuple[str, str, bool] | None = None,
) -> ClassificationResult:
	"""Classify a transaction and save to storage.

	Args:
		transaction: Transaction to classify
		rules: Classification rules
		rules_file: Path to rules YAML file
		data_dir: Base data directory for transactions
		auto_accept_threshold: Confidence threshold for auto-acceptance
		user_accepted: Whether user accepted suggested classification
		user_classification: Manual classification (account_code, description, gst_inclusive)

	Returns:
		ClassificationResult with decision and learned rule
	"""
	# Classify the transaction
	result = classify_and_review(
		transaction, rules, auto_accept_threshold, user_accepted, user_classification
	)

	# Save classified transaction if accepted or manually classified
	if result.classified_transaction and result.decision.value in ("accepted", "rejected", "manual"):
		# Check if transaction already exists in storage
		if transaction_exists(transaction.transaction_id, data_dir, transaction.date):
			# Update existing transaction
			update_transaction(result.classified_transaction, data_dir)
		else:
			# Save new transaction
			save_transaction(result.classified_transaction, data_dir)

	return result


def load_and_classify_unclassified(
	data_dir: Path,
	txn_date: date,
	rules: list[ClassificationRule],
	rules_file: Path,
	auto_accept_threshold: float = 1.0,
) -> dict[str, ClassificationResult]:
	"""Load unclassified transactions from storage and classify them.

	Args:
		data_dir: Base data directory for transactions
		txn_date: Any date in the financial year to process
		rules: Classification rules
		rules_file: Path to rules YAML file
		auto_accept_threshold: Confidence threshold for auto-acceptance

	Returns:
		Dictionary mapping transaction_id to ClassificationResult
	"""
	# Load all transactions for the financial year
	all_txns = load_transactions(data_dir, txn_date)

	# Filter for unclassified transactions
	unclassified = [
		txn for txn in all_txns if any("UNCLASSIFIED" in entry.account_code for entry in txn.entries)
	]

	# Classify the unclassified transactions
	results = process_unclassified_transactions(
		unclassified, rules, rules_file, auto_accept_threshold
	)

	# Save auto-accepted classifications back to storage
	for txn_id, result in results.items():
		if result.classified_transaction and result.decision.value == "accepted":
			update_transaction(result.classified_transaction, data_dir)

	return results
