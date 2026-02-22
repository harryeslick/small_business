"""Jobs screen — job tracking with workflow transitions."""

from __future__ import annotations

from datetime import date

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from small_business.models import Job, JobStatus
from small_business.tui.modals.confirm import ConfirmModal
from small_business.tui.utils import format_date
from small_business.workflows import complete_job_to_invoice


class JobsScreen(Screen):
	"""Job tracking screen with status transitions."""

	BINDINGS = [
		Binding("escape", "pop_screen", "Back"),
		Binding("s", "start_job", "Start"),
		Binding("c", "complete_job", "Complete"),
		Binding("i", "invoice_job", "Invoice"),
	]

	def __init__(self) -> None:
		super().__init__()
		self._jobs: list[Job] = []
		self._selected_job: Job | None = None

	def compose(self) -> ComposeResult:
		yield Header()
		with Vertical(id="jobs-content"):
			yield Static(" Jobs", classes="dashboard-panel-title")
			yield DataTable(id="jobs-table", cursor_type="row")

			with Vertical(id="job-detail-panel", classes="dashboard-panel"):
				yield Static("Select a job to view details.", id="job-detail")

		yield Footer()

	def on_mount(self) -> None:
		"""Load jobs into table."""
		table = self.query_one("#jobs-table", DataTable)
		table.add_columns("ID", "Client", "Status", "Quote", "Accepted", "Scheduled")
		table.zebra_stripes = True
		self._refresh_data()

	def _refresh_data(self) -> None:
		"""Reload jobs from storage."""
		storage = self.app.storage
		if storage is None:
			return

		try:
			self._jobs = storage.get_all_jobs(latest_only=True)
			self._jobs.sort(key=lambda j: j.date_accepted, reverse=True)
		except Exception:
			self._jobs = []

		table = self.query_one("#jobs-table", DataTable)
		table.clear()
		for job in self._jobs:
			table.add_row(
				job.job_id,
				job.client_id,
				job.status.value,
				job.quote_id or "",
				format_date(job.date_accepted),
				format_date(job.scheduled_date) if job.scheduled_date else "",
				key=job.job_id,
			)

	def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
		"""Show job details when row is highlighted."""
		if event.cursor_row is None or event.cursor_row >= len(self._jobs):
			return

		job = self._jobs[event.cursor_row]
		self._selected_job = job
		self._show_detail(job)

	def _show_detail(self, job: Job) -> None:
		"""Update detail panel with job info."""
		lines = [
			f"[bold]{job.job_id}[/]  —  {job.client_id}",
			f"Status: {job.status.value}",
			f"Accepted: {format_date(job.date_accepted)}",
		]
		if job.quote_id:
			lines.append(f"Linked Quote: {job.quote_id}")
		if job.scheduled_date:
			lines.append(f"Scheduled: {format_date(job.scheduled_date)}")
		if job.date_started:
			lines.append(f"Started: {format_date(job.date_started)}")
		if job.date_completed:
			lines.append(f"Completed: {format_date(job.date_completed)}")
		if job.date_invoiced:
			lines.append(f"Invoiced: {format_date(job.date_invoiced)}")
		if job.duration_days is not None:
			lines.append(f"Duration: {job.duration_days} days")
		if job.notes:
			lines.append(f"\nNotes: {job.notes}")

		self.query_one("#job-detail", Static).update("\n".join(lines))

	def action_start_job(self) -> None:
		"""Mark the selected job as started."""
		if self._selected_job is None:
			self.notify("No job selected.", severity="warning")
			return

		job = self._selected_job
		if job.status != JobStatus.SCHEDULED:
			self.notify(
				f"Can only start SCHEDULED jobs (current: {job.status.value}).",
				severity="warning",
			)
			return

		try:
			updated = job.model_copy(update={"date_started": date.today()})
			storage = self.app.storage
			if storage:
				storage.update_job(updated)
				self.notify(f"Job {job.job_id} started.", title="Started")
				self._refresh_data()
				self.app.action_data_changed()
		except Exception as e:
			self.notify(f"Error: {e}", severity="error")

	def action_complete_job(self) -> None:
		"""Mark the selected job as completed."""
		if self._selected_job is None:
			self.notify("No job selected.", severity="warning")
			return

		job = self._selected_job
		if job.status != JobStatus.IN_PROGRESS:
			self.notify(
				f"Can only complete IN_PROGRESS jobs (current: {job.status.value}).",
				severity="warning",
			)
			return

		try:
			updated = job.model_copy(update={"date_completed": date.today()})
			storage = self.app.storage
			if storage:
				storage.update_job(updated)
				self.notify(f"Job {job.job_id} completed.", title="Completed")
				self._refresh_data()
				self.app.action_data_changed()
		except Exception as e:
			self.notify(f"Error: {e}", severity="error")

	def action_invoice_job(self) -> None:
		"""Create an invoice from the completed job."""
		if self._selected_job is None:
			self.notify("No job selected.", severity="warning")
			return

		job = self._selected_job
		if job.status != JobStatus.COMPLETED:
			self.notify(
				f"Can only invoice COMPLETED jobs (current: {job.status.value}).",
				severity="warning",
			)
			return

		self.app.push_screen(
			ConfirmModal(
				"Create Invoice",
				f"Create an invoice for job {job.job_id}?",
			),
			callback=self._on_invoice_confirmed,
		)

	def _on_invoice_confirmed(self, confirmed: bool) -> None:
		"""Handle invoice confirmation."""
		if not confirmed or self._selected_job is None:
			return

		try:
			invoice = complete_job_to_invoice(
				job_id=self._selected_job.job_id,
				data_dir=self.app.data_dir,
			)
			self.notify(
				f"Invoice {invoice.invoice_id} created for job {self._selected_job.job_id}.",
				title="Invoice Created",
			)

			# Reload storage since workflow created its own registry
			if self.app.storage:
				self.app.storage.reload()
			self._refresh_data()
			self.app.action_data_changed()
		except Exception as e:
			self.notify(f"Error: {e}", severity="error")
