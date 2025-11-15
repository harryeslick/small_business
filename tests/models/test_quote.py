"""Tests for Quote model."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from small_business.models.line_item import LineItem
from small_business.models.quote import Quote


def test_quote_with_single_line_item():
	"""Test creating a quote with one line item."""
	quote = Quote(
		quote_id="Q-20251115-001",
		client_id="C-20251115-001",
		date_created=date(2025, 11, 15),
		date_valid_until=date(2025, 12, 15),
		line_items=[
			LineItem(description="Consulting", quantity=Decimal("1"), unit_price=Decimal("110.00"))
		],
	)
	assert quote.subtotal == Decimal("110.00")
	assert quote.gst_amount == Decimal("10.00")
	assert quote.total == Decimal("110.00")
	assert quote.financial_year == "2025-26"


def test_quote_with_multiple_line_items():
	"""Test quote with multiple line items."""
	quote = Quote(
		quote_id="Q-20251115-002",
		client_id="C-20251115-001",
		date_created=date(2025, 11, 15),
		date_valid_until=date(2025, 12, 15),
		line_items=[
			LineItem(description="Item 1", quantity=Decimal("1"), unit_price=Decimal("110.00")),
			LineItem(description="Item 2", quantity=Decimal("2"), unit_price=Decimal("55.00")),
		],
	)
	# Subtotal = 110 + 110 = 220
	assert quote.subtotal == Decimal("220.00")
	# GST = 10 + 10 = 20
	assert quote.gst_amount == Decimal("20.00")
	assert quote.total == Decimal("220.00")


def test_quote_must_have_line_items():
	"""Test that quote requires at least one line item."""
	with pytest.raises(ValidationError) as exc_info:
		Quote(
			quote_id="Q-20251115-003",
			client_id="C-20251115-001",
			date_created=date(2025, 11, 15),
			date_valid_until=date(2025, 12, 15),
			line_items=[],
		)
	assert "line_items" in str(exc_info.value)


def test_quote_auto_generates_id():
	"""Test quote ID auto-generation."""
	quote = Quote(
		client_id="C-20251115-001",
		date_created=date(2025, 11, 15),
		date_valid_until=date(2025, 12, 15),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)
	assert quote.quote_id.startswith("Q-")


def test_quote_financial_year_before_july():
	"""Test financial year calculation for date before July."""
	quote = Quote(
		quote_id="Q-20250630-001",
		client_id="C-20251115-001",
		date_created=date(2025, 6, 30),
		date_valid_until=date(2025, 7, 30),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)
	assert quote.financial_year == "2024-25"
