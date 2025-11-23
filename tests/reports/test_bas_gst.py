"""Test BAS/GST report."""

from datetime import date
from decimal import Decimal

from small_business.models import JournalEntry, Transaction
from small_business.reports.bas_gst import generate_bas_report
from small_business.storage.transaction_store import save_transaction


def test_generate_bas_report(tmp_path):
	"""Test generating BAS/GST report."""
	data_dir = tmp_path / "data"

	# GST collected (on sales) - GST inclusive $110 includes $10 GST
	txn1 = Transaction(
		date=date(2025, 11, 15),
		description="Sales",
		gst_inclusive=True,
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("110.00"), credit=Decimal("0")),
			JournalEntry(account_code="INC-SALES", debit=Decimal("0"), credit=Decimal("110.00")),
		],
	)

	# GST paid (on expenses) - GST inclusive $55 includes $5 GST
	txn2 = Transaction(
		date=date(2025, 11, 16),
		description="Supplies",
		gst_inclusive=True,
		entries=[
			JournalEntry(account_code="EXP-SUPPLIES", debit=Decimal("55.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("55.00")),
		],
	)

	# Another sale
	txn3 = Transaction(
		date=date(2025, 11, 20),
		description="More sales",
		gst_inclusive=True,
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("220.00"), credit=Decimal("0")),
			JournalEntry(account_code="INC-SALES", debit=Decimal("0"), credit=Decimal("220.00")),
		],
	)

	save_transaction(txn1, data_dir)
	save_transaction(txn2, data_dir)
	save_transaction(txn3, data_dir)

	# Generate BAS report
	report = generate_bas_report(
		data_dir=data_dir,
		start_date=date(2025, 11, 1),
		end_date=date(2025, 11, 30),
	)

	# Total sales: $110 + $220 = $330
	assert report["total_sales"] == Decimal("330.00")

	# GST on sales: 330 × 1/11 = $30
	assert report["gst_on_sales"] == Decimal("30.00")

	# Total purchases: $55
	assert report["total_purchases"] == Decimal("55.00")

	# GST on purchases: 55 × 1/11 = $5
	assert report["gst_on_purchases"] == Decimal("5.00")

	# Net GST: $30 - $5 = $25 (owed to ATO)
	assert report["net_gst"] == Decimal("25.00")
