"""Test document generation with Jinja2 templates."""

from datetime import date
from decimal import Decimal

import pytest

from small_business.documents.generator import generate_invoice_document, generate_quote_document
from small_business.models import Client, Invoice, LineItem, Quote, Settings
from small_business.storage import save_client, save_settings


def test_generate_quote_document_raises_when_client_not_found(tmp_path):
	"""Test that generate_quote_document raises KeyError when client not found."""
	data_dir = tmp_path / "data"
	output_dir = tmp_path / "output"
	output_dir.mkdir()

	# Create quote without saving client
	quote = Quote(
		quote_id="Q-20251116-001",
		client_id="Nonexistent Client",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		line_items=[
			LineItem(description="Service", quantity=Decimal("1"), unit_price=Decimal("100"))
		],
	)

	output_path = output_dir / "quote.docx"

	# Should raise KeyError because client doesn't exist
	with pytest.raises(KeyError, match="Client not found"):
		generate_quote_document(quote, output_path, data_dir)


def test_generate_quote_document_raises_when_template_not_found(tmp_path):
	"""Test that generate_quote_document raises FileNotFoundError when template missing."""
	data_dir = tmp_path / "data"
	output_dir = tmp_path / "output"
	output_dir.mkdir()

	# Save client
	client = Client(
		client_id="Acme Corp",
		name="Acme Corp",
		email="contact@acme.com",
	)
	save_client(client, data_dir)

	# Save settings with non-existent template path
	settings = Settings(
		business_name="My Business",
		quote_template_path="nonexistent/template.docx",
	)
	save_settings(settings, data_dir)

	# Create quote
	quote = Quote(
		quote_id="Q-20251116-001",
		client_id="Acme Corp",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		line_items=[
			LineItem(description="Service", quantity=Decimal("1"), unit_price=Decimal("100"))
		],
	)

	output_path = output_dir / "quote.docx"

	# Should raise FileNotFoundError because template doesn't exist
	with pytest.raises(FileNotFoundError):
		generate_quote_document(quote, output_path, data_dir)


def test_generate_invoice_document_raises_when_client_not_found(tmp_path):
	"""Test that generate_invoice_document raises KeyError when client not found."""
	data_dir = tmp_path / "data"
	output_dir = tmp_path / "output"
	output_dir.mkdir()

	# Create invoice without saving client
	invoice = Invoice(
		invoice_id="INV-20251116-001",
		client_id="Nonexistent Client",
		date_issued=date(2025, 11, 16),
		date_due=date(2025, 12, 16),
		line_items=[
			LineItem(description="Service", quantity=Decimal("1"), unit_price=Decimal("100"))
		],
	)

	output_path = output_dir / "invoice.docx"

	# Should raise KeyError because client doesn't exist
	with pytest.raises(KeyError, match="Client not found"):
		generate_invoice_document(invoice, output_path, data_dir)


def test_generate_invoice_document_raises_when_template_not_found(tmp_path):
	"""Test that generate_invoice_document raises FileNotFoundError when template missing."""
	data_dir = tmp_path / "data"
	output_dir = tmp_path / "output"
	output_dir.mkdir()

	# Save client
	client = Client(
		client_id="Test Client",
		name="Test Client",
	)
	save_client(client, data_dir)

	# Save settings with non-existent template path
	settings = Settings(
		business_name="My Business",
		invoice_template_path="nonexistent/template.docx",
	)
	save_settings(settings, data_dir)

	# Create invoice
	invoice = Invoice(
		invoice_id="INV-20251116-001",
		client_id="Test Client",
		date_issued=date(2025, 11, 16),
		date_due=date(2025, 12, 16),
		line_items=[
			LineItem(description="Service", quantity=Decimal("1"), unit_price=Decimal("100"))
		],
	)

	output_path = output_dir / "invoice.docx"

	# Should raise FileNotFoundError because template doesn't exist
	with pytest.raises(FileNotFoundError):
		generate_invoice_document(invoice, output_path, data_dir)
