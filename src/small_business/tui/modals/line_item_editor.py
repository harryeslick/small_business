"""Line item editor modal for quotes and invoices."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, Static

from small_business.models import LineItem


class LineItemEditorModal(ModalScreen[list[LineItem] | None]):
	"""Modal for editing a list of line items.

	Shows existing items in a simple text display and allows adding new ones.
	Returns the updated list of LineItems, or None if cancelled.
	"""

	DEFAULT_CSS = """
	LineItemEditorModal {
		align: center middle;
	}

	#line-item-dialog {
		width: 75;
		height: auto;
		max-height: 85%;
		border: thick $primary;
		background: $surface;
		padding: 1 2;
		overflow-y: auto;
	}

	#existing-items {
		height: auto;
		max-height: 12;
		margin-bottom: 1;
		border: solid $primary-muted;
		padding: 1;
	}

	.item-row {
		height: auto;
		margin-bottom: 1;
	}

	#line-item-error {
		color: #ff1744;
		height: auto;
	}

	#line-item-buttons {
		margin-top: 1;
		height: auto;
		align-horizontal: center;
	}

	#line-item-buttons Button {
		margin: 0 1;
	}
	"""

	def __init__(self, line_items: list[LineItem] | None = None) -> None:
		super().__init__()
		self._items: list[LineItem] = list(line_items) if line_items else []

	def compose(self) -> ComposeResult:
		with Vertical(id="line-item-dialog"):
			yield Static("Line Items", classes="modal-title")

			# Existing items display
			yield Static(self._format_items(), id="existing-items")

			# New item form
			yield Static("Add New Item", classes="dashboard-panel-title")

			with Vertical(classes="item-row"):
				yield Label("Description")
				yield Input(placeholder="e.g. Labour - Site preparation", id="item-description")

			with Horizontal(classes="item-row"):
				with Vertical():
					yield Label("Quantity")
					yield Input(placeholder="1", id="item-quantity", value="1")
				with Vertical():
					yield Label("Unit Price ($)")
					yield Input(placeholder="0.00", id="item-unit-price")

			yield Checkbox("GST Inclusive", id="item-gst-inclusive", value=True)

			yield Static("", id="line-item-error")

			with Horizontal(id="line-item-buttons"):
				yield Button("Add Item", variant="primary", id="btn-add-item")
				yield Button("Done", variant="success", id="btn-done")
				yield Button("Cancel", variant="default", id="btn-cancel")

	def _format_items(self) -> str:
		"""Format existing items for display."""
		if not self._items:
			return " No line items yet."

		lines = []
		for i, item in enumerate(self._items, 1):
			total = f"${item.total:,.2f}"
			gst_label = "inc GST" if item.gst_inclusive else "ex GST"
			lines.append(
				f" {i}. {item.description}  "
				f"({item.quantity} x ${item.unit_price:,.2f} = {total} {gst_label})"
			)

		total_amount = sum(item.total for item in self._items)
		lines.append(f"\n Total: ${total_amount:,.2f}")
		return "\n".join(lines)

	def on_button_pressed(self, event: Button.Pressed) -> None:
		"""Handle button clicks."""
		if event.button.id == "btn-cancel":
			self.dismiss(None)
		elif event.button.id == "btn-done":
			if not self._items:
				self.query_one("#line-item-error", Static).update(
					"At least one line item is required."
				)
				return
			self.dismiss(self._items)
		elif event.button.id == "btn-add-item":
			self._add_item()

	def _add_item(self) -> None:
		"""Validate and add a new line item."""
		description = self.query_one("#item-description", Input).value.strip()
		if not description:
			self.query_one("#line-item-error", Static).update("Description is required.")
			return

		try:
			quantity = Decimal(self.query_one("#item-quantity", Input).value.strip() or "1")
			if quantity <= 0:
				raise ValueError("Quantity must be positive")
		except (InvalidOperation, ValueError) as e:
			self.query_one("#line-item-error", Static).update(f"Invalid quantity: {e}")
			return

		try:
			unit_price = Decimal(self.query_one("#item-unit-price", Input).value.strip() or "0")
			if unit_price < 0:
				raise ValueError("Unit price cannot be negative")
		except (InvalidOperation, ValueError) as e:
			self.query_one("#line-item-error", Static).update(f"Invalid unit price: {e}")
			return

		gst_inclusive = self.query_one("#item-gst-inclusive", Checkbox).value

		try:
			item = LineItem(
				description=description,
				quantity=quantity,
				unit_price=unit_price,
				gst_inclusive=gst_inclusive,
			)
			self._items.append(item)

			# Update display
			self.query_one("#existing-items", Static).update(self._format_items())

			# Clear form
			self.query_one("#item-description", Input).value = ""
			self.query_one("#item-quantity", Input).value = "1"
			self.query_one("#item-unit-price", Input).value = ""
			self.query_one("#line-item-error", Static).update("")

			self.notify(f"Added: {description}", title="Item Added")
		except Exception as e:
			self.query_one("#line-item-error", Static).update(f"Error: {e}")
