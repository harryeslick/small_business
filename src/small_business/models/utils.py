"""Utility functions for ID generation and financial year calculation."""

import uuid
from datetime import date


def get_financial_year(d: date) -> str:
	"""Calculate financial year (July-June) from a date.

	Args:
		d: Date to calculate financial year for

	Returns:
		Financial year string in format "YYYY-YY"

	Example:
		>>> get_financial_year(date(2025, 11, 15))
		'2025-26'
		>>> get_financial_year(date(2025, 6, 30))
		'2024-25'
	"""
	if d.month >= 7:
		return f"{d.year}-{str(d.year + 1)[-2:]}"
	else:
		return f"{d.year - 1}-{str(d.year)[-2:]}"


def generate_quote_id() -> str:
	"""Generate quote ID: Q-YYYYMMDD-NNN.

	Returns:
		Quote ID string
	"""
	today = date.today()
	date_str = today.strftime("%Y%m%d")
	# Use last 3 chars of UUID for uniqueness
	unique_suffix = str(uuid.uuid4())[:3].upper()
	return f"Q-{date_str}-{unique_suffix}"


def generate_job_id() -> str:
	"""Generate job ID: J-YYYYMMDD-NNN.

	Returns:
		Job ID string
	"""
	today = date.today()
	date_str = today.strftime("%Y%m%d")
	unique_suffix = str(uuid.uuid4())[:3].upper()
	return f"J-{date_str}-{unique_suffix}"


def generate_invoice_id() -> str:
	"""Generate invoice ID: INV-YYYYMMDD-NNN.

	Returns:
		Invoice ID string
	"""
	today = date.today()
	date_str = today.strftime("%Y%m%d")
	unique_suffix = str(uuid.uuid4())[:3].upper()
	return f"INV-{date_str}-{unique_suffix}"


def generate_transaction_id() -> str:
	"""Generate transaction ID: TXN-YYYYMMDD-NNN.

	Returns:
		Transaction ID string
	"""
	today = date.today()
	date_str = today.strftime("%Y%m%d")
	unique_suffix = str(uuid.uuid4())[:3].upper()
	return f"TXN-{date_str}-{unique_suffix}"


def generate_client_id() -> str:
	"""Generate client ID: C-YYYYMMDD-NNN.

	Returns:
		Client ID string
	"""
	today = date.today()
	date_str = today.strftime("%Y%m%d")
	unique_suffix = str(uuid.uuid4())[:3].upper()
	return f"C-{date_str}-{unique_suffix}"
