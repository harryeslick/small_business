"""Quotes screen — quote lifecycle management."""

from __future__ import annotations

from datetime import date, timedelta

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Select, Static

from small_business.models import LineItem, Quote, QuoteStatus
from small_business.tui.modals.confirm import ConfirmModal
from small_business.tui.modals.line_item_editor import LineItemEditorModal
from small_business.tui.utils import format_currency, format_date
from small_business.workflows import accept_quote_to_job


class QuotesScreen(Screen):
	"""Quote lifecycle management with DataTable and actions."""

	BINDINGS = [
		Binding("escape", "pop_screen", "Back"),
		Binding("n", "new_quote", "New Quote"),
		Binding("s", "send_quote", "Send"),
		Binding("a", "accept_quote", "Accept"),
	]

	def __init__(self) -> None:
		super().__init__()
		self._quotes: list[Quote] = []
		self._selected_quote: Quote | None = None

	def compose(self) -> ComposeResult:
		yield Header()
		with Vertical(id="quotes-content"):
			yield Static(" Quotes", classes="dashboard-panel-title")
			yield DataTable(id="quotes-table", cursor_type="row")

			# Detail panel
			with Vertical(id="quote-detail-panel", classes="dashboard-panel"):
				yield Static("Select a quote to view details.", id="quote-detail")

		yield Footer()

	def on_mount(self) -> None:
		"""Load quotes into table."""
		table = self.query_one("#quotes-table", DataTable)
		table.add_columns("ID", "Client", "Status", "Total", "Valid Until", "Created")
		table.zebra_stripes = True
		self._refresh_data()

	def _refresh_data(self) -> None:
		"""Reload quotes from storage."""
		storage = self.app.storage
		if storage is None:
			return

		try:
			self._quotes = storage.get_all_quotes(latest_only=True)
			self._quotes.sort(key=lambda q: q.date_created, reverse=True)
		except Exception:
			self._quotes = []

		table = self.query_one("#quotes-table", DataTable)
		table.clear()
		for quote in self._quotes:
			status = quote.status.value
			table.add_row(
				quote.quote_id,
				quote.client_id,
				status,
				format_currency(quote.total),
				format_date(quote.date_valid_until),
				format_date(quote.date_created),
				key=quote.quote_id,
			)

	def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
		"""Show quote details when row is highlighted."""
		if event.cursor_row is None or event.cursor_row >= len(self._quotes):
			return

		quote = self._quotes[event.cursor_row]
		self._selected_quote = quote
		self._show_detail(quote)

	def _show_detail(self, quote: Quote) -> None:
		"""Update detail panel with quote info."""
		lines = [
			f"[bold]{quote.quote_id}[/]  —  {quote.client_id}",
			f"Status: {quote.status.value}  |  Created: {format_date(quote.date_created)}",
			f"Valid Until: {format_date(quote.date_valid_until)}  |  Version: {quote.version}",
			"",
			"Line Items:",
		]
		for item in quote.line_items:
			lines.append(
				f"  {item.description}  "
				f"({item.quantity} x ${item.unit_price:,.2f} = ${item.total:,.2f})"
			)
		lines.append(f"\nSubtotal: {format_currency(quote.subtotal)}")
		lines.append(f"GST: {format_currency(quote.gst_amount)}")
		lines.append(f"[bold]Total: {format_currency(quote.total)}[/]")

		if quote.notes:
			lines.append(f"\nNotes: {quote.notes}")

		self.query_one("#quote-detail", Static).update("\n".join(lines))

	def action_new_quote(self) -> None:
		"""Create a new quote via modal workflow."""
		# First, need to select a client
		storage = self.app.storage
		if storage is None:
			return

		try:
			clients = storage.get_all_clients()
		except Exception:
			clients = []

		if not clients:
			self.notify("Create a client first before creating a quote.", severity="warning")
			return

		# Push client selector then line items editor
		self.app.push_screen(
			_QuoteSetupModal(clients),
			callback=self._on_quote_setup,
		)

	def _on_quote_setup(self, result: dict | None) -> None:
		"""Handle quote setup modal result."""
		if result is None:
			return

		# Now open line item editor
		self.app.push_screen(
			LineItemEditorModal(),
			callback=lambda items: self._on_line_items(result, items),
		)

	def _on_line_items(self, setup: dict, items: list[LineItem] | None) -> None:
		"""Handle line items editor result."""
		if items is None:
			return

		try:
			quote = Quote(
				client_id=setup["client_id"],
				date_valid_until=setup["valid_until"],
				line_items=items,
				notes=setup.get("notes", ""),
			)

			storage = self.app.storage
			if storage:
				storage.save_quote(quote)
				self.notify(f"Quote {quote.quote_id} created.", title="Saved")
				self._refresh_data()
				self.app.action_data_changed()
		except Exception as e:
			self.notify(f"Error creating quote: {e}", severity="error")

	def action_send_quote(self) -> None:
		"""Mark the selected quote as sent."""
		if self._selected_quote is None:
			self.notify("No quote selected.", severity="warning")
			return

		quote = self._selected_quote
		if quote.status != QuoteStatus.DRAFT:
			self.notify(
				f"Can only send DRAFT quotes (current: {quote.status.value}).", severity="warning"
			)
			return

		try:
			updated = quote.model_copy(update={"date_sent": date.today()})
			storage = self.app.storage
			if storage:
				storage.save_quote(updated)
				self.notify(f"Quote {quote.quote_id} marked as sent.", title="Sent")
				self._refresh_data()
				self.app.action_data_changed()
		except Exception as e:
			self.notify(f"Error: {e}", severity="error")

	def action_accept_quote(self) -> None:
		"""Accept the selected quote and create a job."""
		if self._selected_quote is None:
			self.notify("No quote selected.", severity="warning")
			return

		quote = self._selected_quote
		if quote.status != QuoteStatus.SENT:
			self.notify(
				f"Can only accept SENT quotes (current: {quote.status.value}).",
				severity="warning",
			)
			return

		self.app.push_screen(
			ConfirmModal(
				"Accept Quote",
				f"Accept quote {quote.quote_id} and create a job?",
			),
			callback=self._on_accept_confirmed,
		)

	def _on_accept_confirmed(self, confirmed: bool) -> None:
		"""Handle accept confirmation."""
		if not confirmed or self._selected_quote is None:
			return

		try:
			job = accept_quote_to_job(
				quote_id=self._selected_quote.quote_id,
				data_dir=self.app.data_dir,
			)
			self.notify(
				f"Job {job.job_id} created from quote {self._selected_quote.quote_id}.",
				title="Job Created",
			)

			# Reload storage since workflow created its own StorageRegistry
			if self.app.storage:
				self.app.storage.reload()
			self._refresh_data()
			self.app.action_data_changed()
		except Exception as e:
			self.notify(f"Error: {e}", severity="error")


