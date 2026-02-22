"""Client form modal for creating and editing clients."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from small_business.models import Client


class ClientFormModal(ModalScreen[Client | None]):
	"""Modal form for creating or editing a client.

	Returns the Client on save, or None if cancelled.
	"""

	DEFAULT_CSS = """
	ClientFormModal {
		align: center middle;
	}

	#client-dialog {
		width: 65;
		height: auto;
		max-height: 85%;
		border: thick $primary;
		background: $surface;
		padding: 1 2;
		overflow-y: auto;
	}

	.form-field {
		height: auto;
		margin-bottom: 1;
	}

	.field-label {
		margin-bottom: 0;
	}

	#client-error {
		color: #ff1744;
		text-align: center;
		height: auto;
	}

	#client-buttons {
		margin-top: 1;
		height: auto;
		align-horizontal: center;
	}

	#client-buttons Button {
		margin: 0 1;
	}
	"""

	def __init__(self, client: Client | None = None) -> None:
		super().__init__()
		self._editing = client

	def compose(self) -> ComposeResult:
		title = "Edit Client" if self._editing else "New Client"
		c = self._editing

		with Vertical(id="client-dialog"):
			yield Static(title, classes="modal-title")

			with Vertical(classes="form-field"):
				yield Label("Business Name (ID)", classes="field-label")
				yield Input(
					value=c.client_id if c else "",
					placeholder="e.g. Woolworths",
					id="client-id",
					disabled=bool(c),
				)

			with Vertical(classes="form-field"):
				yield Label("Display Name", classes="field-label")
				yield Input(
					value=c.name if c else "",
					placeholder="e.g. Woolworths Group Ltd",
					id="client-name",
				)

			with Vertical(classes="form-field"):
				yield Label("Contact Person", classes="field-label")
				yield Input(
					value=c.contact_person or "" if c else "",
					placeholder="e.g. John Smith",
					id="client-contact",
				)

			with Vertical(classes="form-field"):
				yield Label("Email", classes="field-label")
				yield Input(
					value=c.email or "" if c else "",
					placeholder="e.g. john@example.com",
					id="client-email",
				)

			with Vertical(classes="form-field"):
				yield Label("Phone", classes="field-label")
				yield Input(
					value=c.phone or "" if c else "",
					placeholder="e.g. 0412 345 678",
					id="client-phone",
				)

			with Vertical(classes="form-field"):
				yield Label("ABN", classes="field-label")
				yield Input(
					value=c.abn or "" if c else "",
					placeholder="e.g. 12 345 678 901",
					id="client-abn",
				)

			with Vertical(classes="form-field"):
				yield Label("Street Address", classes="field-label")
				yield Input(
					value=c.street_address or "" if c else "",
					placeholder="e.g. 123 Main St",
					id="client-street",
				)

			with Vertical(classes="form-field"):
				yield Label("Suburb / State / Postcode", classes="field-label")
				yield Input(
					value=_format_suburb_line(c) if c else "",
					placeholder="e.g. Sydney NSW 2000",
					id="client-suburb-line",
				)

			with Vertical(classes="form-field"):
				yield Label("Notes", classes="field-label")
				yield Input(
					value=c.notes if c else "",
					placeholder="Optional notes...",
					id="client-notes",
				)

			yield Static("", id="client-error")

			with Vertical(id="client-buttons"):
				yield Button("Save", variant="primary", id="btn-save")
				yield Button("Cancel", variant="default", id="btn-cancel")

	def on_button_pressed(self, event: Button.Pressed) -> None:
		"""Handle button clicks."""
		if event.button.id == "btn-cancel":
			self.dismiss(None)
		elif event.button.id == "btn-save":
			self._save()

	def _save(self) -> None:
		"""Validate and create/update the client."""
		client_id = self.query_one("#client-id", Input).value.strip()
		name = self.query_one("#client-name", Input).value.strip()

		if not client_id:
			self.query_one("#client-error", Static).update("Business name is required.")
			return
		if not name:
			name = client_id  # Default display name to business name

		# Parse suburb line
		suburb, state, postcode = _parse_suburb_line(
			self.query_one("#client-suburb-line", Input).value.strip()
		)

		street = self.query_one("#client-street", Input).value.strip() or None
		formatted_address = None
		if street:
			parts = [street]
			suburb_parts = [p for p in [suburb, state, postcode] if p]
			if suburb_parts:
				parts.append(" ".join(suburb_parts))
			formatted_address = ", ".join(parts)

		try:
			client = Client(
				client_id=client_id,
				name=name,
				contact_person=self.query_one("#client-contact", Input).value.strip() or None,
				email=self.query_one("#client-email", Input).value.strip() or None,
				phone=self.query_one("#client-phone", Input).value.strip() or None,
				abn=self.query_one("#client-abn", Input).value.strip() or None,
				street_address=street,
				suburb=suburb,
				state=state,
				postcode=postcode,
				formatted_address=formatted_address,
				notes=self.query_one("#client-notes", Input).value.strip(),
			)
			self.dismiss(client)
		except Exception as e:
			self.query_one("#client-error", Static).update(f"Validation error: {e}")


def _format_suburb_line(c: Client) -> str:
	"""Format suburb/state/postcode into a single line."""
	parts = [p for p in [c.suburb, c.state, c.postcode] if p]
	return " ".join(parts)


def _parse_suburb_line(line: str) -> tuple[str | None, str | None, str | None]:
	"""Parse 'Suburb STATE Postcode' into components."""
	if not line:
		return None, None, None
	parts = line.split()
	postcode = None
	state = None
	suburb = None

	# Postcode is typically the last numeric part
	if parts and parts[-1].isdigit():
		postcode = parts.pop()

	# State is typically a 2-3 letter abbreviation
	aus_states = {"NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"}
	if parts and parts[-1].upper() in aus_states:
		state = parts.pop().upper()

	# Everything else is suburb
	if parts:
		suburb = " ".join(parts)

	return suburb, state, postcode
