"""End-to-end integration test for reporting."""

from datetime import date
from decimal import Decimal

from small_business.models import Account, AccountType, ChartOfAccounts, JournalEntry, Transaction
from small_business.reports.balance_sheet import generate_balance_sheet
from small_business.reports.bas_gst import generate_bas_report
from small_business.reports.export import (
	export_balance_sheet_csv,
	export_bas_csv,
	export_profit_loss_csv,
)
from small_business.reports.profit_loss import generate_profit_loss_report
from small_business.storage import StorageRegistry


def test_complete_reporting_workflow(tmp_path):
	"""Test complete reporting workflow with all report types."""
	data_dir = tmp_path / "data"
	reports_dir = tmp_path / "reports"
	reports_dir.mkdir()

	# Create chart of accounts
	chart = ChartOfAccounts(
		accounts=[
			Account(name="Bank Cheque Account", account_type=AccountType.ASSET),
			Account(name="Sales Revenue", account_type=AccountType.INCOME),
			Account(name="Rent", account_type=AccountType.EXPENSE),
			Account(name="Supplies", account_type=AccountType.EXPENSE),
			Account(name="Owner's Equity", account_type=AccountType.EQUITY),
		]
	)

	# Save transactions for November 2025
	transactions = [
		# Opening balance
		Transaction(
			date=date(2025, 11, 1),
			description="Opening balance",
			entries=[
				JournalEntry(
					account_code="Bank Cheque Account", debit=Decimal("10000.00"), credit=Decimal("0")
				),
				JournalEntry(
					account_code="Owner's Equity", debit=Decimal("0"), credit=Decimal("10000.00")
				),
			],
		),
		# Sales with GST
		Transaction(
			date=date(2025, 11, 15),
			description="Sales invoice",
			gst_inclusive=True,
			entries=[
				JournalEntry(
					account_code="Bank Cheque Account", debit=Decimal("1100.00"), credit=Decimal("0")
				),
				JournalEntry(
					account_code="Sales Revenue", debit=Decimal("0"), credit=Decimal("1100.00")
				),
			],
		),
		# Rent expense with GST
		Transaction(
			date=date(2025, 11, 16),
			description="Monthly rent",
			gst_inclusive=True,
			entries=[
				JournalEntry(account_code="Rent", debit=Decimal("550.00"), credit=Decimal("0")),
				JournalEntry(
					account_code="Bank Cheque Account", debit=Decimal("0"), credit=Decimal("550.00")
				),
			],
		),
		# Supplies expense with GST
		Transaction(
			date=date(2025, 11, 20),
			description="Office supplies",
			gst_inclusive=True,
			entries=[
				JournalEntry(account_code="Supplies", debit=Decimal("220.00"), credit=Decimal("0")),
				JournalEntry(
					account_code="Bank Cheque Account", debit=Decimal("0"), credit=Decimal("220.00")
				),
			],
		),
	]

	storage = StorageRegistry(data_dir)
	for txn in transactions:
		storage.save_transaction(txn)

	# Generate P&L report
	pl_report = generate_profit_loss_report(
		chart=chart,
		data_dir=data_dir,
		start_date=date(2025, 11, 1),
		end_date=date(2025, 11, 30),
	)

	# Verify P&L
	assert pl_report["total_income"] == Decimal("1100.00")
	assert pl_report["total_expenses"] == Decimal("770.00")  # 550 + 220
	assert pl_report["net_profit"] == Decimal("330.00")

	# Export P&L to CSV
	pl_csv = reports_dir / "profit_loss.csv"
	export_profit_loss_csv(pl_report, pl_csv)
	assert pl_csv.exists()

	# Generate Balance Sheet
	bs_report = generate_balance_sheet(
		chart=chart,
		data_dir=data_dir,
		as_of_date=date(2025, 11, 30),
	)

	# Verify Balance Sheet
	# Bank: 10000 + 1100 - 550 - 220 = 10330
	assert bs_report["total_assets"] == Decimal("10330.00")
	assert bs_report["total_equity"] == Decimal("10000.00")

	# Export Balance Sheet to CSV
	bs_csv = reports_dir / "balance_sheet.csv"
	export_balance_sheet_csv(bs_report, bs_csv)
	assert bs_csv.exists()

	# Generate BAS report
	bas_report = generate_bas_report(
		chart=chart,
		data_dir=data_dir,
		start_date=date(2025, 11, 1),
		end_date=date(2025, 11, 30),
	)

	# Verify BAS
	# Sales: 1100, GST = 1100 × 1/11 = 100
	assert bas_report["gst_on_sales"] == Decimal("100.00")

	# Purchases: 550 + 220 = 770, GST = 770 × 1/11 = 70
	assert bas_report["gst_on_purchases"] == Decimal("70.00")

	# Net GST: 100 - 70 = 30 (owed to ATO)
	assert bas_report["net_gst"] == Decimal("30.00")

	# Export BAS to CSV
	bas_csv = reports_dir / "bas_report.csv"
	export_bas_csv(bas_report, bas_csv)
	assert bas_csv.exists()

	# Verify all reports generated
	assert len(list(reports_dir.glob("*.csv"))) == 3
