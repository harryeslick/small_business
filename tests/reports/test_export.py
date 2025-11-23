"""Test report export functionality."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd

from small_business.reports.export import export_balance_sheet_csv, export_bas_csv, export_profit_loss_csv


def test_export_profit_loss_csv(tmp_path):
	"""Test exporting P&L to CSV."""
	report = {
		"start_date": date(2025, 11, 1),
		"end_date": date(2025, 11, 30),
		"income": {
			"INC-SALES": {"name": "Sales", "balance": Decimal("1000.00")},
		},
		"total_income": Decimal("1000.00"),
		"expenses": {
			"EXP-RENT": {"name": "Rent", "balance": Decimal("500.00")},
			"EXP-SUPPLIES": {"name": "Supplies", "balance": Decimal("300.00")},
		},
		"total_expenses": Decimal("800.00"),
		"net_profit": Decimal("200.00"),
	}

	output_file = tmp_path / "pl_report.csv"
	export_profit_loss_csv(report, output_file)

	assert output_file.exists()

	# Read and verify CSV
	df = pd.read_csv(output_file)
	assert len(df) > 0
	assert "Account" in df.columns
	assert "Amount" in df.columns


def test_export_balance_sheet_csv(tmp_path):
	"""Test exporting balance sheet to CSV."""
	report = {
		"as_of_date": date(2025, 11, 30),
		"assets": {
			"BANK-CHQ": {"name": "Bank", "balance": Decimal("8000.00")},
		},
		"total_assets": Decimal("8000.00"),
		"liabilities": {
			"LIAB-LOAN": {"name": "Loan", "balance": Decimal("3000.00")},
		},
		"total_liabilities": Decimal("3000.00"),
		"equity": {
			"EQUITY": {"name": "Equity", "balance": Decimal("5000.00")},
		},
		"total_equity": Decimal("5000.00"),
	}

	output_file = tmp_path / "bs_report.csv"
	export_balance_sheet_csv(report, output_file)

	assert output_file.exists()


def test_export_bas_csv(tmp_path):
	"""Test exporting BAS report to CSV."""
	report = {
		"start_date": date(2025, 11, 1),
		"end_date": date(2025, 11, 30),
		"total_sales": Decimal("330.00"),
		"gst_on_sales": Decimal("30.00"),
		"total_purchases": Decimal("55.00"),
		"gst_on_purchases": Decimal("5.00"),
		"net_gst": Decimal("25.00"),
	}

	output_file = tmp_path / "bas_report.csv"
	export_bas_csv(report, output_file)

	assert output_file.exists()
