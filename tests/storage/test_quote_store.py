"""Test quote storage with versioning."""

from datetime import date
from decimal import Decimal

import pytest

from small_business.models import LineItem, Quote, QuoteStatus
from small_business.storage.quote_store import load_quote, load_quotes, save_quote


def test_save_and_load_quote(tmp_path):
	"""Test saving and loading a quote."""
	data_dir = tmp_path / "data"

	quote = Quote(
		quote_id="Q-20251116-001",
		client_id="Test Client",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		status=QuoteStatus.DRAFT,
		line_items=[
			LineItem(
				description="Consulting services",
				quantity=Decimal("10.0"),
				unit_price=Decimal("150.00"),
				gst_inclusive=False,
			)
		],
		version=1,
	)

	# Save quote
	save_quote(quote, data_dir)

	# Verify file exists
	quote_file = data_dir / "quotes" / "2025-26" / "Q-20251116-001_v1.json"
	assert quote_file.exists()

	# Load quote with explicit version
	loaded = load_quote("Q-20251116-001", data_dir, version=1)
	assert loaded.quote_id == "Q-20251116-001"
	assert loaded.version == 1
	assert len(loaded.line_items) == 1


def test_load_quote_defaults_to_latest_version(tmp_path):
	"""Test that load_quote without version returns latest."""
	data_dir = tmp_path / "data"

	# Save version 1
	quote_v1 = Quote(
		quote_id="Q-20251116-001",
		client_id="Test Client",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		status=QuoteStatus.DRAFT,
		line_items=[
			LineItem(
				description="Service A",
				quantity=Decimal("10.0"),
				unit_price=Decimal("100.00"),
				gst_inclusive=False,
			)
		],
		version=1,
	)
	save_quote(quote_v1, data_dir)

	# Save version 2 (modified)
	quote_v2 = Quote(
		quote_id="Q-20251116-001",
		client_id="Test Client",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		status=QuoteStatus.SENT,
		line_items=[
			LineItem(
				description="Service A",
				quantity=Decimal("10.0"),
				unit_price=Decimal("120.00"),  # Price increased
				gst_inclusive=False,
			)
		],
		version=2,
	)
	save_quote(quote_v2, data_dir)

	# Load without version - should get latest (v2)
	latest = load_quote("Q-20251116-001", data_dir)
	assert latest.version == 2
	assert latest.line_items[0].unit_price == Decimal("120.00")
	assert latest.status == QuoteStatus.SENT

	# Can still load specific version
	v1 = load_quote("Q-20251116-001", data_dir, version=1)
	assert v1.version == 1
	assert v1.line_items[0].unit_price == Decimal("100.00")


def test_save_multiple_versions(tmp_path):
	"""Test saving multiple versions of a quote."""
	data_dir = tmp_path / "data"

	# Save version 1
	quote_v1 = Quote(
		quote_id="Q-20251116-001",
		client_id="Test Client",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		status=QuoteStatus.DRAFT,
		line_items=[
			LineItem(
				description="Service A",
				quantity=Decimal("10.0"),
				unit_price=Decimal("100.00"),
				gst_inclusive=False,
			)
		],
		version=1,
	)
	save_quote(quote_v1, data_dir)

	# Save version 2
	quote_v2 = Quote(
		quote_id="Q-20251116-001",
		client_id="Test Client",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		status=QuoteStatus.SENT,
		line_items=[
			LineItem(
				description="Service A",
				quantity=Decimal("10.0"),
				unit_price=Decimal("120.00"),  # Price increased
				gst_inclusive=False,
			)
		],
		version=2,
	)
	save_quote(quote_v2, data_dir)

	# Verify both files exist
	v1_file = data_dir / "quotes" / "2025-26" / "Q-20251116-001_v1.json"
	v2_file = data_dir / "quotes" / "2025-26" / "Q-20251116-001_v2.json"
	assert v1_file.exists()
	assert v2_file.exists()

	# Load both versions
	v1_loaded = load_quote("Q-20251116-001", data_dir, version=1)
	v2_loaded = load_quote("Q-20251116-001", data_dir, version=2)

	assert v1_loaded.line_items[0].unit_price == Decimal("100.00")
	assert v2_loaded.line_items[0].unit_price == Decimal("120.00")
	assert v2_loaded.status == QuoteStatus.SENT


def test_load_quotes_for_year(tmp_path):
	"""Test loading all quotes for a financial year (latest versions only)."""
	data_dir = tmp_path / "data"

	# Save quotes in different years
	quote_2025 = Quote(
		quote_id="Q-20251116-001",
		client_id="Client A",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)

	quote_2024 = Quote(
		quote_id="Q-20240601-001",
		client_id="Client B",
		date_created=date(2024, 6, 1),
		date_valid_until=date(2024, 7, 1),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)

	save_quote(quote_2025, data_dir)
	save_quote(quote_2024, data_dir)

	# Load 2025-26 quotes
	quotes_2025 = load_quotes(data_dir, date(2025, 11, 16))
	assert len(quotes_2025) == 1
	assert quotes_2025[0].quote_id == "Q-20251116-001"


def test_load_quotes_returns_latest_versions(tmp_path):
	"""Test that load_quotes returns only latest version of each quote."""
	data_dir = tmp_path / "data"

	# Save quote with multiple versions
	quote_v1 = Quote(
		quote_id="Q-20251116-001",
		client_id="Test Client",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
		version=1,
	)
	save_quote(quote_v1, data_dir)

	quote_v2 = Quote(
		quote_id="Q-20251116-001",
		client_id="Test Client",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("200"))],
		version=2,
	)
	save_quote(quote_v2, data_dir)

	# Load all quotes - should only get v2
	quotes = load_quotes(data_dir, date(2025, 11, 16))
	assert len(quotes) == 1
	assert quotes[0].version == 2
	assert quotes[0].line_items[0].unit_price == Decimal("200")


def test_load_quote_not_found(tmp_path):
	"""Test loading non-existent quote raises FileNotFoundError."""
	data_dir = tmp_path / "data"

	with pytest.raises(FileNotFoundError, match="Quote not found: Q-NONEXISTENT"):
		load_quote("Q-NONEXISTENT", data_dir)


def test_load_quotes_empty_directory(tmp_path):
	"""Test loading quotes from empty directory returns empty list."""
	data_dir = tmp_path / "data"

	quotes = load_quotes(data_dir, date(2025, 11, 16))
	assert quotes == []
