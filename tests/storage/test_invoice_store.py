"""Test invoice storage with versioning."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from small_business.models import Invoice, InvoiceStatus, LineItem
from small_business.storage.invoice_store import load_invoice, load_invoices, save_invoice


def test_save_and_load_invoice(tmp_path):
	"""Test saving and loading an invoice."""
	data_dir = tmp_path / "data"

	invoice = Invoice(
		invoice_id="INV-20251116-001",
		client_id="Test Client",
		date_issued=date(2025, 11, 16),
		date_due=date(2025, 12, 16),
		status=InvoiceStatus.DRAFT,
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

	# Save invoice
	save_invoice(invoice, data_dir)

	# Verify file exists
	invoice_file = data_dir / "invoices" / "2025-26" / "INV-20251116-001_v1.json"
	assert invoice_file.exists()

	# Load invoice with explicit version
	loaded = load_invoice("INV-20251116-001", data_dir, version=1)
	assert loaded.invoice_id == "INV-20251116-001"
	assert loaded.version == 1


def test_load_invoice_defaults_to_latest_version(tmp_path):
	"""Test that load_invoice without version returns latest."""
	data_dir = tmp_path / "data"

	# Save version 1
	invoice_v1 = Invoice(
		invoice_id="INV-20251116-001",
		client_id="Test Client",
		date_issued=date(2025, 11, 16),
		date_due=date(2025, 12, 16),
		status=InvoiceStatus.DRAFT,
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
	save_invoice(invoice_v1, data_dir)

	# Save version 2 (corrected)
	invoice_v2 = Invoice(
		invoice_id="INV-20251116-001",
		client_id="Test Client",
		date_issued=date(2025, 11, 16),
		date_due=date(2025, 12, 16),
		status=InvoiceStatus.SENT,
		line_items=[
			LineItem(
				description="Service A",
				quantity=Decimal("10.0"),
				unit_price=Decimal("120.00"),  # Corrected price
				gst_inclusive=False,
			)
		],
		version=2,
	)
	save_invoice(invoice_v2, data_dir)

	# Load without version - should get latest (v2)
	latest = load_invoice("INV-20251116-001", data_dir)
	assert latest.version == 2
	assert latest.line_items[0].unit_price == Decimal("120.00")
	assert latest.status == InvoiceStatus.SENT

	# Can still load specific version
	v1 = load_invoice("INV-20251116-001", data_dir, version=1)
	assert v1.version == 1
	assert v1.line_items[0].unit_price == Decimal("100.00")


def test_load_invoices_for_year(tmp_path):
	"""Test loading all invoices for a financial year (latest versions only)."""
	data_dir = tmp_path / "data"

	# Save invoices in different years
	invoice_2025 = Invoice(
		invoice_id="INV-20251116-001",
		client_id="Client A",
		date_issued=date(2025, 11, 16),
		date_due=date(2025, 12, 16),
		line_items=[
			LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))
		],
	)

	invoice_2024 = Invoice(
		invoice_id="INV-20240601-001",
		client_id="Client B",
		date_issued=date(2024, 6, 1),
		date_due=date(2024, 7, 1),
		line_items=[
			LineItem(description="Test", quantity=Decimal("1"), unit_price=Decimal("100"))
		],
	)

	save_invoice(invoice_2025, data_dir)
	save_invoice(invoice_2024, data_dir)

	# Load 2025-26 invoices
	invoices_2025 = load_invoices(data_dir, date(2025, 11, 16))
	assert len(invoices_2025) == 1
	assert invoices_2025[0].invoice_id == "INV-20251116-001"


def test_load_invoice_not_found(tmp_path):
	"""Test loading non-existent invoice raises FileNotFoundError."""
	data_dir = tmp_path / "data"

	with pytest.raises(FileNotFoundError, match="Invoice not found: INV-NONEXISTENT"):
		load_invoice("INV-NONEXISTENT", data_dir)


def test_load_invoices_empty_directory(tmp_path):
	"""Test loading invoices from empty directory returns empty list."""
	data_dir = tmp_path / "data"

	invoices = load_invoices(data_dir, date(2025, 11, 16))
	assert invoices == []
