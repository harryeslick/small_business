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
