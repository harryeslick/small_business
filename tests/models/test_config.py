"""Test configuration models."""

from small_business.models.config import BankFormat, BankFormats


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
