"""Test configuration models."""

from small_business.models.config import BankFormat, BankFormats, Settings


def test_bank_format_valid():
	"""Test valid bank format configuration."""
	config = BankFormat(
		name="commonwealth",
		date_column="Date",
		description_column="Description",
		debit_column="Debit",
		credit_column="Credit",
		balance_column="Balance",
		date_format="%d/%m/%Y",
	)
	assert config.name == "commonwealth"
	assert config.date_format == "%d/%m/%Y"


def test_bank_formats_multiple():
	"""Test bank formats collection with multiple banks."""
	formats = BankFormats(
		formats=[
			BankFormat(
				name="commonwealth",
				date_column="Date",
				description_column="Description",
				debit_column="Debit",
				credit_column="Credit",
				balance_column="Balance",
				date_format="%d/%m/%Y",
			),
			BankFormat(
				name="westpac",
				date_column="Transaction Date",
				description_column="Narration",
				debit_column="Debit Amount",
				credit_column="Credit Amount",
				balance_column="Balance",
				date_format="%d-%m-%Y",
			),
		]
	)
	assert len(formats.formats) == 2
	comm = formats.get_format("commonwealth")
	assert comm.date_column == "Date"


def test_bank_formats_get_format_not_found():
	"""Test getting non-existent bank format raises KeyError."""
	formats = BankFormats(formats=[])
	try:
		formats.get_format("nonexistent")
		assert False, "Should raise KeyError"
	except KeyError as e:
		assert "nonexistent" in str(e)


def test_settings_default_values():
	"""Test Settings model with default values."""
	settings = Settings()
	assert settings.gst_rate.as_tuple().exponent == -2  # 2 decimal places
	assert settings.financial_year_start_month == 7
	assert settings.currency == "AUD"
	assert settings.data_directory == "data"
	assert settings.quote_template_path == "templates/quote_template.docx"
	assert settings.invoice_template_path == "templates/invoice_template.docx"


def test_settings_custom_template_paths():
	"""Test Settings with custom template paths."""
	settings = Settings(
		quote_template_path="custom/quote.docx",
		invoice_template_path="custom/invoice.docx",
	)
	assert settings.quote_template_path == "custom/quote.docx"
	assert settings.invoice_template_path == "custom/invoice.docx"


def test_settings_with_business_details():
	"""Test Settings with business details populated."""
	settings = Settings(
		business_name="Test Business Pty Ltd",
		business_abn="12 345 678 901",
		business_email="info@testbusiness.com.au",
		business_phone="0400 000 000",
		business_address="123 Test St, Sydney NSW 2000",
	)
	assert settings.business_name == "Test Business Pty Ltd"
	assert settings.business_abn == "12 345 678 901"
	assert settings.business_email == "info@testbusiness.com.au"
	assert settings.business_phone == "0400 000 000"
	assert settings.business_address == "123 Test St, Sydney NSW 2000"
