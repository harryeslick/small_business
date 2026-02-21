"""Typed Pydantic models for report return types."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class AccountBalance(BaseModel):
	"""Balance for a single account in a report."""

	name: str
	balance: Decimal


class BalanceSheetReport(BaseModel):
	"""Balance Sheet report data."""

	as_of_date: date
	assets: dict[str, AccountBalance]
	total_assets: Decimal
	liabilities: dict[str, AccountBalance]
	total_liabilities: Decimal
	equity: dict[str, AccountBalance]
	total_equity: Decimal


class ProfitLossReport(BaseModel):
	"""Profit & Loss report data."""

	start_date: date
	end_date: date
	income: dict[str, AccountBalance]
	total_income: Decimal
	expenses: dict[str, AccountBalance]
	total_expenses: Decimal
	net_profit: Decimal


class BASReport(BaseModel):
	"""BAS/GST report data."""

	start_date: date
	end_date: date
	total_sales: Decimal
	gst_on_sales: Decimal
	total_purchases: Decimal
	gst_on_purchases: Decimal
	net_gst: Decimal
