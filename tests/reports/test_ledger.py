"""Test ledger query engine."""

from datetime import date
from decimal import Decimal

from small_business.models import JournalEntry, Transaction
from small_business.reports.ledger import calculate_account_balance, get_account_transactions
from small_business.storage import StorageRegistry


def test_calculate_account_balance(tmp_path):
	"""Test calculating account balance from transactions."""
	data_dir = tmp_path / "data"

	# Save transactions affecting an expense account
	txn1 = Transaction(
		date=date(2025, 11, 15),
		description="Office supplies",
		entries=[
			JournalEntry(account_code="EXP-SUPPLIES", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)

	txn2 = Transaction(
		date=date(2025, 11, 16),
		description="More supplies",
		entries=[
			JournalEntry(account_code="EXP-SUPPLIES", debit=Decimal("50.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("50.00")),
		],
	)

	storage = StorageRegistry(data_dir)
	storage.save_transaction(txn1)
	storage.save_transaction(txn2)

	# Calculate balance
	balance = calculate_account_balance("EXP-SUPPLIES", data_dir, date(2025, 11, 16))

	# Expense accounts increase with debits
	assert balance == Decimal("150.00")


def test_calculate_bank_account_balance(tmp_path):
	"""Test calculating bank account balance."""
	data_dir = tmp_path / "data"

	# Starting balance transaction
	txn1 = Transaction(
		date=date(2025, 11, 1),
		description="Opening balance",
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("1000.00"), credit=Decimal("0")),
			JournalEntry(account_code="EQUITY", debit=Decimal("0"), credit=Decimal("1000.00")),
		],
	)

	# Expense (reduces bank balance)
	txn2 = Transaction(
		date=date(2025, 11, 15),
		description="Expense",
		entries=[
			JournalEntry(account_code="EXP-SUPPLIES", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)

	# Income (increases bank balance)
	txn3 = Transaction(
		date=date(2025, 11, 16),
		description="Income",
		entries=[
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("500.00"), credit=Decimal("0")),
			JournalEntry(account_code="INC-SALES", debit=Decimal("0"), credit=Decimal("500.00")),
		],
	)

	storage = StorageRegistry(data_dir)
	storage.save_transaction(txn1)
	storage.save_transaction(txn2)
	storage.save_transaction(txn3)

	balance = calculate_account_balance("BANK-CHQ", data_dir, date(2025, 11, 16))

	# Bank: 1000 (opening) - 100 (expense) + 500 (income) = 1400
	assert balance == Decimal("1400.00")


def test_get_account_transactions(tmp_path):
	"""Test getting all transactions for an account."""
	data_dir = tmp_path / "data"

	txn1 = Transaction(
		date=date(2025, 11, 15),
		description="Transaction 1",
		entries=[
			JournalEntry(account_code="EXP-TEST", debit=Decimal("100.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("100.00")),
		],
	)

	txn2 = Transaction(
		date=date(2025, 11, 16),
		description="Transaction 2",
		entries=[
			JournalEntry(account_code="EXP-OTHER", debit=Decimal("50.00"), credit=Decimal("0")),
			JournalEntry(account_code="BANK-CHQ", debit=Decimal("0"), credit=Decimal("50.00")),
		],
	)

	storage = StorageRegistry(data_dir)
	storage.save_transaction(txn1)
	storage.save_transaction(txn2)

	# Get transactions for EXP-TEST
	transactions = get_account_transactions("EXP-TEST", data_dir, date(2025, 11, 16))

	assert len(transactions) == 1
	assert transactions[0].description == "Transaction 1"
