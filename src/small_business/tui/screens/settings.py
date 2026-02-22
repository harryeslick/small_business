"""Settings screen — business details, bank formats, chart of accounts."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static, TabbedContent, TabPane

from small_business.models import Settings


class SettingsScreen(Screen):
	"""Business settings with tabbed view."""

	BINDINGS = [
		Binding("escape", "pop_screen", "Back"),
	]

	def compose(self) -> ComposeResult:
		yield Header()
		with Vertical(id="settings-content"):
			yield Static(" Settings", classes="dashboard-panel-title")

			with TabbedContent(id="settings-tabs"):
				with TabPane("Business Details", id="tab-business"):
					with Vertical(id="business-form"):
						with Vertical(classes="form-field"):
							yield Label("Business Name")
							yield Input(id="set-business-name")
						with Vertical(classes="form-field"):
							yield Label("ABN")
							yield Input(id="set-business-abn")
						with Vertical(classes="form-field"):
							yield Label("Email")
							yield Input(id="set-business-email")
						with Vertical(classes="form-field"):
							yield Label("Phone")
							yield Input(id="set-business-phone")
						with Vertical(classes="form-field"):
							yield Label("Address")
							yield Input(id="set-business-address")
						with Vertical(classes="form-field"):
							yield Label("Currency")
							yield Input(id="set-currency")
						with Vertical(classes="form-field"):
							yield Label("GST Rate")
							yield Input(id="set-gst-rate")
						yield Button("Save", variant="primary", id="btn-save-settings")

				with TabPane("Bank Formats", id="tab-bank-formats"):
					yield Static("", id="bank-formats-display")

				with TabPane("Chart of Accounts", id="tab-coa"):
					yield Static("", id="coa-display")

		yield Footer()

	def on_mount(self) -> None:
		"""Load settings data."""
		self._load_settings()
		self._load_bank_formats()
		self._load_chart_of_accounts()

	def _load_settings(self) -> None:
		"""Populate settings form from storage."""
		storage = self.app.storage
		if storage is None:
			return

		try:
			settings = storage.get_settings()
		except FileNotFoundError:
			return

		self.query_one("#set-business-name", Input).value = settings.business_name
		self.query_one("#set-business-abn", Input).value = settings.business_abn
		self.query_one("#set-business-email", Input).value = settings.business_email
		self.query_one("#set-business-phone", Input).value = settings.business_phone
		self.query_one("#set-business-address", Input).value = settings.business_address
		self.query_one("#set-currency", Input).value = settings.currency
		self.query_one("#set-gst-rate", Input).value = str(settings.gst_rate)

	def _load_bank_formats(self) -> None:
		"""Display bank formats."""
		storage = self.app.storage
		if storage is None:
			return

		try:
			bank_formats = storage.get_bank_formats()
		except FileNotFoundError:
			self.query_one("#bank-formats-display", Static).update(" No bank formats configured.")
			return

		lines = [" Configured Bank Formats:", ""]
		for fmt in bank_formats.formats:
			lines.append(f"  [bold]{fmt.name}[/]")
			lines.append(f"    Date column: {fmt.date_column}")
			lines.append(f"    Description column: {fmt.description_column}")
			if fmt.amount_column:
				lines.append(f"    Amount column: {fmt.amount_column}")
			else:
				lines.append(f"    Debit/Credit: {fmt.debit_column} / {fmt.credit_column}")
			lines.append(f"    Date format: {fmt.date_format}")
			lines.append("")

		if not bank_formats.formats:
			lines.append("  No formats configured.")

		self.query_one("#bank-formats-display", Static).update("\n".join(lines))

	def _load_chart_of_accounts(self) -> None:
		"""Display chart of accounts."""
		storage = self.app.storage
		if storage is None:
			return

		try:
			chart = storage.get_chart_of_accounts()
		except FileNotFoundError:
			self.query_one("#coa-display", Static).update(" No chart of accounts found.")
			return

		lines = [" Chart of Accounts:", ""]

		# Group by account type
		from small_business.models import AccountType

		for acct_type in AccountType:
			accounts = chart.get_accounts_by_type(acct_type)
			if accounts:
				lines.append(f"  [bold]{acct_type.value}[/]")
				for acc in accounts:
					desc = f"  ({acc.description})" if acc.description else ""
					lines.append(f"    {acc.name}{desc}")
				lines.append("")

		self.query_one("#coa-display", Static).update("\n".join(lines))

	def on_button_pressed(self, event: Button.Pressed) -> None:
		"""Handle save button."""
		if event.button.id == "btn-save-settings":
			self._save_settings()

	def _save_settings(self) -> None:
		"""Save settings from form inputs."""
		storage = self.app.storage
		if storage is None:
			return

		try:
			# Load existing settings as base
			try:
				existing = storage.get_settings()
			except FileNotFoundError:
				existing = Settings()

			from decimal import Decimal, InvalidOperation

			gst_str = self.query_one("#set-gst-rate", Input).value.strip()
			try:
				gst_rate = Decimal(gst_str) if gst_str else existing.gst_rate
			except InvalidOperation:
				self.notify("Invalid GST rate.", severity="error")
				return

			updated = existing.model_copy(
				update={
					"business_name": self.query_one("#set-business-name", Input).value.strip(),
					"business_abn": self.query_one("#set-business-abn", Input).value.strip(),
					"business_email": self.query_one("#set-business-email", Input).value.strip(),
					"business_phone": self.query_one("#set-business-phone", Input).value.strip(),
					"business_address": self.query_one(
						"#set-business-address", Input
					).value.strip(),
					"currency": self.query_one("#set-currency", Input).value.strip() or "AUD",
					"gst_rate": gst_rate,
				}
			)

			storage.save_settings(updated)

			# Update app title
			if updated.business_name:
				self.app.title = f"Small Business Manager — {updated.business_name}"

			self.notify("Settings saved.", title="Saved")
		except Exception as e:
			self.notify(f"Error saving settings: {e}", severity="error")
