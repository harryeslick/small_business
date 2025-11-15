"""Job model."""

from datetime import date

from pydantic import BaseModel, Field, computed_field

from .enums import JobStatus
from .utils import generate_job_id, get_financial_year


class Job(BaseModel):
	"""Job/work tracking from accepted quote."""

	job_id: str = Field(default_factory=generate_job_id)
	quote_id: str | None = None
	client_id: str
	date_accepted: date
	scheduled_date: date | None = None
	status: JobStatus = JobStatus.SCHEDULED
	actual_costs: list[str] = Field(default_factory=list)
	notes: str = ""
	calendar_event_id: str | None = None

	@computed_field
	@property
	def financial_year(self) -> str:
		"""Financial year based on date_accepted."""
		return get_financial_year(self.date_accepted)
