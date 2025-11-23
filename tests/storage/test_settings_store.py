"""Test settings storage operations."""

from small_business.models import Settings
from small_business.storage.settings_store import load_settings, save_settings


def test_save_and_load_settings(tmp_path):
	"""Test saving and loading settings."""
	settings = Settings(
		business_name="My Business",
		business_abn="12 345 678 901",
		business_email="info@mybusiness.com",
		business_phone="0400 123 456",
		business_address="123 Business St, Sydney NSW 2000",
	)

	save_settings(settings, tmp_path)
	loaded = load_settings(tmp_path)

	assert loaded.business_name == "My Business"
	assert loaded.business_abn == "12 345 678 901"
	assert loaded.business_email == "info@mybusiness.com"


def test_load_settings_with_defaults(tmp_path):
	"""Test loading settings when file doesn't exist returns defaults."""
	settings = load_settings(tmp_path)

	assert isinstance(settings, Settings)
	assert settings.business_name == ""
	assert settings.business_abn == ""


def test_save_settings_creates_directory(tmp_path):
	"""Test that save_settings creates the data directory if needed."""
	nested_path = tmp_path / "nested" / "data"

	settings = Settings(business_name="Test")
	save_settings(settings, nested_path)

	assert (nested_path / "settings.json").exists()


def test_save_settings_overwrites_existing(tmp_path):
	"""Test that saving settings overwrites existing file."""
	# Save initial settings
	settings1 = Settings(business_name="Business 1")
	save_settings(settings1, tmp_path)

	# Save different settings
	settings2 = Settings(business_name="Business 2")
	save_settings(settings2, tmp_path)

	# Load should get the latest
	loaded = load_settings(tmp_path)
	assert loaded.business_name == "Business 2"


def test_settings_with_template_paths(tmp_path):
	"""Test saving and loading settings with custom template paths."""
	settings = Settings(
		business_name="My Business",
		quote_template_path="custom/quote.docx",
		invoice_template_path="custom/invoice.docx",
	)

	save_settings(settings, tmp_path)
	loaded = load_settings(tmp_path)

	assert loaded.quote_template_path == "custom/quote.docx"
	assert loaded.invoice_template_path == "custom/invoice.docx"
