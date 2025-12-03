"""Profit & Loss (P&L) report generation."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.models import AccountType, ChartOfAccounts, get_financial_year
from small_business.storage import StorageRegistry


def generate_profit_loss_report(
	chart: ChartOfAccounts,
	data_dir: Path,
	start_date: date,
	end_date: date,
) -> dict:
	"""Generate Profit & Loss report.

	Args:
		chart: Chart of accounts
		data_dir: Data directory
		start_date: Report start date
		end_date: Report end date

	Returns:
		Dictionary with income, expenses, and net profit
	"""
	# Load transactions in date range
	storage = StorageRegistry(data_dir)
	fy = get_financial_year(end_date)
	transactions = storage.get_all_transactions(financial_year=fy)
	transactions = [t for t in transactions if start_date <= t.date <= end_date]

	# Calculate income by account
	income_accounts = {}
	total_income = Decimal("0")

	for account in chart.accounts:
		if account.account_type == AccountType.INCOME:
			# For income accounts, credits increase balance
			balance = Decimal("0")
			for txn in transactions:
				for entry in txn.entries:
					if entry.account_code == account.name:
						balance += entry.credit - entry.debit

			if balance > 0:
				income_accounts[account.name] = {
					"name": account.name,
					"balance": balance,
				}
				total_income += balance

	# Calculate expenses by account
	expense_accounts = {}
	total_expenses = Decimal("0")

	for account in chart.accounts:
		if account.account_type == AccountType.EXPENSE:
			# For expense accounts, debits increase balance
			balance = Decimal("0")
			for txn in transactions:
				for entry in txn.entries:
					if entry.account_code == account.name:
						balance += entry.debit - entry.credit

			if balance > 0:
				expense_accounts[account.name] = {
					"name": account.name,
					"balance": balance,
				}
				total_expenses += balance

	# Calculate net profit
	net_profit = total_income - total_expenses

	return {
		"start_date": start_date,
		"end_date": end_date,
		"income": income_accounts,
		"total_income": total_income,
		"expenses": expense_accounts,
		"total_expenses": total_expenses,
		"net_profit": net_profit,
	}
