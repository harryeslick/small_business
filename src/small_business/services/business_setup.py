"""Service functions for setting up a new business directory."""

import shutil
from importlib.resources import files
from pathlib import Path

from small_business.core.models.config import Settings


def init_business(business_settings: Settings, path: Path | None = None) -> Path:
	"""Initialize a new business in a subdirectory named after the business.

	Creates the following structure:
	- [path]/[business_name_safe]/
	  - clients/
	  - quotes/
	  - ...

	Args:
		business_settings: Settings object with business configuration
		path: Base path where business directory will be created (default: current directory)

	Returns:
		Path to the created business directory

	Raises:
		FileExistsError: If business directory already exists and contains data
	"""
	# Use current directory if no path provided
	if path is None:
		path = Path.cwd()

	# Create business directory from business name (sanitized)
	business_name_safe = business_settings.business_name.lower().replace(" ", "_")
	business_dir = path / business_name_safe

	# Check if directory exists and has content
	if business_dir.exists():
		# Check if it has any subdirectories - indicates it's already initialized
		if any(business_dir.iterdir()):
			raise FileExistsError(
				f"Business directory already exists and contains data: {business_dir}"
			)

	# Create directory structure
	init_business_in_place(business_settings, business_dir)

	return business_dir


def init_business_in_place(settings: Settings, path: Path) -> Path:
	"""Initialize a business directly in the given directory (no subdirectory).

	Creates the standard business directory structure inside `path`.
	"""
	path.mkdir(parents=True, exist_ok=True)

	for subdir in (
		"clients",
		"quotes",
		"invoices",
		"jobs",
		"transactions",
		"receipts",
		"reports",
		"config",
	):
		(path / subdir).mkdir(exist_ok=True)

	# Save settings
	settings_path = path / "config" / "settings.json"
	settings_path.write_text(settings.model_dump_json(indent=2))

	# Copy default chart of accounts
	default_coa = files("small_business.data").joinpath("default_chart_of_accounts.yaml")
	shutil.copy(str(default_coa), path / "config" / "chart_of_accounts.yaml")

	return path
