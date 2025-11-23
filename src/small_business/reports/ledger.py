"""Ledger queries for account balances and transactions."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.models import Transaction
from small_business.storage.transaction_store import load_transactions


def calculate_account_balance(
	account_code: str,
	data_dir: Path,
	as_of_date: date,
) -> Decimal:
	"""Calculate account balance as of a specific date.

	Args:
		account_code: Account code to calculate balance for
		data_dir: Data directory
		as_of_date: Calculate balance up to this date

	Returns:
		Account balance (debits - credits for asset/expense accounts,
		                  credits - debits for liability/income/equity accounts)
	"""
	transactions = load_transactions(data_dir, as_of_date)

	total_debits = Decimal("0")
	total_credits = Decimal("0")

	for txn in transactions:
		# Only include transactions up to as_of_date
		if txn.date <= as_of_date:
			for entry in txn.entries:
				if entry.account_code == account_code:
					total_debits += entry.debit
					total_credits += entry.credit

	# For most accounts, balance = debits - credits
	# (This is correct for assets and expenses)
	# For liabilities, income, and equity: balance = credits - debits
	# However, we return the raw debit balance here and let reports
	# interpret based on account type
	return total_debits - total_credits


def get_account_transactions(
	account_code: str,
	data_dir: Path,
	as_of_date: date,
) -> list[Transaction]:
	"""Get all transactions affecting an account.

	Args:
		account_code: Account code to query
		data_dir: Data directory
		as_of_date: Get transactions up to this date

	Returns:
		List of transactions affecting the account
	"""
	all_transactions = load_transactions(data_dir, as_of_date)

	# Filter transactions that have entries for this account
	account_transactions = []
	for txn in all_transactions:
		if txn.date <= as_of_date:
			for entry in txn.entries:
				if entry.account_code == account_code:
					account_transactions.append(txn)
					break  # Only add transaction once

	return account_transactions
