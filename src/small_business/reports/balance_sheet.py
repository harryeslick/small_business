"""Balance Sheet report generation."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.models import AccountType, ChartOfAccounts, get_financial_year
from small_business.storage import StorageRegistry


def generate_balance_sheet(
	chart: ChartOfAccounts,
	data_dir: Path,
	as_of_date: date,
) -> dict:
	"""Generate Balance Sheet report.

	Args:
		chart: Chart of accounts
		data_dir: Data directory
		as_of_date: Report as of this date

	Returns:
		Dictionary with assets, liabilities, and equity
	"""
	storage = StorageRegistry(data_dir)
	fy = get_financial_year(as_of_date)
	transactions = storage.get_all_transactions(financial_year=fy)
	transactions = [t for t in transactions if t.date <= as_of_date]

	# Calculate assets
	asset_accounts = {}
	total_assets = Decimal("0")

	for account in chart.accounts:
		if account.account_type == AccountType.ASSET:
			# For assets, debits increase balance
			balance = Decimal("0")
			for txn in transactions:
				for entry in txn.entries:
					if entry.account_code == account.name:
						balance += entry.debit - entry.credit

			if balance != 0:
				asset_accounts[account.name] = {
					"name": account.name,
					"balance": balance,
				}
				total_assets += balance

	# Calculate liabilities
	liability_accounts = {}
	total_liabilities = Decimal("0")

	for account in chart.accounts:
		if account.account_type == AccountType.LIABILITY:
			# For liabilities, credits increase balance
			balance = Decimal("0")
			for txn in transactions:
				for entry in txn.entries:
					if entry.account_code == account.name:
						balance += entry.credit - entry.debit

			if balance != 0:
				liability_accounts[account.name] = {
					"name": account.name,
					"balance": balance,
				}
				total_liabilities += balance

	# Calculate equity
	equity_accounts = {}
	total_equity = Decimal("0")

	for account in chart.accounts:
		if account.account_type == AccountType.EQUITY:
			# For equity, credits increase balance
			balance = Decimal("0")
			for txn in transactions:
				for entry in txn.entries:
					if entry.account_code == account.name:
						balance += entry.credit - entry.debit

			if balance != 0:
				equity_accounts[account.name] = {
					"name": account.name,
					"balance": balance,
				}
				total_equity += balance

	return {
		"as_of_date": as_of_date,
		"assets": asset_accounts,
		"total_assets": total_assets,
		"liabilities": liability_accounts,
		"total_liabilities": total_liabilities,
		"equity": equity_accounts,
		"total_equity": total_equity,
	}
