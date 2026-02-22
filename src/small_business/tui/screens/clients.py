"""Clients screen — client management with list and detail view."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from small_business.models import Client
from small_business.tui.modals.client_form import ClientFormModal


class ClientsScreen(Screen):
	"""Client management screen with DataTable and detail panel."""

	BINDINGS = [
		Binding("escape", "pop_screen", "Back"),
		Binding("n", "new_client", "New Client"),
		Binding("e", "edit_client", "Edit"),
		Binding("slash", "focus_search", "Search", show=False),
	]

	def __init__(self) -> None:
		super().__init__()
		self._clients: list[Client] = []
		self._selected_client: Client | None = None

	def compose(self) -> ComposeResult:
		yield Header()
		with Horizontal(id="clients-layout"):
			# Left: client list
			with Vertical(id="client-list-panel"):
				yield Static(" Clients", classes="dashboard-panel-title")
				yield DataTable(id="client-table", cursor_type="row")

			# Right: detail panel
			with Vertical(id="client-detail-panel", classes="dashboard-panel"):
				yield Static("Select a client to view details.", id="client-detail")

		yield Footer()

	def on_mount(self) -> None:
		"""Load clients into table."""
		table = self.query_one("#client-table", DataTable)
		table.add_columns("Business Name", "Contact", "Phone", "Email")
		table.zebra_stripes = True
		self._refresh_data()

	def _refresh_data(self) -> None:
		"""Reload clients from storage."""
		storage = self.app.storage
		if storage is None:
			return

		try:
			self._clients = storage.get_all_clients()
		except Exception:
			self._clients = []

		table = self.query_one("#client-table", DataTable)
		table.clear()
		for client in self._clients:
			table.add_row(
				client.client_id,
				client.contact_person or "",
				client.phone or "",
				client.email or "",
				key=client.client_id,
			)

	def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
		"""Show client details when row is highlighted."""
		if event.cursor_row is None or event.cursor_row >= len(self._clients):
			return

		client = self._clients[event.cursor_row]
		self._selected_client = client
		self._show_detail(client)

	def _show_detail(self, client: Client) -> None:
		"""Update detail panel with client info."""
		lines = [
			f"[bold]{client.name}[/]",
			f"ID: {client.client_id}",
			"",
		]
		if client.contact_person:
			lines.append(f"Contact: {client.contact_person}")
		if client.email:
			lines.append(f"Email: {client.email}")
		if client.phone:
			lines.append(f"Phone: {client.phone}")
		if client.abn:
			lines.append(f"ABN: {client.abn}")
		if client.formatted_address:
			lines.append(f"Address: {client.formatted_address}")
		if client.notes:
			lines.append(f"\nNotes: {client.notes}")

		self.query_one("#client-detail", Static).update("\n".join(lines))

	def action_new_client(self) -> None:
		"""Open the new client form."""
		self.app.push_screen(ClientFormModal(), callback=self._on_client_saved)

	def action_edit_client(self) -> None:
		"""Edit the selected client."""
		if self._selected_client is None:
			self.notify("No client selected.", severity="warning")
			return
		self.app.push_screen(
			ClientFormModal(self._selected_client),
			callback=self._on_client_saved,
		)

	def _on_client_saved(self, result: Client | None) -> None:
		"""Handle client form result."""
		if result is None:
			return

		storage = self.app.storage
		if storage is None:
			return

		try:
			storage.save_client(result)
			self.notify(f"Client '{result.client_id}' saved.", title="Saved")
			self._refresh_data()
		except Exception as e:
			self.notify(f"Error saving client: {e}", severity="error")

	def action_focus_search(self) -> None:
		"""Focus search — placeholder for future filter input."""
		self.notify("Search coming in Phase 5.", severity="information")
