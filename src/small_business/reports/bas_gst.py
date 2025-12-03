"""BAS/GST report generation for Australian tax compliance."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from small_business.models import AccountType, ChartOfAccounts, get_financial_year
from small_business.storage import StorageRegistry


def calculate_gst_component(amount: Decimal, gst_inclusive: bool) -> Decimal:
	"""Calculate GST component of an amount.

	Args:
		amount: Total amount
		gst_inclusive: Whether amount includes GST

	Returns:
		GST component (1/11 if inclusive, 10% if exclusive)
	"""
	if gst_inclusive:
		# GST = amount × 1/11
		return (amount / Decimal("11")).quantize(Decimal("0.01"))
	else:
		# GST = amount × 10%
		return (amount * Decimal("0.10")).quantize(Decimal("0.01"))


def generate_bas_report(
	chart: ChartOfAccounts,
	data_dir: Path,
	start_date: date,
	end_date: date,
) -> dict:
	"""Generate BAS/GST report.

	Args:
		chart: Chart of accounts
		data_dir: Data directory
		start_date: Report start date
		end_date: Report end date

	Returns:
		Dictionary with GST collected, paid, and net amount
	"""
	storage = StorageRegistry(data_dir)
	fy = get_financial_year(end_date)
	transactions = storage.get_all_transactions(financial_year=fy)
	transactions = [t for t in transactions if start_date <= t.date <= end_date]

	# Build sets of income and expense account names
	income_accounts = {acc.name for acc in chart.accounts if acc.account_type == AccountType.INCOME}
	expense_accounts = {
		acc.name for acc in chart.accounts if acc.account_type == AccountType.EXPENSE
	}

	total_sales = Decimal("0")
	total_purchases = Decimal("0")
	gst_on_sales = Decimal("0")
	gst_on_purchases = Decimal("0")

	for txn in transactions:
		# Determine if transaction is income or expense
		# Income: has credit to income account
		# Expense: has debit to expense account

		is_income = any(
			entry.account_code in income_accounts and entry.credit > 0 for entry in txn.entries
		)
		is_expense = any(
			entry.account_code in expense_accounts and entry.debit > 0 for entry in txn.entries
		)

		if is_income:
			# Calculate sales amount and GST
			for entry in txn.entries:
				if entry.account_code in income_accounts:
					amount = entry.credit
					total_sales += amount
					if txn.gst_inclusive:
						gst_on_sales += calculate_gst_component(amount, True)

		elif is_expense:
			# Calculate purchase amount and GST
			for entry in txn.entries:
				if entry.account_code in expense_accounts:
					amount = entry.debit
					total_purchases += amount
					if txn.gst_inclusive:
						gst_on_purchases += calculate_gst_component(amount, True)

	# Net GST = GST collected - GST paid
	net_gst = gst_on_sales - gst_on_purchases

	return {
		"start_date": start_date,
		"end_date": end_date,
		"total_sales": total_sales,
		"gst_on_sales": gst_on_sales,
		"total_purchases": total_purchases,
		"gst_on_purchases": gst_on_purchases,
		"net_gst": net_gst,
	}
