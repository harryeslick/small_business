"""Document generation using Jinja2 templates."""

from pathlib import Path

from docxtpl import DocxTemplate

from small_business.models import Invoice, Quote
from small_business.storage import load_client, load_settings

from .templates import render_invoice_context, render_quote_context


def generate_quote_document(
	quote: Quote,
	output_path: Path,
	data_dir: Path,
) -> None:
	"""Generate quote document using configured template.

	Auto-loads client and settings from data_dir.

	Args:
		quote: Quote to generate document for
		output_path: Path to save the generated document
		data_dir: Root data directory (for loading client and settings)

	Raises:
		KeyError: If client not found
		FileNotFoundError: If template file not found

	Notes:
		Template path is loaded from Settings.quote_template_path.
		Client is looked up by quote.client_id.
	"""
	# Auto-load dependencies
	settings = load_settings(data_dir)
	client = load_client(quote.client_id, data_dir)

	# Resolve template path (relative to data_dir if not absolute)
	template_path = Path(settings.quote_template_path)
	if not template_path.is_absolute():
		template_path = data_dir / template_path

	# Render context and generate document
	context = render_quote_context(quote, client, settings)

	doc = DocxTemplate(template_path)
	doc.render(context)
	doc.save(output_path)


def generate_invoice_document(
	invoice: Invoice,
	output_path: Path,
	data_dir: Path,
) -> None:
	"""Generate invoice document using configured template.

	Auto-loads client and settings from data_dir.

	Args:
		invoice: Invoice to generate document for
		output_path: Path to save the generated document
		data_dir: Root data directory (for loading client and settings)

	Raises:
		KeyError: If client not found
		FileNotFoundError: If template file not found

	Notes:
		Template path is loaded from Settings.invoice_template_path.
		Client is looked up by invoice.client_id.
	"""
	# Auto-load dependencies
	settings = load_settings(data_dir)
	client = load_client(invoice.client_id, data_dir)

	# Resolve template path (relative to data_dir if not absolute)
	template_path = Path(settings.invoice_template_path)
	if not template_path.is_absolute():
		template_path = data_dir / template_path

	# Render context and generate document
	context = render_invoice_context(invoice, client, settings)

	doc = DocxTemplate(template_path)
	doc.render(context)
	doc.save(output_path)
