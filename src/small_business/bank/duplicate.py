"""Duplicate transaction detection."""

import hashlib

from small_business.bank.models import BankTransaction, ImportedBankStatement


def generate_transaction_hash(txn: BankTransaction) -> str:
	"""Generate hash for duplicate detection.

	Hash is based on: date, description, amount (ignores balance).

	Args:
		txn: Bank transaction

	Returns:
		SHA256 hash string
	"""
	# Create hash from date, description, and amount
	hash_input = f"{txn.date.isoformat()}|{txn.description}|{txn.amount}"
	return hashlib.sha256(hash_input.encode()).hexdigest()


def is_duplicate(
	txn: BankTransaction,
	existing_statements: list[ImportedBankStatement],
) -> bool:
	"""Check if transaction is a duplicate.

	Args:
		txn: Transaction to check
		existing_statements: Previously imported statements

	Returns:
		True if transaction already exists
	"""
	txn_hash = generate_transaction_hash(txn)

	for stmt in existing_statements:
		for existing_txn in stmt.transactions:
			if generate_transaction_hash(existing_txn) == txn_hash:
				return True

	return False
