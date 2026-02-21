"""Tests for Invoice model."""

from datetime import date, timedelta
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
		date_due=date(2025, 12, 15),
		line_items=[
			LineItem(description="Service", quantity=Decimal("1"), unit_price=Decimal("100.00"))
		],
	)
	assert invoice.job_id is None
	assert invoice.status == InvoiceStatus.DRAFT


def test_invoice_with_payment():
	"""Test invoice with payment tracking."""
	invoice = Invoice(
		client_id="Test Client",
		date_issued=date(2025, 11, 15),
		date_due=date(2025, 12, 15),
		date_paid=date(2025, 11, 20),
		payment_amount=Decimal("110.00"),
		payment_reference="BANK-12345",
		line_items=[
			LineItem(description="Service", quantity=Decimal("1"), unit_price=Decimal("110.00"))
		],
	)
	assert invoice.date_paid == date(2025, 11, 20)
	assert invoice.payment_amount == Decimal("110.00")
	assert invoice.payment_reference == "BANK-12345"
	assert invoice.status == InvoiceStatus.PAID


def test_invoice_must_have_line_items():
	"""Test that invoice requires at least one line item."""
	with pytest.raises(ValidationError) as exc_info:
		Invoice(
			client_id="Test Client",
			date_due=date(2025, 12, 15),
			line_items=[],
		)
	assert "line_items" in str(exc_info.value)


def test_invoice_auto_generates_id():
	"""Test invoice ID auto-generation."""
	invoice = Invoice(
		client_id="Test Client",
		date_due=date(2025, 12, 15),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)
	assert invoice.invoice_id.startswith("INV-")


def test_invoice_financial_year():
	"""Test invoice financial year calculation."""
	invoice = Invoice(
		client_id="Test Client",
		date_created=date(2025, 6, 30),
		date_due=date(2025, 7, 30),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)
	assert invoice.financial_year == "2024-25"


def test_invoice_status_draft():
	"""Test invoice status is DRAFT when not issued."""
	invoice = Invoice(
		client_id="Test Client",
		date_due=date(2025, 12, 15),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)
	assert invoice.status == InvoiceStatus.DRAFT
	assert invoice.date_issued is None


def test_invoice_status_sent():
	"""Test invoice status is SENT when issued but not paid."""
	today = date.today()
	invoice = Invoice(
		client_id="Test Client",
		date_issued=today - timedelta(days=1),
		date_due=today + timedelta(days=30),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)
	assert invoice.status == InvoiceStatus.SENT
	assert invoice.date_paid is None


def test_invoice_status_paid():
	"""Test invoice status is PAID when payment recorded."""
	invoice = Invoice(
		client_id="Test Client",
		date_issued=date(2025, 11, 15),
		date_due=date(2025, 12, 15),
		date_paid=date(2025, 11, 20),
		payment_amount=Decimal("100.00"),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)
	assert invoice.status == InvoiceStatus.PAID


def test_invoice_status_cancelled():
	"""Test invoice status is CANCELLED when cancelled."""
	invoice = Invoice(
		client_id="Test Client",
		date_issued=date(2025, 11, 15),
		date_due=date(2025, 12, 15),
		date_cancelled=date(2025, 11, 20),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)
	assert invoice.status == InvoiceStatus.CANCELLED


def test_invoice_status_overdue():
	"""Test invoice status is OVERDUE when past due date."""
	invoice = Invoice(
		client_id="Test Client",
		date_issued=date(2024, 11, 15),
		date_due=date(2024, 12, 15),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)
	assert invoice.status == InvoiceStatus.OVERDUE


def test_invoice_days_outstanding():
	"""Test invoice days_outstanding calculation."""
	invoice = Invoice(
		client_id="Test Client",
		date_issued=date(2025, 11, 1),
		date_due=date(2025, 12, 1),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)
	# days_outstanding should be calculated from date_issued to today
	assert invoice.days_outstanding is not None
	assert invoice.days_outstanding >= 0

	# Paid invoice should have None for days_outstanding
	paid_invoice = Invoice(
		client_id="Test Client",
		date_issued=date(2025, 11, 1),
		date_due=date(2025, 12, 1),
		date_paid=date(2025, 11, 15),
		line_items=[LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))],
	)
	assert paid_invoice.days_outstanding is None
