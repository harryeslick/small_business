"""Tests for utility functions."""

from datetime import date

from small_business.models.utils import (
	generate_client_id,
	generate_invoice_id,
	generate_job_id,
	generate_quote_id,
	generate_transaction_id,
	get_financial_year,
)


def test_get_financial_year_july_to_december():
	"""Test financial year calculation for July-December dates."""
	assert get_financial_year(date(2025, 7, 1)) == "2025-26"
	assert get_financial_year(date(2025, 11, 15)) == "2025-26"
	assert get_financial_year(date(2025, 12, 31)) == "2025-26"


def test_get_financial_year_january_to_june():
	"""Test financial year calculation for January-June dates."""
	assert get_financial_year(date(2025, 1, 1)) == "2024-25"
	assert get_financial_year(date(2025, 6, 30)) == "2024-25"


def test_get_financial_year_boundary():
	"""Test financial year calculation at FY boundaries."""
	# Last day of FY 2024-25
	assert get_financial_year(date(2025, 6, 30)) == "2024-25"
	# First day of FY 2025-26
	assert get_financial_year(date(2025, 7, 1)) == "2025-26"


def test_generate_quote_id_format():
	"""Test quote ID has correct format Q-YYYYMMDD-NNN."""
	quote_id = generate_quote_id()
	assert quote_id.startswith("Q-")
	# Format: Q-YYYYMMDD-NNN (14 chars minimum)
	assert len(quote_id) >= 14


def test_generate_job_id_format():
	"""Test job ID has correct format J-YYYYMMDD-NNN."""
	job_id = generate_job_id()
	assert job_id.startswith("J-")
	assert len(job_id) >= 14


def test_generate_invoice_id_format():
	"""Test invoice ID has correct format INV-YYYYMMDD-NNN."""
	invoice_id = generate_invoice_id()
	assert invoice_id.startswith("INV-")
	assert len(invoice_id) >= 16


def test_generate_transaction_id_format():
	"""Test transaction ID has correct format TXN-YYYYMMDD-NNN."""
	transaction_id = generate_transaction_id()
	assert transaction_id.startswith("TXN-")
	assert len(transaction_id) >= 16


def test_generate_client_id_format():
	"""Test client ID has correct format C-YYYYMMDD-NNN."""
	client_id = generate_client_id()
	assert client_id.startswith("C-")
	assert len(client_id) >= 14


def test_generated_ids_are_unique():
	"""Test that generated IDs are unique."""
	# Generate multiple IDs and verify they're different
	quote_ids = [generate_quote_id() for _ in range(5)]
	assert len(set(quote_ids)) == 5, "All quote IDs should be unique"
