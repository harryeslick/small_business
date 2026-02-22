"""Transactions screen — browse, search, void, and delete transactions."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Static

from small_business.models import Transaction
from small_business.tui.modals.confirm import ConfirmModal
from small_business.tui.utils import format_currency, format_date_short


class TransactionsScreen(Screen):
	"""Transaction browser with search, void, and delete."""

	BINDINGS = [
		Binding("escape", "pop_screen", "Back"),
		Binding("slash", "focus_search", "Search"),
		Binding("v", "void_transaction", "Void"),
		Binding("d", "delete_transaction", "Delete"),
	]

	def __init__(self) -> None:
		super().__init__()
		self._transactions: list[Transaction] = []
		self._filtered: list[Transaction] = []
		self._selected_txn: Transaction | None = None

	def compose(self) -> ComposeResult:
		yield Header()
		with Vertical(id="txn-content"):
			with Horizontal(id="txn-header"):
				yield Static(" Transactions", classes="dashboard-panel-title")
				yield Input(placeholder="Search descriptions...", id="txn-search")

			yield DataTable(id="txn-table", cursor_type="row")

			with Vertical(id="txn-detail-panel", classes="dashboard-panel"):
				yield Static("Select a transaction to view details.", id="txn-detail")

		yield Footer()

	def on_mount(self) -> None:
		"""Load transactions into table."""
		table = self.query_one("#txn-table", DataTable)
		table.add_columns("Date", "Description", "Amount", "Accounts")
		table.zebra_stripes = True
		self._refresh_data()

	def _refresh_data(self, query: str = "") -> None:
		"""Reload transactions from storage, optionally filtering."""
		storage = self.app.storage
		if storage is None:
			return

		try:
			if query:
				self._transactions = storage.search_transactions(query=query)
			else:
				self._transactions = storage.get_all_transactions()
			self._transactions.sort(key=lambda t: t.date, reverse=True)
		except Exception:
			self._transactions = []

		self._filtered = self._transactions
		self._populate_table()

	def _populate_table(self) -> None:
		"""Fill the DataTable with filtered transactions."""
		table = self.query_one("#txn-table", DataTable)
		table.clear()
		for txn in self._filtered:
			# Summarize accounts involved
			accounts = ", ".join(sorted({e.account_code for e in txn.entries}))
			if len(accounts) > 30:
				accounts = accounts[:27] + "..."

			# Display amount
			amount = format_currency(txn.amount)

			table.add_row(
				format_date_short(txn.date),
				txn.description[:40],
				amount,
				accounts,
				key=txn.transaction_id,
			)

	def on_input_changed(self, event: Input.Changed) -> None:
		"""Live filter as user types in search."""
		if event.input.id != "txn-search":
			return
		self._refresh_data(query=event.value.strip())

	def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
		"""Show transaction details when row is highlighted."""
		if event.cursor_row is None or event.cursor_row >= len(self._filtered):
			return

		txn = self._filtered[event.cursor_row]
		self._selected_txn = txn
		self._show_detail(txn)

	def _show_detail(self, txn: Transaction) -> None:
		"""Update detail panel with transaction journal entries."""
		lines = [
			f"[bold]{txn.transaction_id}[/]  —  {txn.date}",
			f"Description: {txn.description}",
			f"Amount: {format_currency(txn.amount)}",
			"",
			"Journal Entries:",
		]
		for entry in txn.entries:
			debit_str = f"${entry.debit:,.2f}" if entry.debit else ""
			credit_str = f"${entry.credit:,.2f}" if entry.credit else ""
			lines.append(f"  {entry.account_code:<25} DR {debit_str:>10}  CR {credit_str:>10}")

		if txn.import_source:
			lines.append(f"\nImport: {txn.import_source} ({txn.import_file or 'unknown'})")
		if txn.notes:
			lines.append(f"Notes: {txn.notes}")

		self.query_one("#txn-detail", Static).update("\n".join(lines))

	def action_focus_search(self) -> None:
		"""Focus the search input."""
		self.query_one("#txn-search", Input).focus()

	def action_void_transaction(self) -> None:
		"""Void the selected transaction (creates reversing entry)."""
		if self._selected_txn is None:
			self.notify("No transaction selected.", severity="warning")
			return

		txn = self._selected_txn
		self.app.push_screen(
			ConfirmModal(
				"Void Transaction",
				f"Void transaction {txn.transaction_id}?\nThis creates a reversing entry.",
			),
			callback=self._on_void_confirmed,
		)

	def _on_void_confirmed(self, confirmed: bool) -> None:
		"""Handle void confirmation."""
		if not confirmed or self._selected_txn is None:
			return

		storage = self.app.storage
		if storage is None:
			return

		try:
			reversing = storage.void_transaction(
				self._selected_txn.transaction_id,
				self._selected_txn.date,
			)
			self.notify(
				f"Voided. Reversing entry: {reversing.transaction_id}",
				title="Transaction Voided",
			)
			self._refresh_data()
			self.app.action_data_changed()
		except Exception as e:
			self.notify(f"Error: {e}", severity="error")

	def action_delete_transaction(self) -> None:
		"""Delete the selected transaction permanently."""
		if self._selected_txn is None:
			self.notify("No transaction selected.", severity="warning")
			return

		txn = self._selected_txn
		self.app.push_screen(
			ConfirmModal(
				"Delete Transaction",
				f"Permanently delete {txn.transaction_id}?\nThis cannot be undone.",
				confirm_label="Delete",
			),
			callback=self._on_delete_confirmed,
		)

	def _on_delete_confirmed(self, confirmed: bool) -> None:
		"""Handle delete confirmation."""
		if not confirmed or self._selected_txn is None:
			return

		storage = self.app.storage
		if storage is None:
			return

		try:
			storage.delete_transaction(
				self._selected_txn.transaction_id,
				self._selected_txn.date,
			)
			self.notify(
				f"Deleted {self._selected_txn.transaction_id}.",
				title="Transaction Deleted",
			)
			self._selected_txn = None
			self._refresh_data()
			self.app.action_data_changed()
		except Exception as e:
			self.notify(f"Error: {e}", severity="error")
