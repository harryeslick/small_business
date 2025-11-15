"""Tests for LineItem model."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from small_business.models.line_item import LineItem


def test_line_item_gst_inclusive():
	"""Test line item with GST-inclusive pricing."""
	item = LineItem(
		description="Consulting services",
		quantity=Decimal("2"),
		unit_price=Decimal("110.00"),
		gst_inclusive=True,
	)
	assert item.description == "Consulting services"
	assert item.quantity == Decimal("2")
	assert item.unit_price == Decimal("110.00")
	assert item.gst_inclusive is True
	# Subtotal = 2 × 110 = 220
	assert item.subtotal == Decimal("220.00")
	# GST = 220 / 11 = 20
	assert item.gst_amount == Decimal("20.00")
	# Total = subtotal (already includes GST)
	assert item.total == Decimal("220.00")


def test_line_item_gst_exclusive():
	"""Test line item with GST-exclusive pricing."""
	item = LineItem(
		description="Equipment",
		quantity=Decimal("1"),
		unit_price=Decimal("100.00"),
		gst_inclusive=False,
	)
	# Subtotal = 1 × 100 = 100
	assert item.subtotal == Decimal("100.00")
	# GST = 100 × 0.10 = 10
	assert item.gst_amount == Decimal("10.00")
	# Total = 100 + 10 = 110
	assert item.total == Decimal("110.00")


def test_line_item_fractional_quantity():
	"""Test line item with fractional quantity."""
	item = LineItem(
		description="Hours of work",
		quantity=Decimal("2.5"),
		unit_price=Decimal("110.00"),
		gst_inclusive=True,
	)
	# Subtotal = 2.5 × 110 = 275
	assert item.subtotal == Decimal("275.00")
	# GST = 275 / 11 = 25
	assert item.gst_amount == Decimal("25.00")


def test_line_item_zero_price():
	"""Test line item with zero price (free item)."""
	item = LineItem(
		description="Free consultation",
		quantity=Decimal("1"),
		unit_price=Decimal("0"),
		gst_inclusive=False,
	)
	assert item.subtotal == Decimal("0.00")
	assert item.gst_amount == Decimal("0.00")
	assert item.total == Decimal("0.00")


def test_line_item_quantity_must_be_positive():
	"""Test that quantity must be greater than zero."""
	with pytest.raises(ValidationError) as exc_info:
		LineItem(
			description="Test",
			quantity=Decimal("0"),
			unit_price=Decimal("100"),
			gst_inclusive=True,
		)
	assert "quantity" in str(exc_info.value)


def test_line_item_price_cannot_be_negative():
	"""Test that unit price cannot be negative."""
	with pytest.raises(ValidationError) as exc_info:
		LineItem(
			description="Test",
			quantity=Decimal("1"),
			unit_price=Decimal("-100"),
			gst_inclusive=True,
		)
	assert "unit_price" in str(exc_info.value)


def test_line_item_description_required():
	"""Test that description is required."""
	with pytest.raises(ValidationError) as exc_info:
		LineItem(quantity=Decimal("1"), unit_price=Decimal("100"), gst_inclusive=True)
	assert "description" in str(exc_info.value)


def test_line_item_description_cannot_be_empty():
	"""Test that description cannot be empty string."""
	with pytest.raises(ValidationError) as exc_info:
		LineItem(
			description="", quantity=Decimal("1"), unit_price=Decimal("100"), gst_inclusive=True
		)
	assert "description" in str(exc_info.value)


def test_line_item_serialization_includes_computed_fields():
	"""Test that computed fields are included in serialization."""
	item = LineItem(
		description="Test item",
		quantity=Decimal("1"),
		unit_price=Decimal("110.00"),
		gst_inclusive=True,
	)
	data = item.model_dump()
	assert "subtotal" in data
	assert "gst_amount" in data
	assert "total" in data
	assert data["subtotal"] == Decimal("110.00")
	assert data["gst_amount"] == Decimal("10.00")
	assert data["total"] == Decimal("110.00")


def test_line_item_gst_calculation_rounding():
	"""Test GST calculation rounding to 2 decimal places."""
	item = LineItem(
		description="Test",
		quantity=Decimal("3"),
		unit_price=Decimal("33.33"),
		gst_inclusive=True,
	)
	# Subtotal = 3 × 33.33 = 99.99
	assert item.subtotal == Decimal("99.99")
	# GST = 99.99 / 11 = 9.09 (rounded)
	assert item.gst_amount == Decimal("9.09")
