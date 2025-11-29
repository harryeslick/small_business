"""Settings model."""

from decimal import Decimal

from pydantic import BaseModel, Field


class Settings(BaseModel):
	"""Application settings and constants."""

	# Tax settings
	gst_rate: Decimal = Field(default=Decimal("0.10"), ge=0, le=1, decimal_places=2)

	# Financial year settings
	financial_year_start_month: int = Field(default=7, ge=1, le=12)

	# Currency and formatting
	currency: str = "AUD"
	date_format: str = "%Y-%m-%d"

	# Business details
	business_name: str = ""
	business_abn: str = ""
	business_email: str = ""
	business_phone: str = ""
	business_address: str = ""

	# File paths
	data_directory: str = "data"

	# Template paths
	quote_template_path: str = "templates/quote_template.docx"
	invoice_template_path: str = "templates/invoice_template.docx"

	# Chart of accounts path (relative to data_directory/config/)
	chart_of_accounts_path: str = "chart_of_accounts.yaml"


class BankFormat(BaseModel):
	"""Configuration for a specific bank's CSV format."""

	name: str = Field(min_length=1)
	date_column: str = Field(min_length=1)
	description_column: str = Field(min_length=1)
	debit_column: str | None = None
	credit_column: str | None = None
	amount_column: str | None = None  # For single amount column (positive/negative)
	balance_column: str | None = None
	date_format: str = "%Y-%m-%d"


class BankFormats(BaseModel):
	"""Collection of bank format configurations."""

	formats: list[BankFormat] = Field(default_factory=list)

	def get_format(self, name: str) -> BankFormat:
		"""Get bank format by name."""
		for fmt in self.formats:
			if fmt.name == name:
				return fmt
		raise KeyError(f"Bank format not found: {name}")
