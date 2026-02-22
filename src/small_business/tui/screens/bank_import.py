"""Bank Import screen — import CSV bank statements with preview and progress."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
	Button,
	DataTable,
	Footer,
	Header,
	Input,
	Label,
	ProgressBar,
	Select,
	Static,
)

from small_business.bank import import_bank_statement, parse_csv
from small_business.models import BankFormat
from small_business.tui.utils import format_currency, format_date_short


class BankImportScreen(Screen):
	"""Import bank CSV statements with format selection, preview, and progress."""

	BINDINGS = [
		Binding("escape", "pop_screen", "Back"),
	]

	def __init__(self) -> None:
		super().__init__()
		self._bank_formats: list[BankFormat] = []
		self._selected_format: BankFormat | None = None
		self._csv_path: Path | None = None
		self._account_codes: list[str] = []

	def compose(self) -> ComposeResult:
		yield Header()
		with Vertical(id="import-content"):
			yield Static(" Bank Import", classes="dashboard-panel-title")

			# Format + Account row
			with Horizontal(classes="form-row", id="import-selectors"):
				with Vertical(id="format-selector"):
					yield Label("Bank Format")
					yield Select([], id="bank-format-select", prompt="Select bank format...")
				with Vertical(id="account-selector"):
					yield Label("Bank Account Code")
					yield Input(
						placeholder="e.g. BANK-ANZ-CHEQUE",
						id="bank-account-code",
					)

			# File path + Bank name
			with Horizontal(classes="form-row", id="import-file-row"):
				with Vertical(id="file-input-container"):
					yield Label("CSV File Path")
					yield Input(placeholder="Path to bank CSV file...", id="csv-path-input")
				with Vertical(id="bank-name-container"):
					yield Label("Bank Name")
					yield Input(placeholder="e.g. ANZ", id="bank-name-input")

			# Account name
			with Horizontal(classes="form-row", id="account-name-row"):
				with Vertical(id="account-name-container"):
					yield Label("Account Name")
					yield Input(placeholder="e.g. Business Cheque", id="account-name-input")

			# Buttons
			with Horizontal(id="import-buttons"):
				yield Button("Preview", variant="default", id="btn-preview")
				yield Button("Import", variant="primary", id="btn-import", disabled=True)

			# Preview table
			with Vertical(id="preview-section"):
				yield Static("", id="preview-title")
				yield DataTable(id="preview-table", show_cursor=False)

			# Progress
			with Vertical(id="progress-section"):
				yield ProgressBar(id="import-progress", show_eta=False)
				yield Static("", id="import-status")

		yield Footer()

	def on_mount(self) -> None:
		"""Load bank formats from storage."""
		storage = self.app.storage
		if storage is None:
			return

		# Load bank formats
		try:
			bank_formats = storage.get_bank_formats()
			self._bank_formats = bank_formats.formats
			format_options = [(fmt.name, fmt.name) for fmt in self._bank_formats]
			self.query_one("#bank-format-select", Select).set_options(format_options)
		except FileNotFoundError:
			self.notify("No bank formats configured. Add them in Settings.", severity="warning")

		# Load account codes for reference
		try:
			self._account_codes = storage.get_account_codes()
		except FileNotFoundError:
			pass

		# Set up preview table columns
		table = self.query_one("#preview-table", DataTable)
		table.add_columns("Date", "Description", "Amount", "Balance")
		table.zebra_stripes = True

	def on_select_changed(self, event: Select.Changed) -> None:
		"""Handle bank format selection."""
		if event.select.id != "bank-format-select":
			return
		selected_name = event.value
		if selected_name is Select.BLANK:
			self._selected_format = None
			return
		for fmt in self._bank_formats:
			if fmt.name == selected_name:
				self._selected_format = fmt
				break

	def on_button_pressed(self, event: Button.Pressed) -> None:
		"""Handle button clicks."""
		if event.button.id == "btn-preview":
			self._do_preview()
		elif event.button.id == "btn-import":
			self._do_import()

	def _do_preview(self) -> None:
		"""Parse and preview the CSV file."""
		# Validate inputs
		if self._selected_format is None:
			self.notify("Please select a bank format.", severity="error")
			return

		csv_path_str = self.query_one("#csv-path-input", Input).value.strip()
		if not csv_path_str:
			self.notify("Please enter the CSV file path.", severity="error")
			return

		csv_path = Path(csv_path_str).expanduser().resolve()
		if not csv_path.exists():
			self.notify(f"File not found: {csv_path}", severity="error")
			return

		bank_name = self.query_one("#bank-name-input", Input).value.strip() or "Bank"
		account_name = self.query_one("#account-name-input", Input).value.strip() or "Account"

		try:
			statement = parse_csv(csv_path, self._selected_format, bank_name, account_name)
		except Exception as e:
			self.notify(f"Parse error: {e}", severity="error")
			return

		self._csv_path = csv_path

		# Populate preview table (first 10 rows)
		table = self.query_one("#preview-table", DataTable)
		table.clear()
		preview_txns = statement.transactions[:10]
		for txn in preview_txns:
			amount_str = format_currency(txn.amount, show_sign=True)
			balance_str = format_currency(txn.balance) if txn.balance is not None else ""
			table.add_row(
				format_date_short(txn.date),
				txn.description[:40],
				amount_str,
				balance_str,
			)

		total = len(statement.transactions)
		showing = min(total, 10)
		title = f" Preview: {showing} of {total} transactions"
		if total > 10:
			title += f" ({total - 10} more not shown)"
		self.query_one("#preview-title", Static).update(title)

		# Enable import button
		self.query_one("#btn-import", Button).disabled = False
		self.notify(f"Parsed {total} transactions from CSV.", title="Preview Ready")

	def _do_import(self) -> None:
		"""Import the bank statement."""
		if self._selected_format is None or self._csv_path is None:
			self.notify("Please preview the file first.", severity="error")
			return

		bank_account_code = self.query_one("#bank-account-code", Input).value.strip()
		if not bank_account_code:
			self.notify("Please enter a bank account code.", severity="error")
			return

		bank_name = self.query_one("#bank-name-input", Input).value.strip() or "Bank"
		account_name = self.query_one("#account-name-input", Input).value.strip() or "Account"

		# Show progress
		progress = self.query_one("#import-progress", ProgressBar)
		progress.update(total=100, progress=10)
		self.query_one("#import-status", Static).update(" Importing...")

		try:
			result = import_bank_statement(
				csv_path=self._csv_path,
				bank_format=self._selected_format,
				bank_name=bank_name,
				account_name=account_name,
				bank_account_code=bank_account_code,
				data_dir=self.app.data_dir,
			)

			progress.update(total=100, progress=100)

			imported = result["imported"]
			duplicates = result["duplicates"]
			status_text = f" Imported: {imported}  Duplicates: {duplicates}"
			self.query_one("#import-status", Static).update(status_text)

			self.notify(
				f"Imported {imported} transactions ({duplicates} duplicates skipped).",
				title="Import Complete",
			)

			# Refresh storage and counts
			if self.app.storage:
				self.app.storage.reload()
			self.app.action_data_changed()

			# Disable import button to prevent double-import
			self.query_one("#btn-import", Button).disabled = True

		except Exception as e:
			progress.update(total=100, progress=0)
			self.query_one("#import-status", Static).update(f" Error: {e}")
			self.notify(f"Import failed: {e}", severity="error")
