"""Test Profit & Loss report."""

from datetime import date
from decimal import Decimal

from small_business.models import Account, AccountType, ChartOfAccounts, JournalEntry, Transaction
from small_business.reports.profit_loss import generate_profit_loss_report
from small_business.storage import StorageRegistry


def test_generate_profit_loss_report(tmp_path):
	"""Test generating P&L report."""
	data_dir = tmp_path / "data"

	# Create chart of accounts
	chart = ChartOfAccounts(
		accounts=[
			Account(code="INC-SALES", name="Sales", account_type=AccountType.INCOME),
			Account(code="INC-OTHER", name="Other Income", account_type=AccountType.INCOME),
			Account(code="EXP-SUPPLIES", name="Supplies", account_type=AccountType.EXPENSE),
			Account(code="EXP-RENT", name="Rent", account_type=AccountType.EXPENSE),
			Account(code="BANK-CHQ", name="Bank", account_type=AccountType.ASSET),
		]
	)

	# Save transactions
	# Income: $1000
	txn1 = Transaction(
		date=date(2025, 11, 15),
		description="Sales",
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("1000.00"), credit=Decimal("0")),
			JournalEntry(account_code="INC-SALES", debit=Decimal("0"), credit=Decimal("1000.00")),
		],
	)

	# Expense: $300
	txn2 = Transaction(
		date=date(2025, 11, 16),
		description="Supplies",
		entries=[
			JournalEntry(account_code="EXP-SUPPLIES", debit=Decimal("300.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("300.00")),
		],
	)

	# Expense: $500
	txn3 = Transaction(
		date=date(2025, 11, 17),
		description="Rent",
		entries=[
			JournalEntry(account_code="EXP-RENT", debit=Decimal("500.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("500.00")),
		],
	)

	storage = StorageRegistry(data_dir)
	storage.save_transaction(txn1)
	storage.save_transaction(txn2)
	storage.save_transaction(txn3)

	# Generate P&L report
	report = generate_profit_loss_report(
		chart=chart,
		data_dir=data_dir,
		start_date=date(2025, 11, 1),
		end_date=date(2025, 11, 30),
	)

	# Check totals
	assert report["total_income"] == Decimal("1000.00")
	assert report["total_expenses"] == Decimal("800.00")
	assert report["net_profit"] == Decimal("200.00")

	# Check breakdown
	assert len(report["income"]) == 1
	assert report["income"]["INC-SALES"]["balance"] == Decimal("1000.00")

	assert len(report["expenses"]) == 2
	assert report["expenses"]["EXP-SUPPLIES"]["balance"] == Decimal("300.00")
	assert report["expenses"]["EXP-RENT"]["balance"] == Decimal("500.00")
