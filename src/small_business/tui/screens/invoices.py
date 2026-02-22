"""Invoices screen — invoice management and payment tracking."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Select, Static

from small_business.models import Client, Invoice, InvoiceStatus, LineItem
from small_business.tui.modals.confirm import ConfirmModal
from small_business.tui.modals.line_item_editor import LineItemEditorModal
from small_business.tui.utils import format_currency, format_date


class InvoicesScreen(Screen):
	"""Invoice management screen with payment tracking."""

	BINDINGS = [
		Binding("escape", "pop_screen", "Back"),
		Binding("n", "new_invoice", "New Invoice"),
		Binding("i", "issue_invoice", "Issue"),
		Binding("p", "record_payment", "Pay"),
		Binding("x", "cancel_invoice", "Cancel"),
	]

	def __init__(self) -> None:
		super().__init__()
		self._invoices: list[Invoice] = []
		self._selected_invoice: Invoice | None = None

	def compose(self) -> ComposeResult:
		yield Header()
		with Vertical(id="invoices-content"):
			yield Static(" Invoices", classes="dashboard-panel-title")
			yield DataTable(id="invoices-table", cursor_type="row")

			with Vertical(id="invoice-detail-panel", classes="dashboard-panel"):
				yield Static("Select an invoice to view details.", id="invoice-detail")

		yield Footer()

	def on_mount(self) -> None:
		"""Load invoices into table."""
		table = self.query_one("#invoices-table", DataTable)
		table.add_columns("ID", "Client", "Status", "Total", "Due Date", "Days Out")
		table.zebra_stripes = True
		self._refresh_data()

	def _refresh_data(self) -> None:
		"""Reload invoices from storage."""
		storage = self.app.storage
		if storage is None:
			return

		try:
			self._invoices = storage.get_all_invoices(latest_only=True)
			self._invoices.sort(key=lambda inv: inv.date_created, reverse=True)
		except Exception:
			self._invoices = []

		table = self.query_one("#invoices-table", DataTable)
		table.clear()
		for inv in self._invoices:
			days_out = str(inv.days_outstanding) if inv.days_outstanding is not None else ""
			table.add_row(
				inv.invoice_id,
				inv.client_id,
				inv.status.value,
				format_currency(inv.total),
				format_date(inv.date_due),
				days_out,
				key=inv.invoice_id,
			)

	def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
		"""Show invoice details when row is highlighted."""
		if event.cursor_row is None or event.cursor_row >= len(self._invoices):
			return

		inv = self._invoices[event.cursor_row]
		self._selected_invoice = inv
		self._show_detail(inv)

	def _show_detail(self, inv: Invoice) -> None:
		"""Update detail panel with invoice info."""
		lines = [
			f"[bold]{inv.invoice_id}[/]  —  {inv.client_id}",
			f"Status: {inv.status.value}  |  Created: {format_date(inv.date_created)}",
			f"Due: {format_date(inv.date_due)}",
		]
		if inv.job_id:
			lines.append(f"Linked Job: {inv.job_id}")
		if inv.date_issued:
			lines.append(f"Issued: {format_date(inv.date_issued)}")
		if inv.date_paid:
			lines.append(f"Paid: {format_date(inv.date_paid)}")
			if inv.payment_amount:
				lines.append(f"Payment: {format_currency(inv.payment_amount)}")
			if inv.payment_reference:
				lines.append(f"Reference: {inv.payment_reference}")
		if inv.days_outstanding is not None:
			lines.append(f"Days Outstanding: {inv.days_outstanding}")

		lines.append("\nLine Items:")
		for item in inv.line_items:
			lines.append(
				f"  {item.description}  "
				f"({item.quantity} x ${item.unit_price:,.2f} = ${item.total:,.2f})"
			)
		lines.append(f"\nSubtotal: {format_currency(inv.subtotal)}")
		lines.append(f"GST: {format_currency(inv.gst_amount)}")
		lines.append(f"[bold]Total: {format_currency(inv.total)}[/]")

		if inv.notes:
			lines.append(f"\nNotes: {inv.notes}")

		self.query_one("#invoice-detail", Static).update("\n".join(lines))

	def action_new_invoice(self) -> None:
		"""Create a standalone invoice."""
		storage = self.app.storage
		if storage is None:
			return

		try:
			clients = storage.get_all_clients()
		except Exception:
			clients = []

		if not clients:
			self.notify("Create a client first.", severity="warning")
			return

		self.app.push_screen(
			_InvoiceSetupModal(clients),
			callback=self._on_invoice_setup,
		)

	def _on_invoice_setup(self, result: dict | None) -> None:
		"""Handle invoice setup result."""
		if result is None:
			return

		self.app.push_screen(
			LineItemEditorModal(),
			callback=lambda items: self._on_line_items(result, items),
		)

	def _on_line_items(self, setup: dict, items: list[LineItem] | None) -> None:
		"""Handle line items result."""
		if items is None:
			return

		try:
			invoice = Invoice(
				client_id=setup["client_id"],
				date_due=setup["due_date"],
				line_items=items,
				notes=setup.get("notes", ""),
			)

			storage = self.app.storage
			if storage:
				storage.save_invoice(invoice)
				self.notify(f"Invoice {invoice.invoice_id} created.", title="Saved")
				self._refresh_data()
				self.app.action_data_changed()
		except Exception as e:
			self.notify(f"Error: {e}", severity="error")

	def action_issue_invoice(self) -> None:
		"""Mark the selected invoice as issued/sent."""
		if self._selected_invoice is None:
			self.notify("No invoice selected.", severity="warning")
			return

		inv = self._selected_invoice
		if inv.status != InvoiceStatus.DRAFT:
			self.notify(
				f"Can only issue DRAFT invoices (current: {inv.status.value}).", severity="warning"
			)
			return

		try:
			updated = inv.model_copy(update={"date_issued": date.today()})
			storage = self.app.storage
			if storage:
				storage.save_invoice(updated)
				self.notify(f"Invoice {inv.invoice_id} issued.", title="Issued")
				self._refresh_data()
				self.app.action_data_changed()
		except Exception as e:
			self.notify(f"Error: {e}", severity="error")

	def action_record_payment(self) -> None:
		"""Record payment on the selected invoice."""
		if self._selected_invoice is None:
			self.notify("No invoice selected.", severity="warning")
			return

		inv = self._selected_invoice
		if inv.status not in (InvoiceStatus.SENT, InvoiceStatus.OVERDUE):
			self.notify(
				f"Can only pay SENT or OVERDUE invoices (current: {inv.status.value}).",
				severity="warning",
			)
			return

		self.app.push_screen(
			_PaymentModal(inv),
			callback=self._on_payment,
		)

	def _on_payment(self, result: dict | None) -> None:
		"""Handle payment modal result."""
		if result is None or self._selected_invoice is None:
			return

		try:
			updated = self._selected_invoice.model_copy(
				update={
					"date_paid": date.today(),
					"payment_amount": result["amount"],
					"payment_reference": result.get("reference", ""),
				}
			)
			storage = self.app.storage
			if storage:
				storage.save_invoice(updated)
				self.notify(
					f"Payment of {format_currency(result['amount'])} recorded.",
					title="Payment Recorded",
				)
				self._refresh_data()
				self.app.action_data_changed()
		except Exception as e:
			self.notify(f"Error: {e}", severity="error")

	def action_cancel_invoice(self) -> None:
		"""Cancel the selected invoice."""
		if self._selected_invoice is None:
			self.notify("No invoice selected.", severity="warning")
			return

		inv = self._selected_invoice
		if inv.status in (InvoiceStatus.PAID, InvoiceStatus.CANCELLED):
			self.notify(f"Cannot cancel {inv.status.value} invoices.", severity="warning")
			return

		self.app.push_screen(
			ConfirmModal("Cancel Invoice", f"Cancel invoice {inv.invoice_id}?"),
			callback=self._on_cancel_confirmed,
		)

	def _on_cancel_confirmed(self, confirmed: bool) -> None:
		"""Handle cancel confirmation."""
		if not confirmed or self._selected_invoice is None:
			return

		try:
			updated = self._selected_invoice.model_copy(update={"date_cancelled": date.today()})
			storage = self.app.storage
			if storage:
				storage.save_invoice(updated)
				self.notify(
					f"Invoice {self._selected_invoice.invoice_id} cancelled.",
					title="Cancelled",
				)
				self._refresh_data()
				self.app.action_data_changed()
		except Exception as e:
			self.notify(f"Error: {e}", severity="error")


class _InvoiceSetupModal(ModalScreen[dict | None]):
	"""Internal modal for invoice client and due date setup."""

	DEFAULT_CSS = """
	_InvoiceSetupModal {
		align: center middle;
	}

	#invoice-setup-dialog {
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

	#invoice-setup-error {
		color: #ff1744;
		height: auto;
	}

	#invoice-setup-buttons {
		margin-top: 1;
		height: auto;
		align-horizontal: center;
	}

	#invoice-setup-buttons Button {
		margin: 0 1;
	}
	"""

	def __init__(self, clients: list[Client]) -> None:
		super().__init__()
		self._clients = clients

	def compose(self) -> ComposeResult:
		client_options = [(c.client_id, c.client_id) for c in self._clients]
		default_due = (date.today() + timedelta(days=30)).isoformat()

		with Vertical(id="invoice-setup-dialog"):
			yield Static("New Invoice", classes="modal-title")

			with Vertical(classes="setup-field"):
				yield Label("Client")
				yield Select(client_options, id="inv-client-select", prompt="Select client...")

			with Vertical(classes="setup-field"):
				yield Label("Due Date (YYYY-MM-DD)")
				yield Input(value=default_due, id="inv-due-date")

			with Vertical(classes="setup-field"):
				yield Label("Notes (optional)")
				yield Input(placeholder="Optional notes...", id="inv-notes")

			yield Static("", id="invoice-setup-error")

			with Vertical(id="invoice-setup-buttons"):
				yield Button("Next: Add Line Items", variant="primary", id="btn-next")
				yield Button("Cancel", variant="default", id="btn-cancel")

	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == "btn-cancel":
			self.dismiss(None)
		elif event.button.id == "btn-next":
			self._validate()

	def _validate(self) -> None:
		client_val = self.query_one("#inv-client-select", Select).value
		if client_val is Select.BLANK:
			self.query_one("#invoice-setup-error", Static).update("Please select a client.")
			return

		due_str = self.query_one("#inv-due-date", Input).value.strip()
		try:
			due_date = date.fromisoformat(due_str)
		except ValueError:
			self.query_one("#invoice-setup-error", Static).update(
				"Invalid date format. Use YYYY-MM-DD."
			)
			return

		self.dismiss(
			{
				"client_id": client_val,
				"due_date": due_date,
				"notes": self.query_one("#inv-notes", Input).value.strip(),
			}
		)


class _PaymentModal(ModalScreen[dict | None]):
	"""Modal for recording a payment on an invoice."""

	DEFAULT_CSS = """
	_PaymentModal {
		align: center middle;
	}

	#payment-dialog {
		width: 50;
		height: auto;
		border: thick $primary;
		background: $surface;
		padding: 1 2;
	}

	.pay-field {
		height: auto;
		margin-bottom: 1;
	}

	#payment-error {
		color: #ff1744;
		height: auto;
	}

	#payment-buttons {
		margin-top: 1;
		height: auto;
		align-horizontal: center;
	}

	#payment-buttons Button {
		margin: 0 1;
	}
	"""

	def __init__(self, invoice: Invoice) -> None:
		super().__init__()
		self._invoice = invoice

	def compose(self) -> ComposeResult:
		with Vertical(id="payment-dialog"):
			yield Static("Record Payment", classes="modal-title")
			yield Static(
				f"Invoice {self._invoice.invoice_id}  —  "
				f"Total: {format_currency(self._invoice.total)}"
			)

			with Vertical(classes="pay-field"):
				yield Label("Payment Amount ($)")
				yield Input(
					value=str(self._invoice.total),
					id="pay-amount",
				)

			with Vertical(classes="pay-field"):
				yield Label("Reference (optional)")
				yield Input(placeholder="e.g. Bank transfer ref", id="pay-reference")

			yield Static("", id="payment-error")

			with Horizontal(id="payment-buttons"):
				yield Button("Record Payment", variant="primary", id="btn-pay")
				yield Button("Cancel", variant="default", id="btn-cancel")

	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == "btn-cancel":
			self.dismiss(None)
		elif event.button.id == "btn-pay":
			self._validate()

	def _validate(self) -> None:
		try:
			amount = Decimal(self.query_one("#pay-amount", Input).value.strip())
			if amount <= 0:
				raise ValueError("Amount must be positive")
		except (InvalidOperation, ValueError) as e:
			self.query_one("#payment-error", Static).update(f"Invalid amount: {e}")
			return

		self.dismiss(
			{
				"amount": amount,
				"reference": self.query_one("#pay-reference", Input).value.strip(),
			}
		)
