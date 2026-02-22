"""EntityPipeline widget — horizontal pipeline view of entity counts at each stage."""

from __future__ import annotations

from textual.reactive import reactive
from textual.widgets import Static


class EntityPipeline(Static):
	"""Display entity pipeline: Quotes (draft/sent) | Jobs (active) | Invoices (overdue)."""

	draft_quotes: reactive[int] = reactive(0)
	sent_quotes: reactive[int] = reactive(0)
	active_jobs: reactive[int] = reactive(0)
	overdue_invoices: reactive[int] = reactive(0)

	def __init__(
		self,
		*,
		id: str | None = None,
		classes: str | None = None,
	) -> None:
		super().__init__("", id=id, classes=classes)

	def _watch_draft_quotes(self) -> None:
		self._render()

	def _watch_sent_quotes(self) -> None:
		self._render()

	def _watch_active_jobs(self) -> None:
		self._render()

	def _watch_overdue_invoices(self) -> None:
		self._render()

	def _render(self) -> None:
		"""Render the pipeline text."""
		parts = [
			f"Quotes: {self.draft_quotes} draft, {self.sent_quotes} sent",
			f"Jobs: {self.active_jobs} active",
		]
		if self.overdue_invoices > 0:
			parts.append(f"[bold #ff1744]Invoices: {self.overdue_invoices} overdue[/]")
		else:
			parts.append("Invoices: 0 overdue")

		self.update("  " + "  |  ".join(parts))

	def on_mount(self) -> None:
		"""Initial render."""
		self._render()
