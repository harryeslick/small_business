"""Tests for Settings model."""

from decimal import Decimal

from small_business.models.config import Settings


def test_settings_default_values():
	"""Test settings model with default values."""
	settings = Settings()
	assert settings.gst_rate == Decimal("0.10")
	assert settings.financial_year_start_month == 7
	assert settings.currency == "AUD"
	assert settings.date_format == "%Y-%m-%d"
	assert settings.data_directory == "data"


def test_settings_custom_values():
	"""Test settings with custom values."""
	settings = Settings(
		gst_rate=Decimal("0.15"),
		financial_year_start_month=4,
		currency="NZD",
		business_name="Test Business",
		business_abn="12 345 678 901",
	)
	assert settings.gst_rate == Decimal("0.15")
	assert settings.financial_year_start_month == 4
	assert settings.currency == "NZD"
	assert settings.business_name == "Test Business"
	assert settings.business_abn == "12 345 678 901"


def test_settings_serialization():
	"""Test settings serialization."""
	settings = Settings(business_name="My Business")
	data = settings.model_dump()
	assert "gst_rate" in data
	assert "business_name" in data
	assert data["business_name"] == "My Business"
