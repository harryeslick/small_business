"""Formatting helpers for the TUI."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from small_business.models import get_financial_year


def format_currency(amount: Decimal | None, show_sign: bool = False) -> str:
	"""Format a Decimal as Australian currency string."""
	if amount is None:
		return "$0.00"
	if show_sign and amount > 0:
		return f"+${amount:,.2f}"
	if amount < 0:
		return f"-${abs(amount):,.2f}"
	return f"${amount:,.2f}"


def format_date(d: date | None, fmt: str = "%d %b %Y") -> str:
	"""Format a date for display (e.g., '20 Feb 2026')."""
	if d is None:
		return ""
	return d.strftime(fmt)


def format_date_short(d: date | None) -> str:
	"""Format a date as short display (e.g., 'Feb 20')."""
	if d is None:
		return ""
	return d.strftime("%b %d")


def current_financial_year() -> str:
	"""Get the current Australian financial year string (e.g., '2025-26')."""
	return get_financial_year(date.today())


def days_until(d: date) -> int:
	"""Return days from today until a given date (negative if past)."""
	return (d - date.today()).days
