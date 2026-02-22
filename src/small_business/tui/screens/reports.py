"""Reports screen — financial reports with tabbed Balance Sheet / P&L / BAS."""

from __future__ import annotations

from datetime import date

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static, TabbedContent, TabPane

from small_business.reports import (
	BalanceSheetReport,
	BASReport,
	ProfitLossReport,
	export_balance_sheet_csv,
	export_bas_csv,
	export_profit_loss_csv,
	generate_balance_sheet,
	generate_bas_report,
	generate_profit_loss_report,
)
from small_business.tui.utils import format_currency, format_date


class ReportsScreen(Screen):
	"""Financial reports with tabbed view and CSV export."""

	BINDINGS = [
		Binding("escape", "pop_screen", "Back"),
		Binding("e", "export_csv", "Export CSV"),
		Binding("g", "generate", "Generate"),
	]

	def __init__(self) -> None:
		super().__init__()
		self._bs_report: BalanceSheetReport | None = None
		self._pl_report: ProfitLossReport | None = None
		self._bas_report: BASReport | None = None

	def compose(self) -> ComposeResult:
		yield Header()
		with Vertical(id="reports-content"):
			yield Static(" Reports", classes="dashboard-panel-title")

			# Period selector
			with Horizontal(id="report-period-row", classes="form-row"):
				with Vertical():
					yield Label("Start Date (YYYY-MM-DD)")
					yield Input(
						value=_fy_start().isoformat(),
						id="report-start-date",
					)
				with Vertical():
					yield Label("End Date (YYYY-MM-DD)")
					yield Input(
						value=date.today().isoformat(),
						id="report-end-date",
					)
				with Vertical():
					yield Button("Generate", variant="primary", id="btn-generate")
					yield Button("Export CSV", variant="default", id="btn-export")

			# Tabbed reports
			with TabbedContent(id="report-tabs"):
				with TabPane("Balance Sheet", id="tab-bs"):
					yield Static("Press [g] Generate to view report.", id="bs-content")
				with TabPane("Profit & Loss", id="tab-pl"):
					yield Static("Press [g] Generate to view report.", id="pl-content")
				with TabPane("BAS / GST", id="tab-bas"):
					yield Static("Press [g] Generate to view report.", id="bas-content")

		yield Footer()

	def on_button_pressed(self, event: Button.Pressed) -> None:
		"""Handle button clicks."""
		if event.button.id == "btn-generate":
			self.action_generate()
		elif event.button.id == "btn-export":
			self.action_export_csv()

	def action_generate(self) -> None:
		"""Generate all three reports."""
		storage = self.app.storage
		if storage is None:
			return

		start_str = self.query_one("#report-start-date", Input).value.strip()
		end_str = self.query_one("#report-end-date", Input).value.strip()

		try:
			start_date = date.fromisoformat(start_str)
			end_date = date.fromisoformat(end_str)
		except ValueError:
			self.notify("Invalid date format. Use YYYY-MM-DD.", severity="error")
			return

		try:
			chart = storage.get_chart_of_accounts()
		except FileNotFoundError:
			self.notify("Chart of accounts not found.", severity="error")
			return

		data_dir = self.app.data_dir

		# Generate all reports
		try:
			self._bs_report = generate_balance_sheet(chart, data_dir, end_date)
			self._render_balance_sheet(self._bs_report)
		except Exception as e:
			self.query_one("#bs-content", Static).update(f"Error: {e}")

		try:
			self._pl_report = generate_profit_loss_report(chart, data_dir, start_date, end_date)
			self._render_profit_loss(self._pl_report)
		except Exception as e:
			self.query_one("#pl-content", Static).update(f"Error: {e}")

		try:
			self._bas_report = generate_bas_report(chart, data_dir, start_date, end_date)
			self._render_bas(self._bas_report)
		except Exception as e:
			self.query_one("#bas-content", Static).update(f"Error: {e}")

		self.notify("Reports generated.", title="Done")

	def _render_balance_sheet(self, report: BalanceSheetReport) -> None:
		"""Render balance sheet report."""
		lines = [
			f"[bold]Balance Sheet[/]  —  As of {format_date(report.as_of_date)}",
			"",
			"[bold]ASSETS[/]",
		]
		for code, acct in report.assets.items():
			if acct.balance != 0:
				lines.append(f"  {acct.name:<40} {format_currency(acct.balance):>12}")
		lines.append(f"  {'Total Assets':<40} [bold]{format_currency(report.total_assets):>12}[/]")

		lines.append("")
		lines.append("[bold]LIABILITIES[/]")
		for code, acct in report.liabilities.items():
			if acct.balance != 0:
				lines.append(f"  {acct.name:<40} {format_currency(acct.balance):>12}")
		lines.append(
			f"  {'Total Liabilities':<40} [bold]{format_currency(report.total_liabilities):>12}[/]"
		)

		lines.append("")
		lines.append("[bold]EQUITY[/]")
		for code, acct in report.equity.items():
			if acct.balance != 0:
				lines.append(f"  {acct.name:<40} {format_currency(acct.balance):>12}")
		lines.append(f"  {'Total Equity':<40} [bold]{format_currency(report.total_equity):>12}[/]")

		self.query_one("#bs-content", Static).update("\n".join(lines))

	def _render_profit_loss(self, report: ProfitLossReport) -> None:
		"""Render profit & loss report."""
		lines = [
			f"[bold]Profit & Loss[/]  —  {format_date(report.start_date)} to {format_date(report.end_date)}",
			"",
			"[bold]INCOME[/]",
		]
		for code, acct in report.income.items():
			if acct.balance != 0:
				lines.append(f"  {acct.name:<40} {format_currency(acct.balance):>12}")
		lines.append(f"  {'Total Income':<40} [bold]{format_currency(report.total_income):>12}[/]")

		lines.append("")
		lines.append("[bold]EXPENSES[/]")
		for code, acct in report.expenses.items():
			if acct.balance != 0:
				lines.append(f"  {acct.name:<40} {format_currency(acct.balance):>12}")
		lines.append(
			f"  {'Total Expenses':<40} [bold]{format_currency(report.total_expenses):>12}[/]"
		)

		lines.append("")
		profit_color = "green" if report.net_profit >= 0 else "red"
		lines.append(
			f"  [bold {profit_color}]{'NET PROFIT':<40} {format_currency(report.net_profit):>12}[/]"
		)

		self.query_one("#pl-content", Static).update("\n".join(lines))

	def _render_bas(self, report: BASReport) -> None:
		"""Render BAS/GST report."""
		lines = [
			f"[bold]BAS / GST Report[/]  —  {format_date(report.start_date)} to {format_date(report.end_date)}",
			"",
			f"  {'Total Sales':<40} {format_currency(report.total_sales):>12}",
			f"  {'GST on Sales':<40} {format_currency(report.gst_on_sales):>12}",
			"",
			f"  {'Total Purchases':<40} {format_currency(report.total_purchases):>12}",
			f"  {'GST on Purchases':<40} {format_currency(report.gst_on_purchases):>12}",
			"",
		]

		net_label = "Net GST Payable" if report.net_gst >= 0 else "Net GST Refund"
		net_color = "red" if report.net_gst >= 0 else "green"
		lines.append(
			f"  [bold {net_color}]{net_label:<40} {format_currency(abs(report.net_gst)):>12}[/]"
		)

		self.query_one("#bas-content", Static).update("\n".join(lines))

	def action_export_csv(self) -> None:
		"""Export the currently visible report to CSV."""
		if not self.app.data_dir:
			return

		reports_dir = self.app.data_dir / "reports"
		reports_dir.mkdir(exist_ok=True)

		exported = []

		if self._pl_report:
			path = reports_dir / "profit_loss.csv"
			export_profit_loss_csv(self._pl_report, path)
			exported.append(f"P&L: {path}")

		if self._bs_report:
			path = reports_dir / "balance_sheet.csv"
			export_balance_sheet_csv(self._bs_report, path)
			exported.append(f"BS: {path}")

		if self._bas_report:
			path = reports_dir / "bas_gst.csv"
			export_bas_csv(self._bas_report, path)
			exported.append(f"BAS: {path}")

		if exported:
			self.notify("\n".join(exported), title="Exported")
		else:
			self.notify("Generate reports first.", severity="warning")


def _fy_start() -> date:
	"""Get the start date of the current Australian financial year."""
	today = date.today()
	if today.month >= 7:
		return date(today.year, 7, 1)
	return date(today.year - 1, 7, 1)
