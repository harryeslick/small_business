"""Template context rendering for documents."""

from decimal import Decimal

from small_business.models import Client, Invoice, Quote, Settings


def format_currency(amount: Decimal) -> str:
	"""Format currency with thousands separator.

	Args:
		amount: Decimal amount

	Returns:
		Formatted string (e.g., "1,234.56")
	"""
	return f"{amount:,.2f}"


def format_date(date_obj) -> str:
	"""Format date as DD/MM/YYYY.

	Args:
		date_obj: Date object

	Returns:
		Formatted date string
	"""
	return date_obj.strftime("%d/%m/%Y")


def render_quote_context(
	quote: Quote,
	client: Client,
	settings: Settings,
) -> dict:
	"""Render template context for a quote.

	Args:
		quote: Quote to render
		client: Client information
		settings: Application settings (for business details)

	Returns:
		Context dictionary for Jinja2 template rendering

	Template variables provided:
		- Quote: quote_id, date_created, date_valid_until, status, version
		- Client: client_name, client_email, client_phone, client_abn, client_address, client_contact_person
		- Business: business_name, business_abn, business_email, business_phone, business_address
		- Items: line_items[] (description, quantity, unit_price, subtotal, gst_inclusive)
		- Totals: subtotal, gst_amount, total
		- Notes: notes, terms_and_conditions
	"""
	# Format line items
	line_items = []
	for item in quote.line_items:
		line_items.append(
			{
				"description": item.description,
				"quantity": format_currency(item.quantity),
				"unit_price": format_currency(item.unit_price),
				"subtotal": format_currency(item.subtotal),
				"gst_inclusive": "Yes" if item.gst_inclusive else "No",
			}
		)

	return {
		# Quote details
		"quote_id": quote.quote_id,
		"date_created": format_date(quote.date_created),
		"date_valid_until": format_date(quote.date_valid_until),
		"status": quote.status.value,
		"version": quote.version,
		# Client details
		"client_name": client.name,
		"client_email": client.email or "",
		"client_phone": client.phone or "",
		"client_abn": client.abn or "",
		"client_address": client.formatted_address or "",
		"client_contact_person": client.contact_person or "",
		# Our business details (from Settings)
		"business_name": settings.business_name,
		"business_abn": settings.business_abn,
		"business_email": settings.business_email,
		"business_phone": settings.business_phone,
		"business_address": settings.business_address,
		# Line items and totals
		"line_items": line_items,
		"subtotal": format_currency(quote.subtotal),
		"gst_amount": format_currency(quote.gst_amount),
		"total": format_currency(quote.total),
		# Additional
		"notes": quote.notes,
		"terms_and_conditions": quote.terms_and_conditions,
	}


def render_invoice_context(
	invoice: Invoice,
	client: Client,
	settings: Settings,
) -> dict:
	"""Render template context for an invoice.

	Args:
		invoice: Invoice to render
		client: Client information
		settings: Application settings (for business details)

	Returns:
		Context dictionary for Jinja2 template rendering

	Template variables provided:
		- Invoice: invoice_id, date_issued, date_due, status, version
		- Client: client_name, client_email, client_phone, client_abn, client_address
		- Business: business_name, business_abn, business_email, business_phone, business_address
		- Items: line_items[] (description, quantity, unit_price, subtotal)
		- Totals: subtotal, gst_amount, total
		- Payment: payment_date, payment_amount, payment_reference (if paid)
		- Notes: notes
	"""
	# Format line items
	line_items = []
	for item in invoice.line_items:
		line_items.append(
			{
				"description": item.description,
				"quantity": format_currency(item.quantity),
				"unit_price": format_currency(item.unit_price),
				"subtotal": format_currency(item.subtotal),
			}
		)

	context = {
		# Invoice details
		"invoice_id": invoice.invoice_id,
		"date_issued": format_date(invoice.date_issued),
		"date_due": format_date(invoice.date_due),
		"status": invoice.status.value,
		"version": invoice.version,
		# Client details
		"client_name": client.name,
		"client_email": client.email or "",
		"client_phone": client.phone or "",
		"client_abn": client.abn or "",
		"client_address": client.formatted_address or "",
		# Our business details (from Settings)
		"business_name": settings.business_name,
		"business_abn": settings.business_abn,
		"business_email": settings.business_email,
		"business_phone": settings.business_phone,
		"business_address": settings.business_address,
		# Line items and totals
		"line_items": line_items,
		"subtotal": format_currency(invoice.subtotal),
		"gst_amount": format_currency(invoice.gst_amount),
		"total": format_currency(invoice.total),
		# Additional
		"notes": invoice.notes,
	}

	# Add payment information if paid
	if invoice.date_paid:
		context["payment_date"] = format_date(invoice.date_paid)
	if invoice.payment_amount:
		context["payment_amount"] = format_currency(invoice.payment_amount)
	if invoice.payment_reference:
		context["payment_reference"] = invoice.payment_reference

	return context
