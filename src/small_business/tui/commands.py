"""Command palette providers for the TUI."""

from __future__ import annotations

from functools import partial

from textual.command import Hit, Hits, Provider


class NavigationProvider(Provider):
	"""Provides navigation commands for the command palette."""

	SCREENS = {
		"Dashboard": ("dashboard", "Home screen with financial overview"),
		"Clients": ("clients", "Manage clients"),
		"Quotes": ("quotes", "Manage quotes and proposals"),
		"Jobs": ("jobs", "Track active jobs"),
		"Invoices": ("invoices", "Manage invoices and payments"),
		"Transactions": ("transactions", "Browse all transactions"),
		"Bank Import": ("bank_import", "Import bank CSV statements"),
		"Classify Transactions": ("classification", "Classify unclassified transactions"),
		"Reports": ("reports", "Generate financial reports"),
		"Settings": ("settings", "Business settings and configuration"),
	}

	async def search(self, query: str) -> Hits:
		"""Search for screen navigation commands."""
		matcher = self.matcher(query)
		for name, (screen_name, help_text) in self.SCREENS.items():
			command = f"Go to {name}"
			score = matcher.match(command)
			if score > 0:
				yield Hit(
					score,
					matcher.highlight(command),
					partial(self.app.switch_screen, screen_name),
					help=help_text,
				)


class ActionProvider(Provider):
	"""Provides action commands for the command palette."""

	ACTIONS = {
		"New Client": ("clients", "action_new_client", "Create a new client"),
		"New Quote": ("quotes", "action_new_quote", "Create a new quote"),
		"New Invoice": ("invoices", "action_new_invoice", "Create a standalone invoice"),
		"Import Bank Statement": ("bank_import", None, "Import a bank CSV file"),
		"Classify Transactions": ("classification", None, "Classify unclassified transactions"),
		"Generate Reports": ("reports", "action_generate", "Generate financial reports"),
	}

	async def search(self, query: str) -> Hits:
		"""Search for action commands."""
		matcher = self.matcher(query)
		for name, (screen_name, action_name, help_text) in self.ACTIONS.items():
			score = matcher.match(name)
			if score > 0:
				yield Hit(
					score,
					matcher.highlight(name),
					partial(self._run_action, screen_name, action_name),
					help=help_text,
				)

	def _run_action(self, screen_name: str, action_name: str | None) -> None:
		"""Switch to screen and optionally trigger an action."""
		self.app.switch_screen(screen_name)
		if action_name:
			# Schedule the action to run after the screen switch
			self.app.call_later(lambda: self.app.screen.run_action(action_name))


class EntityProvider(Provider):
	"""Searches across clients, quotes, jobs, and invoices by ID/name."""

	async def search(self, query: str) -> Hits:
		"""Search for entities across all types."""
		storage = getattr(self.app, "storage", None)
		if storage is None:
			return

		matcher = self.matcher(query)

		# Search clients
		try:
			for client in storage.get_all_clients():
				search_text = f"Client: {client.client_id} ({client.name})"
				score = matcher.match(search_text)
				if score > 0:
					yield Hit(
						score,
						matcher.highlight(search_text),
						partial(self.app.switch_screen, "clients"),
						help=f"View client {client.client_id}",
					)
		except Exception:
			pass

		# Search quotes
		try:
			for quote in storage.get_all_quotes(latest_only=True):
				search_text = f"Quote: {quote.quote_id} ({quote.client_id})"
				score = matcher.match(search_text)
				if score > 0:
					yield Hit(
						score,
						matcher.highlight(search_text),
						partial(self.app.switch_screen, "quotes"),
						help=f"{quote.status.value} — ${quote.total:,.2f}",
					)
		except Exception:
			pass

		# Search jobs
		try:
			for job in storage.get_all_jobs(latest_only=True):
				search_text = f"Job: {job.job_id} ({job.client_id})"
				score = matcher.match(search_text)
				if score > 0:
					yield Hit(
						score,
						matcher.highlight(search_text),
						partial(self.app.switch_screen, "jobs"),
						help=f"{job.status.value}",
					)
		except Exception:
			pass

		# Search invoices
		try:
			for inv in storage.get_all_invoices(latest_only=True):
				search_text = f"Invoice: {inv.invoice_id} ({inv.client_id})"
				score = matcher.match(search_text)
				if score > 0:
					yield Hit(
						score,
						matcher.highlight(search_text),
						partial(self.app.switch_screen, "invoices"),
						help=f"{inv.status.value} — ${inv.total:,.2f}",
					)
		except Exception:
			pass
