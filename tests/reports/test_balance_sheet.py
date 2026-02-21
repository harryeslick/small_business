"""Test Balance Sheet report."""

from datetime import date
from decimal import Decimal

from small_business.models import Account, AccountType, ChartOfAccounts, JournalEntry, Transaction
from small_business.reports.balance_sheet import generate_balance_sheet
from small_business.reports.models import BalanceSheetReport
from small_business.storage import StorageRegistry


def test_generate_balance_sheet(tmp_path):
	"""Test generating balance sheet."""
	data_dir = tmp_path / "data"

	chart = ChartOfAccounts(
		accounts=[
			Account(name="Bank Cheque", account_type=AccountType.ASSET),
			Account(name="Equipment", account_type=AccountType.ASSET),
			Account(name="Business Loan", account_type=AccountType.LIABILITY),
			Account(name="Owner's Equity", account_type=AccountType.EQUITY),
		]
	)

	# Opening equity
	txn1 = Transaction(
		date=date(2025, 11, 1),
		description="Opening balance",
		entries=[
			JournalEntry(account_code="Bank Cheque", debit=Decimal("10000.00"), credit=Decimal("0")),
			JournalEntry(account_code="Owner's Equity", debit=Decimal("0"), credit=Decimal("10000.00")),
		],
	)

	# Purchase equipment
	txn2 = Transaction(
		date=date(2025, 11, 15),
		description="Equipment purchase",
		entries=[
			JournalEntry(account_code="Equipment", debit=Decimal("5000.00"), credit=Decimal("0")),
			JournalEntry(account_code="Bank Cheque", debit=Decimal("0"), credit=Decimal("5000.00")),
		],
	)

	# Business loan
	txn3 = Transaction(
		date=date(2025, 11, 20),
		description="Business loan",
		entries=[
			JournalEntry(account_code="Bank Cheque", debit=Decimal("3000.00"), credit=Decimal("0")),
			JournalEntry(account_code="Business Loan", debit=Decimal("0"), credit=Decimal("3000.00")),
		],
	)

	storage = StorageRegistry(data_dir)
	storage.save_transaction(txn1)
	storage.save_transaction(txn2)
	storage.save_transaction(txn3)

	# Generate balance sheet
	report = generate_balance_sheet(
		chart=chart,
		data_dir=data_dir,
		as_of_date=date(2025, 11, 30),
	)

	assert isinstance(report, BalanceSheetReport)

	# Check assets: Bank (10000 - 5000 + 3000) + Equipment (5000) = 13000
	assert report.total_assets == Decimal("13000.00")
	assert report.assets["Bank Cheque"].balance == Decimal("8000.00")
	assert report.assets["Equipment"].balance == Decimal("5000.00")

	# Check liabilities: Loan = 3000
	assert report.total_liabilities == Decimal("3000.00")

	# Check equity: 10000
	assert report.total_equity == Decimal("10000.00")

	# Accounting equation: Assets = Liabilities + Equity
	assert report.total_assets == report.total_liabilities + report.total_equity
