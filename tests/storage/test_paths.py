"""Test storage path utilities."""

from datetime import date
from pathlib import Path

from small_business.storage.paths import (
	get_financial_year_dir,
	get_transaction_file_path,
	ensure_data_directory,
)


def test_get_financial_year_dir():
	"""Test financial year directory path generation."""
	base = Path("/data")

	# Test date in second half of year (after July)
	path = get_financial_year_dir(base, date(2025, 11, 15))
	assert path == Path("/data/2025-26")

	# Test date in first half of year (before July)
	path = get_financial_year_dir(base, date(2025, 6, 30))
	assert path == Path("/data/2024-25")

	# Test July (start of financial year)
	path = get_financial_year_dir(base, date(2025, 7, 1))
	assert path == Path("/data/2025-26")


def test_get_transaction_file_path():
	"""Test transaction file path generation."""
	base = Path("/data")

	path = get_transaction_file_path(base, date(2025, 11, 15))
	assert path == Path("/data/2025-26/transactions.jsonl")


def test_ensure_data_directory(tmp_path):
	"""Test creating data directory structure."""
	data_dir = tmp_path / "data"

	# Create structure
	ensure_data_directory(data_dir)

	# Check directories exist
	assert (data_dir / "transactions").exists()
	assert (data_dir / "receipts").exists()
	assert (data_dir / "config").exists()
	assert (data_dir / "clients").exists()