class _QuoteSetupModal(Screen[dict | None]):
	"""Internal modal for quote client selection and validity date."""

	DEFAULT_CSS = """
	_QuoteSetupModal {
		align: center middle;
	}

	#quote-setup-dialog {
		width: 60;
		height: auto;
		border: thick $primary;
		background: $surface;
		padding: 1 2;
	}

	.setup-field {
		height: auto;
		margin-bottom: 1;
	}

	#quote-setup-error {
		color: #ff1744;
		height: auto;
	}

	#quote-setup-buttons {
		margin-top: 1;
		height: auto;
		align-horizontal: center;
	}

	#quote-setup-buttons Button {
		margin: 0 1;
	}
	"""

	def __init__(self, clients: list) -> None:
		super().__init__()
		self._clients = clients

	def compose(self) -> ComposeResult:
		from textual.widgets import Button, Label

		client_options = [(c.client_id, c.client_id) for c in self._clients]
		default_valid = (date.today() + timedelta(days=30)).isoformat()

		with Vertical(id="quote-setup-dialog"):
			yield Static("New Quote", classes="modal-title")

			with Vertical(classes="setup-field"):
				yield Label("Client")
				yield Select(client_options, id="quote-client-select", prompt="Select client...")

			with Vertical(classes="setup-field"):
				yield Label("Valid Until (YYYY-MM-DD)")
				yield Input(value=default_valid, id="quote-valid-until")

			with Vertical(classes="setup-field"):
				yield Label("Notes (optional)")
				yield Input(placeholder="Optional notes...", id="quote-notes")

			yield Static("", id="quote-setup-error")

			with Vertical(id="quote-setup-buttons"):
				yield Button("Next: Add Line Items", variant="primary", id="btn-next")
				yield Button("Cancel", variant="default", id="btn-cancel")

	def on_button_pressed(self, event) -> None:
		if event.button.id == "btn-cancel":
			self.dismiss(None)
		elif event.button.id == "btn-next":
			self._validate_and_proceed()

	def _validate_and_proceed(self) -> None:
		client_val = self.query_one("#quote-client-select", Select).value
		if client_val is Select.BLANK:
			self.query_one("#quote-setup-error", Static).update("Please select a client.")
			return

		valid_until_str = self.query_one("#quote-valid-until", Input).value.strip()
		try:
			valid_until = date.fromisoformat(valid_until_str)
		except ValueError:
			self.query_one("#quote-setup-error", Static).update(
				"Invalid date format. Use YYYY-MM-DD."
			)
			return

		notes = self.query_one("#quote-notes", Input).value.strip()

		self.dismiss(
			{
				"client_id": client_val,
				"valid_until": valid_until,
				"notes": notes,
			}
		)
