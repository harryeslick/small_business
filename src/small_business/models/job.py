"""Job model."""

from datetime import date

from pydantic import BaseModel, Field, computed_field

from .enums import JobStatus
from .utils import generate_job_id, get_financial_year


class Job(BaseModel):
	"""Job/work tracking from accepted quote.

	Status is derived from date fields:
	- SCHEDULED: No date_started (default state)
	- IN_PROGRESS: date_started set, not completed
	- COMPLETED: date_completed set, not invoiced
	- INVOICED: date_invoiced set
	"""

	job_id: str = Field(default_factory=generate_job_id)
	quote_id: str | None = None
	client_id: str
	date_accepted: date
	scheduled_date: date | None = None
	date_started: date | None = None
	date_completed: date | None = None
	date_invoiced: date | None = None
	actual_costs: list[str] = Field(default_factory=list)
	notes: str = ""
	calendar_event_id: str | None = None

	@computed_field
	@property
	def status(self) -> JobStatus:
		"""Derive status from date fields."""
		if self.date_invoiced:
			return JobStatus.INVOICED
		if self.date_completed:
			return JobStatus.COMPLETED
		if self.date_started:
			return JobStatus.IN_PROGRESS
		return JobStatus.SCHEDULED

	@computed_field
	@property
	def duration_days(self) -> int | None:
		"""Days between start and completion (if both set)."""
		if self.date_started and self.date_completed:
			return (self.date_completed - self.date_started).days
		return None

	@computed_field
	@property
	def financial_year(self) -> str:
		"""Financial year based on date_accepted."""
		return get_financial_year(self.date_accepted)
