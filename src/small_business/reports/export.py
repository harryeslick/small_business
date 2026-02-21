"""Report export functionality to CSV and PDF."""

from pathlib import Path

import pandas as pd

from small_business.reports.models import BalanceSheetReport, BASReport, ProfitLossReport


def export_profit_loss_csv(report: ProfitLossReport, output_file: Path) -> None:
	"""Export Profit & Loss report to CSV.

	Args:
		report: P&L report model
		output_file: Path to save CSV file
	"""
	rows = []

	# Income section
	rows.append({"Category": "INCOME", "Account": "", "Amount": ""})
	for code, data in report.income.items():
		rows.append(
			{"Category": "Income", "Account": data.name, "Amount": float(data.balance)}
		)

	rows.append(
		{"Category": "", "Account": "Total Income", "Amount": float(report.total_income)}
	)
	rows.append({"Category": "", "Account": "", "Amount": ""})

	# Expenses section
	rows.append({"Category": "EXPENSES", "Account": "", "Amount": ""})
	for code, data in report.expenses.items():
		rows.append(
			{"Category": "Expense", "Account": data.name, "Amount": float(data.balance)}
		)

	rows.append(
		{"Category": "", "Account": "Total Expenses", "Amount": float(report.total_expenses)}
	)
	rows.append({"Category": "", "Account": "", "Amount": ""})

	# Net profit
	rows.append({"Category": "", "Account": "NET PROFIT", "Amount": float(report.net_profit)})

	df = pd.DataFrame(rows)
	df.to_csv(output_file, index=False)


def export_balance_sheet_csv(report: BalanceSheetReport, output_file: Path) -> None:
	"""Export Balance Sheet to CSV.

	Args:
		report: Balance sheet report model
		output_file: Path to save CSV file
	"""
	rows = []

	# Assets
	rows.append({"Category": "ASSETS", "Account": "", "Amount": ""})
	for code, data in report.assets.items():
		rows.append(
			{"Category": "Asset", "Account": data.name, "Amount": float(data.balance)}
		)

	rows.append(
		{"Category": "", "Account": "Total Assets", "Amount": float(report.total_assets)}
	)
	rows.append({"Category": "", "Account": "", "Amount": ""})

	# Liabilities
	rows.append({"Category": "LIABILITIES", "Account": "", "Amount": ""})
	for code, data in report.liabilities.items():
		rows.append(
			{"Category": "Liability", "Account": data.name, "Amount": float(data.balance)}
		)

	rows.append(
		{
			"Category": "",
			"Account": "Total Liabilities",
			"Amount": float(report.total_liabilities),
		}
	)
	rows.append({"Category": "", "Account": "", "Amount": ""})

	# Equity
	rows.append({"Category": "EQUITY", "Account": "", "Amount": ""})
	for code, data in report.equity.items():
		rows.append(
			{"Category": "Equity", "Account": data.name, "Amount": float(data.balance)}
		)

	rows.append(
		{"Category": "", "Account": "Total Equity", "Amount": float(report.total_equity)}
	)

	df = pd.DataFrame(rows)
	df.to_csv(output_file, index=False)


def export_bas_csv(report: BASReport, output_file: Path) -> None:
	"""Export BAS/GST report to CSV.

	Args:
		report: BAS report model
		output_file: Path to save CSV file
	"""
	rows = [
		{"Item": "Total Sales (GST Inclusive)", "Amount": float(report.total_sales)},
		{"Item": "GST on Sales", "Amount": float(report.gst_on_sales)},
		{"Item": "", "Amount": ""},
		{"Item": "Total Purchases (GST Inclusive)", "Amount": float(report.total_purchases)},
		{"Item": "GST on Purchases", "Amount": float(report.gst_on_purchases)},
		{"Item": "", "Amount": ""},
		{"Item": "NET GST (Owed to/from ATO)", "Amount": float(report.net_gst)},
	]

	df = pd.DataFrame(rows)
	df.to_csv(output_file, index=False)
