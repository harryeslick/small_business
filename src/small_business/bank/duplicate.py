"""Duplicate transaction detection."""

from small_business.bank.models import BankTransaction, ImportedBankStatement


def is_duplicate(
	txn: BankTransaction,
	existing_statements: list[ImportedBankStatement],
) -> bool:
	"""Check if transaction is a duplicate.

	Uses direct field comparison (date, description, amount) instead of hashing.
	This provides transparency, interoperability, and debuggability.

	NOTE: The account context is handled by the caller - existing_statements should
	only contain transactions from the same account being imported.

	Args:
		txn: Transaction to check
		existing_statements: Previously imported statements (filtered to same account by caller)

	Returns:
		True if transaction already exists
	"""
	for stmt in existing_statements:
		for existing_txn in stmt.transactions:
			# Direct comparison of the three key fields
			# (account filtering happens in import_workflow before calling this function)
			if (
				existing_txn.date == txn.date
				and existing_txn.description == txn.description
				and existing_txn.amount == txn.amount
			):
				return True

	return False
