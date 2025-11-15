"""File path utilities for data storage."""

from datetime import date
from pathlib import Path

from small_business.models.utils import get_financial_year


def get_financial_year_dir(base_path: Path, txn_date: date) -> Path:
	"""Get directory path for a financial year.

	Args:
		base_path: Base data directory
		txn_date: Transaction date

	Returns:
		Path to financial year directory (e.g., /data/2025-26)
	"""
	fy = get_financial_year(txn_date)
	return base_path / fy


def get_transaction_file_path(base_path: Path, txn_date: date) -> Path:
	"""Get file path for transaction storage.

	Args:
		base_path: Base data directory
		txn_date: Transaction date

	Returns:
		Path to transaction file (e.g., /data/2025-26/transactions.jsonl)
	"""
	fy_dir = get_financial_year_dir(base_path, txn_date)
	return fy_dir / "transactions.jsonl"


def ensure_data_directory(base_path: Path) -> None:
	"""Create data directory structure if it doesn't exist.

	Creates:
		- transactions/
		- receipts/
		- config/
		- clients/
	"""
	base_path.mkdir(parents=True, exist_ok=True)
	(base_path / "transactions").mkdir(exist_ok=True)
	(base_path / "receipts").mkdir(exist_ok=True)
	(base_path / "config").mkdir(exist_ok=True)
	(base_path / "clients").mkdir(exist_ok=True)
