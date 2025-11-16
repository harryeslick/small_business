"""Apply classification rules to transactions."""

from small_business.classification.models import RuleMatch
from small_business.models.transaction import JournalEntry, Transaction


def apply_classification(
	transaction: Transaction,
	match: RuleMatch,
) -> Transaction:
	"""Apply a classification rule to a transaction.

	Updates the account code for UNCLASSIFIED entries to the matched rule's account code.
	Returns a new Transaction instance (does not modify the original).

	Args:
		transaction: Transaction to classify
		match: RuleMatch containing the rule to apply

	Returns:
		New Transaction with updated account codes
	"""
	# Create new journal entries with updated account codes
	updated_entries = []

	for entry in transaction.entries:
		# Replace UNCLASSIFIED account codes with the matched rule's account code
		if "UNCLASSIFIED" in entry.account_code:
			new_entry = JournalEntry(
				account_code=match.rule.account_code,
				debit=entry.debit,
				credit=entry.credit,
			)
			updated_entries.append(new_entry)
		else:
			# Keep bank and other accounts unchanged
			updated_entries.append(entry)

	# Return new Transaction with updated entries
	return Transaction(
		transaction_id=transaction.transaction_id,
		date=transaction.date,
		description=transaction.description,
		entries=updated_entries,
	)
