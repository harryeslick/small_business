"""Test Balance Sheet report."""

from datetime import date
from decimal import Decimal

from small_business.models import Account, AccountType, ChartOfAccounts, JournalEntry, Transaction
from small_business.reports.balance_sheet import generate_balance_sheet
from small_business.storage.transaction_store import save_transaction


def test_generate_balance_sheet(tmp_path):
	"""Test generating balance sheet."""
	data_dir = tmp_path / "data"

	chart = ChartOfAccounts(
		accounts=[
			Account(code="BANK-CHQ", name="Bank Cheque", account_type=AccountType.ASSET),
			Account(code="ASSET-EQUIP", name="Equipment", account_type=AccountType.ASSET),
			Account(code="LIAB-LOAN", name="Business Loan", account_type=AccountType.LIABILITY),
			Account(code="EQUITY", name="Owner's Equity", account_type=AccountType.EQUITY),
		]
	)

	# Opening equity
	txn1 = Transaction(
		date=date(2025, 11, 1),
		description="Opening balance",
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("10000.00"), credit=Decimal("0")),
			JournalEntry(account_code="EQUITY", debit=Decimal("0"), credit=Decimal("10000.00")),
		],
	)

	# Purchase equipment
	txn2 = Transaction(
		date=date(2025, 11, 15),
		description="Equipment purchase",
		entries=[
			JournalEntry(account_code="ASSET-EQUIP", debit=Decimal("5000.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("5000.00")),
		],
	)

	# Business loan
	txn3 = Transaction(
		date=date(2025, 11, 20),
		description="Business loan",
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("3000.00"), credit=Decimal("0")),
			JournalEntry(account_code="LIAB-LOAN", debit=Decimal("0"), credit=Decimal("3000.00")),
		],
	)

	save_transaction(txn1, data_dir)
	save_transaction(txn2, data_dir)
	save_transaction(txn3, data_dir)

	# Generate balance sheet
	report = generate_balance_sheet(
		chart=chart,
		data_dir=data_dir,
		as_of_date=date(2025, 11, 30),
	)

	# Check assets: Bank (10000 - 5000 + 3000) + Equipment (5000) = 13000
	assert report["total_assets"] == Decimal("13000.00")
	assert report["assets"]["BANK-CHQ"]["balance"] == Decimal("8000.00")
	assert report["assets"]["ASSET-EQUIP"]["balance"] == Decimal("5000.00")

	# Check liabilities: Loan = 3000
	assert report["total_liabilities"] == Decimal("3000.00")

	# Check equity: 10000
	assert report["total_equity"] == Decimal("10000.00")

	# Accounting equation: Assets = Liabilities + Equity
	assert report["total_assets"] == report["total_liabilities"] + report["total_equity"]
