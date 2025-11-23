"""Quote storage using JSON format with versioning support."""

import json
from datetime import date
from pathlib import Path

from small_business.models import Quote
from small_business.storage.paths import get_financial_year_dir


def save_quote(quote: Quote, data_dir: Path) -> None:
	"""Save quote to JSON file in financial year directory.

	Saves to: data/quotes/YYYY-YY/QUOTE_ID_vVERSION.json

	Args:
		quote: Quote to save
		data_dir: Base data directory
	"""
	# Get financial year directory
	fy_dir = get_financial_year_dir(data_dir, quote.date_created)
	quotes_dir = data_dir / "quotes" / fy_dir.name
	quotes_dir.mkdir(parents=True, exist_ok=True)

	# Save quote file
	quote_file = quotes_dir / f"{quote.quote_id}_v{quote.version}.json"
	with open(quote_file, "w") as f:
		json_str = quote.model_dump_json(indent=2)
		f.write(json_str)


def load_quote(quote_id: str, data_dir: Path, version: int | None = None) -> Quote:
	"""Load a quote, defaulting to latest version if not specified.

	Args:
		quote_id: Quote ID
		data_dir: Base data directory
		version: Specific version to load, or None for latest

	Returns:
		Quote instance

	Raises:
		FileNotFoundError: If quote not found
	"""
	if version is None:
		return _load_latest_quote(quote_id, data_dir)
	else:
		return _load_quote_version(quote_id, version, data_dir)


def _load_latest_quote(quote_id: str, data_dir: Path) -> Quote:
	"""Load the latest version of a quote.

	Args:
		quote_id: Quote ID
		data_dir: Base data directory

	Returns:
		Latest version of the quote

	Raises:
		FileNotFoundError: If quote not found
	"""
	quotes_base = data_dir / "quotes"
	if not quotes_base.exists():
		raise FileNotFoundError(f"Quote not found: {quote_id}")

	# Find all versions of this quote
	versions = []
	for fy_dir in quotes_base.iterdir():
		if fy_dir.is_dir():
			for quote_file in fy_dir.glob(f"{quote_id}_v*.json"):
				# Extract version number from filename
				version_str = quote_file.stem.split("_v")[1]
				versions.append((int(version_str), quote_file))

	if not versions:
		raise FileNotFoundError(f"Quote not found: {quote_id}")

	# Load highest version
	_, latest_file = max(versions, key=lambda x: x[0])
	with open(latest_file) as f:
		data = json.load(f)
		return Quote.model_validate(data)


def _load_quote_version(quote_id: str, version: int, data_dir: Path) -> Quote:
	"""Load a specific version of a quote.

	Args:
		quote_id: Quote ID
		version: Version number
		data_dir: Base data directory

	Returns:
		Specific version of the quote

	Raises:
		FileNotFoundError: If quote version not found
	"""
	quotes_base = data_dir / "quotes"
	if not quotes_base.exists():
		raise FileNotFoundError(f"Quote not found: {quote_id} v{version}")

	for fy_dir in quotes_base.iterdir():
		if fy_dir.is_dir():
			quote_file = fy_dir / f"{quote_id}_v{version}.json"
			if quote_file.exists():
				with open(quote_file) as f:
					data = json.load(f)
					return Quote.model_validate(data)

	raise FileNotFoundError(f"Quote not found: {quote_id} v{version}")


def load_quotes(data_dir: Path, txn_date: date) -> list[Quote]:
	"""Load all quotes for a financial year (latest versions only).

	Args:
		data_dir: Base data directory
		txn_date: Date to determine financial year

	Returns:
		List of quotes (latest version of each)
	"""
	fy_dir = get_financial_year_dir(data_dir, txn_date)
	quotes_dir = data_dir / "quotes" / fy_dir.name

	if not quotes_dir.exists():
		return []

	# Load all quote files
	quote_versions: dict[str, list[Quote]] = {}

	for quote_file in quotes_dir.glob("*.json"):
		with open(quote_file) as f:
			data = json.load(f)
			quote = Quote.model_validate(data)

			# Group by quote_id
			if quote.quote_id not in quote_versions:
				quote_versions[quote.quote_id] = []
			quote_versions[quote.quote_id].append(quote)

	# Return latest version of each quote
	quotes = []
	for quote_id, versions in quote_versions.items():
		latest = max(versions, key=lambda q: q.version)
		quotes.append(latest)

	return quotes
