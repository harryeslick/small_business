"""Invoice storage using JSON format with versioning support."""

import json
from datetime import date
from pathlib import Path

from small_business.models import Invoice
from small_business.storage.paths import get_financial_year_dir


def save_invoice(invoice: Invoice, data_dir: Path) -> None:
	"""Save invoice to JSON file in financial year directory.

	Saves to: data/invoices/YYYY-YY/INVOICE_ID_vVERSION.json

	Args:
		invoice: Invoice to save
		data_dir: Base data directory
	"""
	# Get financial year directory
	fy_dir = get_financial_year_dir(data_dir, invoice.date_issued)
	invoices_dir = data_dir / "invoices" / fy_dir.name
	invoices_dir.mkdir(parents=True, exist_ok=True)

	# Save invoice file
	invoice_file = invoices_dir / f"{invoice.invoice_id}_v{invoice.version}.json"
	with open(invoice_file, "w") as f:
		json_str = invoice.model_dump_json(indent=2)
		f.write(json_str)


def load_invoice(invoice_id: str, data_dir: Path, version: int | None = None) -> Invoice:
	"""Load an invoice, defaulting to latest version if not specified.

	Args:
		invoice_id: Invoice ID
		data_dir: Base data directory
		version: Specific version to load, or None for latest

	Returns:
		Invoice instance

	Raises:
		FileNotFoundError: If invoice not found
	"""
	if version is None:
		return _load_latest_invoice(invoice_id, data_dir)
	else:
		return _load_invoice_version(invoice_id, version, data_dir)


def _load_latest_invoice(invoice_id: str, data_dir: Path) -> Invoice:
	"""Load the latest version of an invoice.

	Args:
		invoice_id: Invoice ID
		data_dir: Base data directory

	Returns:
		Latest version of the invoice

	Raises:
		FileNotFoundError: If invoice not found
	"""
	invoices_base = data_dir / "invoices"
	if not invoices_base.exists():
		raise FileNotFoundError(f"Invoice not found: {invoice_id}")

	# Find all versions of this invoice
	versions = []
	for fy_dir in invoices_base.iterdir():
		if fy_dir.is_dir():
			for invoice_file in fy_dir.glob(f"{invoice_id}_v*.json"):
				# Extract version number from filename
				version_str = invoice_file.stem.split("_v")[1]
				versions.append((int(version_str), invoice_file))

	if not versions:
		raise FileNotFoundError(f"Invoice not found: {invoice_id}")

	# Load highest version
	_, latest_file = max(versions, key=lambda x: x[0])
	with open(latest_file) as f:
		data = json.load(f)
		return Invoice.model_validate(data)


def _load_invoice_version(invoice_id: str, version: int, data_dir: Path) -> Invoice:
	"""Load a specific version of an invoice.

	Args:
		invoice_id: Invoice ID
		version: Version number
		data_dir: Base data directory

	Returns:
		Specific version of the invoice

	Raises:
		FileNotFoundError: If invoice version not found
	"""
	invoices_base = data_dir / "invoices"
	if not invoices_base.exists():
		raise FileNotFoundError(f"Invoice not found: {invoice_id} v{version}")

	for fy_dir in invoices_base.iterdir():
		if fy_dir.is_dir():
			invoice_file = fy_dir / f"{invoice_id}_v{version}.json"
			if invoice_file.exists():
				with open(invoice_file) as f:
					data = json.load(f)
					return Invoice.model_validate(data)

	raise FileNotFoundError(f"Invoice not found: {invoice_id} v{version}")


def load_invoices(data_dir: Path, txn_date: date) -> list[Invoice]:
	"""Load all invoices for a financial year (latest versions only).

	Args:
		data_dir: Base data directory
		txn_date: Date to determine financial year

	Returns:
		List of invoices (latest version of each)
	"""
	fy_dir = get_financial_year_dir(data_dir, txn_date)
	invoices_dir = data_dir / "invoices" / fy_dir.name

	if not invoices_dir.exists():
		return []

	# Load all invoice files
	invoice_versions: dict[str, list[Invoice]] = {}

	for invoice_file in invoices_dir.glob("*.json"):
		with open(invoice_file) as f:
			data = json.load(f)
			invoice = Invoice.model_validate(data)

			# Group by invoice_id
			if invoice.invoice_id not in invoice_versions:
				invoice_versions[invoice.invoice_id] = []
			invoice_versions[invoice.invoice_id].append(invoice)

	# Return latest version of each invoice
	invoices = []
	for invoice_id, versions in invoice_versions.items():
		latest = max(versions, key=lambda i: i.version)
		invoices.append(latest)

	return invoices
