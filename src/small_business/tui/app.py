"""SmallBusinessApp — main Textual application class."""

from __future__ import annotations

from pathlib import Path

from textual.app import App
from textual.binding import Binding
from textual.reactive import reactive

from small_business.models import InvoiceStatus
from small_business.storage.registry import StorageRegistry
from small_business.tui.commands import ActionProvider, EntityProvider, NavigationProvider
from small_business.tui.screens.bank_import import BankImportScreen
from small_business.tui.screens.classification import ClassificationScreen
from small_business.tui.screens.clients import ClientsScreen
from small_business.tui.screens.dashboard import DashboardScreen
from small_business.tui.screens.invoices import InvoicesScreen
from small_business.tui.screens.jobs import JobsScreen
from small_business.tui.screens.quotes import QuotesScreen
from small_business.tui.screens.reports import ReportsScreen
from small_business.tui.screens.settings import SettingsScreen
from small_business.tui.screens.transactions import TransactionsScreen
from small_business.tui.utils import current_financial_year


class SmallBusinessApp(App):
	"""Small Business Manager TUI application."""

	TITLE = "Small Business Manager"
	CSS_PATH = [
		"styles/app.tcss",
		"styles/dashboard.tcss",
		"styles/bank_import.tcss",
		"styles/classification.tcss",
	]

	COMMANDS = App.COMMANDS | {NavigationProvider, ActionProvider, EntityProvider}

	SCREENS = {
		"dashboard": DashboardScreen,
		"clients": ClientsScreen,
		"quotes": QuotesScreen,
		"jobs": JobsScreen,
		"invoices": InvoicesScreen,
		"transactions": TransactionsScreen,
		"bank_import": BankImportScreen,
		"classification": ClassificationScreen,
		"reports": ReportsScreen,
		"settings": SettingsScreen,
	}

	BINDINGS = [
		Binding("ctrl+q", "quit", "Quit", priority=True),
		Binding("1", "switch_screen('dashboard')", "Dashboard", show=False),
		Binding("2", "switch_screen('clients')", "Clients", show=False),
		Binding("3", "switch_screen('quotes')", "Quotes", show=False),
		Binding("4", "switch_screen('jobs')", "Jobs", show=False),
		Binding("5", "switch_screen('invoices')", "Invoices", show=False),
		Binding("6", "switch_screen('transactions')", "Transactions", show=False),
		Binding("7", "switch_screen('bank_import')", "Import", show=False),
		Binding("8", "switch_screen('classification')", "Classify", show=False),
		Binding("9", "switch_screen('reports')", "Reports", show=False),
	]

	# Reactive attributes that drive notification badges
	unclassified_count: reactive[int] = reactive(0)
	overdue_count: reactive[int] = reactive(0)

	def __init__(self, data_dir: Path | None = None) -> None:
		super().__init__()
		self.data_dir = data_dir
		self.storage: StorageRegistry | None = None

	def on_mount(self) -> None:
		"""Initialize storage and show appropriate first screen."""
		if self.data_dir and self.data_dir.exists():
			self._init_storage(self.data_dir)
			self.push_screen("dashboard")
		else:
			# Show setup wizard
			from small_business.tui.modals.setup_wizard import SetupWizardModal

			self.push_screen(SetupWizardModal(), callback=self._on_setup_complete)

	def _on_setup_complete(self, result: Path | None) -> None:
		"""Handle setup wizard completion."""
		if result is None:
			# User cancelled — exit the app
			self.exit()
			return

		self.data_dir = result
		self._init_storage(result)
		self.push_screen("dashboard")
		self.notify(f"Business created at {result}", title="Setup Complete")

	def _init_storage(self, data_dir: Path) -> None:
		"""Initialize the StorageRegistry and update reactive counts."""
		self.storage = StorageRegistry(data_dir)
		self._update_counts()

		# Update the title with business name
		try:
			settings = self.storage.get_settings()
			if settings.business_name:
				self.title = f"Small Business Manager — {settings.business_name}"
		except FileNotFoundError:
			pass

	def _update_counts(self) -> None:
		"""Refresh reactive notification counts from storage."""
		if self.storage is None:
			return

		fy = current_financial_year()

		try:
			self.unclassified_count = len(
				self.storage.get_unclassified_transactions(financial_year=fy)
			)
		except Exception:
			self.unclassified_count = 0

		try:
			invoices = self.storage.get_all_invoices(financial_year=fy)
			self.overdue_count = len(
				[inv for inv in invoices if inv.status == InvoiceStatus.OVERDUE]
			)
		except Exception:
			self.overdue_count = 0

	def action_data_changed(self) -> None:
		"""Called after any data mutation to refresh counts and visible screen."""
		if self.storage:
			self.storage.reload()
		self._update_counts()
