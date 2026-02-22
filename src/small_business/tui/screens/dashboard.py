"""Dashboard screen — financial health overview and action items."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from small_business.models import InvoiceStatus, QuoteStatus
from small_business.tui.utils import (
	current_financial_year,
	days_until,
	format_currency,
	format_date_short,
)
from small_business.tui.widgets.currency import CurrencyDisplay
from small_business.tui.widgets.notification_bar import NotificationBar
from small_business.tui.widgets.pipeline import EntityPipeline
from small_business.tui.widgets.sparkline_panel import SparklinePanel


class DashboardScreen(Screen):
	"""Main dashboard with financial overview, action items, and recent activity."""

	BINDINGS = [
		Binding("i", "app.push_screen('bank_import')", "Import"),
		Binding("c", "app.push_screen('classification')", "Classify"),
		Binding("r", "app.push_screen('reports')", "Reports"),
		Binding("question_mark", "help", "Help"),
	]

	def compose(self) -> ComposeResult:
		yield Header()
		yield NotificationBar(id="dashboard-notifications")
		with Vertical(id="dashboard-content"):
			# Financial Health summary
			with Container(classes="dashboard-panel", id="financial-health"):
				yield Static("Financial Health", classes="dashboard-panel-title")
				with Horizontal(id="health-metrics"):
					with Vertical(id="metric-revenue", classes="metric-column"):
						yield Static("Revenue", classes="metric-label")
						yield CurrencyDisplay(id="revenue-amount")
					with Vertical(id="metric-expenses", classes="metric-column"):
						yield Static("Expenses", classes="metric-label")
						yield CurrencyDisplay(id="expenses-amount")
					with Vertical(id="metric-profit", classes="metric-column"):
						yield Static("Net Profit", classes="metric-label")
						yield CurrencyDisplay(id="profit-amount")
				yield SparklinePanel(title="Monthly Revenue", id="revenue-sparkline")

			with Horizontal(id="dashboard-middle"):
				# Action Items
				with Container(classes="dashboard-panel", id="action-items"):
					yield Static("Action Items", classes="dashboard-panel-title")
					yield Static("", id="action-items-list")

				# Recent Activity
				with Container(classes="dashboard-panel", id="recent-activity"):
					yield Static("Recent Activity", classes="dashboard-panel-title")
					yield DataTable(id="recent-txns-table", show_cursor=False)

			# Pipeline
			with Container(classes="dashboard-panel", id="pipeline"):
				yield Static("Pipeline", classes="dashboard-panel-title")
				yield EntityPipeline(id="pipeline-widget")

		yield Footer()

	def on_mount(self) -> None:
		"""Load data when screen mounts."""
		# Set up recent transactions table
		table = self.query_one("#recent-txns-table", DataTable)
		table.add_columns("Date", "Description", "Amount")
		table.zebra_stripes = True

		self._refresh_data()

	def _refresh_data(self) -> None:
		"""Load all dashboard data from storage."""
		storage = self.app.storage
		if storage is None:
			return

		fy = current_financial_year()

		# ── Financial Health ──
		try:
			transactions = storage.get_all_transactions(financial_year=fy)
		except Exception:
			transactions = []

		total_income = Decimal(0)
		total_expenses = Decimal(0)
		for txn in transactions:
			for entry in txn.entries:
				if entry.account_code.startswith("INC-"):
					total_income += entry.credit - entry.debit
				elif entry.account_code.startswith("EXP-"):
					total_expenses += entry.debit - entry.credit

		self.query_one("#revenue-amount", CurrencyDisplay).amount = total_income
		self.query_one("#expenses-amount", CurrencyDisplay).amount = total_expenses
		self.query_one("#profit-amount", CurrencyDisplay).amount = total_income - total_expenses

		# ── Monthly Sparkline ──
		monthly_income: dict[str, Decimal] = defaultdict(Decimal)
		for txn in transactions:
			month_key = txn.date.strftime("%Y-%m")
			for entry in txn.entries:
				if entry.account_code.startswith("INC-"):
					monthly_income[month_key] += entry.credit - entry.debit

		if monthly_income:
			sorted_months = sorted(monthly_income.keys())[-12:]  # Last 12 months
			sparkline_values = [monthly_income[m] for m in sorted_months]
			self.query_one("#revenue-sparkline", SparklinePanel).values = tuple(sparkline_values)

		# ── Action Items ──
		action_lines: list[str] = []
		notifications: list[tuple[str, str]] = []

		try:
			unclassified = storage.get_unclassified_transactions(financial_year=fy)
			if unclassified:
				msg = f"{len(unclassified)} unclassified transactions"
				action_lines.append(f"  [bold #ffab00]![/] {msg}")
				notifications.append((msg, "warning"))
		except Exception:
			pass

		try:
			invoices = storage.get_all_invoices(financial_year=fy)
			overdue = [inv for inv in invoices if inv.status == InvoiceStatus.OVERDUE]
			if overdue:
				msg = f"{len(overdue)} overdue invoice{'s' if len(overdue) != 1 else ''}"
				action_lines.append(f"  [bold #ff1744]!![/] {msg}")
				notifications.append((msg, "urgent"))
		except Exception:
			invoices = []
			overdue = []

		try:
			quotes = storage.get_all_quotes(financial_year=fy)
			expiring = [
				q
				for q in quotes
				if q.status == QuoteStatus.SENT and 0 <= days_until(q.date_valid_until) <= 7
			]
			if expiring:
				msg = f"{len(expiring)} quote{'s' if len(expiring) != 1 else ''} expiring soon"
				action_lines.append(f"  [#2979ff]i[/] {msg}")
				notifications.append((msg, "warning"))
		except Exception:
			quotes = []

		try:
			jobs = storage.get_all_jobs(financial_year=fy)
			active_jobs = [j for j in jobs if j.status.value in ("SCHEDULED", "IN_PROGRESS")]
			if active_jobs:
				action_lines.append(
					f"  [#2979ff]i[/] {len(active_jobs)} active"
					f" job{'s' if len(active_jobs) != 1 else ''}"
				)
		except Exception:
			jobs = []

		if not action_lines:
			action_lines.append("  [dim]All clear — nothing needs attention.[/]")

		self.query_one("#action-items-list", Static).update("\n".join(action_lines))

		# ── Notification Bar ──
		self.query_one("#dashboard-notifications", NotificationBar).set_notifications(notifications)

		# ── Recent Activity ──
		table = self.query_one("#recent-txns-table", DataTable)
		table.clear()
		recent = sorted(transactions, key=lambda t: t.date, reverse=True)[:8]
		for txn in recent:
			net = Decimal(0)
			for entry in txn.entries:
				if entry.account_code.startswith("INC-"):
					net += entry.credit - entry.debit
				elif entry.account_code.startswith("EXP-"):
					net -= entry.debit - entry.credit
				elif entry.account_code.startswith("BANK"):
					net += entry.debit - entry.credit
			amount_str = format_currency(net, show_sign=True)
			table.add_row(
				format_date_short(txn.date),
				txn.description[:35],
				amount_str,
			)

		# ── Pipeline Widget ──
		pipeline = self.query_one("#pipeline-widget", EntityPipeline)
		try:
			pipeline.draft_quotes = len([q for q in quotes if q.status == QuoteStatus.DRAFT])
			pipeline.sent_quotes = len([q for q in quotes if q.status == QuoteStatus.SENT])
		except Exception:
			pass

		try:
			pipeline.active_jobs = len(
				[j for j in jobs if j.status.value in ("SCHEDULED", "IN_PROGRESS")]
			)
		except Exception:
			pass

		pipeline.overdue_invoices = len(overdue)

	def action_help(self) -> None:
		"""Show help overlay."""
		self.notify(
			"[1]-[9] Screen nav  [i]Import  [c]Classify  [r]Reports  [Ctrl+P]Commands  [?]Help",
			title="Keyboard Shortcuts",
		)
