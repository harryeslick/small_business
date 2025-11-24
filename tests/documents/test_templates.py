"""Test document template context rendering."""

from datetime import date
from decimal import Decimal

from small_business.documents.templates import render_invoice_context, render_quote_context
from small_business.models import Client, Invoice, LineItem, Quote, Settings


def test_render_quote_context():
	"""Test rendering quote context for Jinja2 templates."""
	client = Client(
		client_id="Acme Corp",
		name="Acme Corp",
		email="contact@acme.com",
		phone="0400 000 000",
		abn="12 345 678 901",
		street_address="123 Business St",
		suburb="Sydney",
		state="NSW",
		postcode="2000",
		formatted_address="123 Business St, Sydney NSW 2000",
	)

	quote = Quote(
		quote_id="Q-20251116-001",
		client_id="Acme Corp",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		line_items=[
			LineItem(
				description="Consulting services",
				quantity=Decimal("10.0"),
				unit_price=Decimal("150.00"),
				gst_inclusive=False,
			),
			LineItem(
				description="Training workshop",
				quantity=Decimal("1.0"),
				unit_price=Decimal("500.00"),
				gst_inclusive=False,
			),
		],
	)

	settings = Settings(
		business_name="My Business",
		business_abn="98 765 432 109",
		business_email="info@mybusiness.com",
		business_phone="0400 123 456",
		business_address="123 Business St, Sydney NSW 2000",
	)

	context = render_quote_context(quote, client, settings)

	assert context["quote_id"] == "Q-20251116-001"
	assert context["client_name"] == "Acme Corp"
	assert context["client_email"] == "contact@acme.com"
	assert context["client_address"] == "123 Business St, Sydney NSW 2000"
	assert context["business_name"] == "My Business"
	assert context["business_abn"] == "98 765 432 109"
	assert len(context["line_items"]) == 2
	assert context["subtotal"] == "2,000.00"
	assert context["gst_amount"] == "200.00"
	assert context["total"] == "2,200.00"
	assert context["date_created"] == "16/11/2025"
	assert context["date_valid_until"] == "16/12/2025"


def test_render_quote_context_with_minimal_client():
	"""Test rendering quote context with minimal client info."""
	client = Client(
		client_id="Basic Client",
		name="Basic Client",
	)

	quote = Quote(
		quote_id="Q-20251116-002",
		client_id="Basic Client",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		line_items=[
			LineItem(description="Service", quantity=Decimal("1"), unit_price=Decimal("100.00"))
		],
	)

	settings = Settings(business_name="Test Business")

	context = render_quote_context(quote, client, settings)

	assert context["client_name"] == "Basic Client"
	assert context["client_email"] == ""
	assert context["client_phone"] == ""
	assert context["client_address"] == ""
	assert context["business_name"] == "Test Business"


def test_render_invoice_context():
	"""Test rendering invoice context for Jinja2 templates."""
	client = Client(
		client_id="Acme Corp",
		name="Acme Corp",
		email="contact@acme.com",
		formatted_address="123 Business St, Sydney NSW 2000",
	)

	invoice = Invoice(
		invoice_id="INV-20251116-001",
		client_id="Acme Corp",
		date_issued=date(2025, 11, 16),
		date_due=date(2025, 12, 16),
		line_items=[
			LineItem(
				description="Consulting services",
				quantity=Decimal("10.0"),
				unit_price=Decimal("150.00"),
				gst_inclusive=False,
			)
		],
	)

	settings = Settings(business_name="My Business")

	context = render_invoice_context(invoice, client, settings)

	assert context["invoice_id"] == "INV-20251116-001"
	assert context["client_name"] == "Acme Corp"
	assert context["business_name"] == "My Business"
	assert context["date_issued"] == "16/11/2025"
	assert context["date_due"] == "16/12/2025"
	assert len(context["line_items"]) == 1
	assert context["subtotal"] == "1,500.00"
	assert context["gst_amount"] == "150.00"
	assert context["total"] == "1,650.00"


def test_render_invoice_context_with_payment():
	"""Test rendering invoice context with payment information."""
	client = Client(
		client_id="Paid Client",
		name="Paid Client",
	)

	invoice = Invoice(
		invoice_id="INV-20251116-002",
		client_id="Paid Client",
		date_issued=date(2025, 11, 16),
		date_due=date(2025, 12, 16),
		line_items=[
			LineItem(description="Service", quantity=Decimal("1"), unit_price=Decimal("100.00"))
		],
		date_paid=date(2025, 11, 20),
		payment_amount=Decimal("110.00"),
		payment_reference="PAY-001",
	)

	settings = Settings()

	context = render_invoice_context(invoice, client, settings)

	assert "payment_date" in context
	assert context["payment_date"] == "20/11/2025"
	assert context["payment_amount"] == "110.00"
	assert context["payment_reference"] == "PAY-001"


def test_line_item_formatting():
	"""Test that line items are properly formatted in context."""
	client = Client(client_id="Test", name="Test")
	quote = Quote(
		quote_id="Q-001",
		client_id="Test",
		date_created=date(2025, 11, 16),
		date_valid_until=date(2025, 12, 16),
		line_items=[
			LineItem(
				description="Item with GST included",
				quantity=Decimal("5.5"),
				unit_price=Decimal("123.45"),
				gst_inclusive=True,
			),
		],
	)
	settings = Settings()

	context = render_quote_context(quote, client, settings)

	line_item = context["line_items"][0]
	assert line_item["description"] == "Item with GST included"
	assert line_item["quantity"] == "5.50"
	assert line_item["unit_price"] == "123.45"
	assert line_item["gst_inclusive"] == "Yes"
