"""Tests for Invoice model."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from small_business.models.enums import InvoiceStatus
from small_business.models.invoice import Invoice
from small_business.models.line_item import LineItem


def test_invoice_with_job():
	"""Test creating an invoice from a job."""
	invoice = Invoice(
		invoice_id="INV-20251115-001",
		job_id="J-20251115-001",
		client_id="Test Client",
		date_issued=date(2025, 11, 15),
		date_due=date(2025, 12, 15),
		line_items=[
			LineItem(description="Service", quantity=Decimal("1"), unit_price=Decimal("110.00"))
		],
	)
	assert invoice.invoice_id == "INV-20251115-001"
	assert invoice.job_id == "J-20251115-001"
	assert invoice.status == InvoiceStatus.DRAFT
	assert invoice.subtotal == Decimal("110.00")
	assert invoice.gst_amount == Decimal("10.00")
	assert invoice.total == Decimal("110.00")


def test_invoice_without_job():
	"""Test creating an invoice without a job."""
	invoice = Invoice(
		client_id="Test Client",
		date_issued=date(2025, 11, 15),
		date_due=date(2025, 12, 15),
		line_items=[
			LineItem(description="Service", quantity=Decimal("1"), unit_price=Decimal("100.00"))
		],
	)
	assert invoice.job_id is None


def test_invoice_with_payment():
	"""Test invoice with payment tracking."""
	invoice = Invoice(
		client_id="Test Client",
		date_issued=date(2025, 11, 15),
		date_due=date(2025, 12, 15),
		payment_date=date(2025, 11, 20),
		payment_amount=Decimal("110.00"),
		payment_reference="BANK-12345",
		line_items=[
			LineItem(description="Service", quantity=Decimal("1"), unit_price=Decimal("110.00"))
		],
	)
	assert invoice.payment_date == date(2025, 11, 20)
	assert invoice.payment_amount == Decimal("110.00")
	assert invoice.payment_reference == "BANK-12345"


def test_invoice_must_have_line_items():
	"""Test that invoice requires at least one line item."""
	with pytest.raises(ValidationError) as exc_info:
		Invoice(
			client_id="Test Client",
			date_issued=date(2025, 11, 15),
			date_due=date(2025, 12, 15),
			line_items=[],
		)
	assert "line_items" in str(exc_info.value)


def test_invoice_auto_generates_id():
	"""Test invoice ID auto-generation."""
	invoice = Invoice(
		client_id="Test Client",
		date_issued=date(2025, 11, 15),
		date_due=date(2025, 12, 15),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)
	assert invoice.invoice_id.startswith("INV-")


def test_invoice_financial_year():
	"""Test invoice financial year calculation."""
	invoice = Invoice(
		client_id="Test Client",
		date_issued=date(2025, 6, 30),
		date_due=date(2025, 7, 30),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)
	assert invoice.financial_year == "2024-25"
