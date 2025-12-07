"""Initialize a new business data directory."""

import shutil
from importlib.resources import files
from pathlib import Path

from small_business.models.config import Settings


def init_business(business_settings: Settings, path: Path | None = None) -> Path:
	"""Initialize a new business directory with complete folder structure.

	Creates the following structure:
	- clients/           # Client records
	- quotes/            # Quote documents
	- invoices/          # Invoice documents
	- jobs/              # Job records
	- transactions/      # Accounting transactions by financial year
	- receipts/          # Receipt/invoice images
	- reports/           # Generated reports
	- config/            # Configuration files
	  - settings.json    # Business settings
	  - chart_of_accounts.yaml  # Chart of accounts (copy of default)

	Args:
		business_settings: Settings object with business configuration
		path: Base path where business directory will be created (default: current directory)

	Returns:
		Path to the created business directory

	Raises:
		FileExistsError: If business directory already exists and contains data

	Examples:
		>>> from pathlib import Path
		>>> from small_business.models import Settings
		>>> settings = Settings(
		...     business_name="Earthworks Studio",
		...     business_abn="12 345 678 901",
		...     business_email="hello@earthworks.studio"
		... )
		>>> business_dir = init_business(settings, Path("~/businesses"))
		>>> print(business_dir)
		/Users/user/businesses/earthworks_studio
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
	business_dir.mkdir(parents=True, exist_ok=True)
	(business_dir / "clients").mkdir(exist_ok=True)
	(business_dir / "quotes").mkdir(exist_ok=True)
	(business_dir / "invoices").mkdir(exist_ok=True)
	(business_dir / "jobs").mkdir(exist_ok=True)
	(business_dir / "transactions").mkdir(exist_ok=True)
	(business_dir / "receipts").mkdir(exist_ok=True)
	(business_dir / "reports").mkdir(exist_ok=True)
	(business_dir / "config").mkdir(exist_ok=True)

	# Save settings to config/settings.json
	settings_path = business_dir / "config" / "settings.json"
	settings_path.write_text(business_settings.model_dump_json(indent=2))

	# Copy default chart of accounts to config/chart_of_accounts.yaml
	default_coa_path = files("small_business.data").joinpath("default_chart_of_accounts.yaml")
	target_coa_path = business_dir / "config" / "chart_of_accounts.yaml"

	# Copy the file
	shutil.copy(str(default_coa_path), target_coa_path)

	return business_dir
