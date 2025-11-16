"""Transaction storage using JSONL format."""

import json
from datetime import date
from pathlib import Path

from small_business.models.transaction import Transaction
from small_business.storage.paths import get_financial_year_dir


def save_transaction(txn: Transaction, data_dir: Path) -> None:
	"""Save transaction to JSONL file.

	Args:
		txn: Transaction to save
		data_dir: Base data directory
	"""
	# Get financial year directory
	fy_dir = get_financial_year_dir(data_dir, txn.date)
	fy_dir.mkdir(parents=True, exist_ok=True)

	# Append to JSONL file
	txn_file = fy_dir / "transactions.jsonl"
	with open(txn_file, "a") as f:
		json_str = txn.model_dump_json()
		f.write(json_str + "\n")


def load_transactions(data_dir: Path, txn_date: date) -> list[Transaction]:
	"""Load all transactions for a financial year.

	Args:
		data_dir: Base data directory
		txn_date: Any date in the financial year to load

	Returns:
		List of transactions
	"""
	fy_dir = get_financial_year_dir(data_dir, txn_date)
	txn_file = fy_dir / "transactions.jsonl"

	if not txn_file.exists():
		return []

	transactions = []
	with open(txn_file) as f:
		for line in f:
			line = line.strip()
			if line:
				data = json.loads(line)
				txn = Transaction.model_validate(data)
				transactions.append(txn)

	return transactions


def transaction_exists(txn_id: str, data_dir: Path, txn_date: date) -> bool:
	"""Check if transaction ID already exists.

	Args:
		txn_id: Transaction ID to check
		data_dir: Base data directory
		txn_date: Date to determine financial year

	Returns:
		True if transaction exists
	"""
	transactions = load_transactions(data_dir, txn_date)
	return any(txn.transaction_id == txn_id for txn in transactions)


def update_transaction(txn: Transaction, data_dir: Path) -> None:
	"""Update an existing transaction in JSONL file.

	Rewrites the entire JSONL file with the updated transaction.

	Args:
		txn: Transaction with updates
		data_dir: Base data directory
	"""
	# Load all transactions
	transactions = load_transactions(data_dir, txn.date)

	# Find and replace the transaction
	found = False
	for i, existing_txn in enumerate(transactions):
		if existing_txn.transaction_id == txn.transaction_id:
			transactions[i] = txn
			found = True
			break

	if not found:
		msg = f"Transaction {txn.transaction_id} not found for update"
		raise ValueError(msg)

	# Rewrite the JSONL file
	fy_dir = get_financial_year_dir(data_dir, txn.date)
	txn_file = fy_dir / "transactions.jsonl"

	with open(txn_file, "w") as f:
		for t in transactions:
			json_str = t.model_dump_json()
			f.write(json_str + "\n")
